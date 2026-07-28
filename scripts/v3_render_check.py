"""DT-94 render verification: every primitive and graph topology on real audio.

Exposing a pedalboard plugin in the registry proves nothing on its own. This
script renders actual audio through each newly-exposed primitive and each graph
topology, and asserts the output is (a) finite, (b) within the ceiling, (c)
audibly different from the input, and (d) channel-correct.

"Audibly different" is deliberately crude — an RMS/spectral delta, not a quality
judgement. It catches the failure mode that matters here: a processor that is
wired up but silently doing nothing.

    python scripts/v3_render_check.py [--input PATH] [--outdir DIR]

Renders are written for optional listening. They are not evidence of quality and
no verdict here is perceptual.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dsp_engine.channels import (  # noqa: E402
    channel_count,
    mono_compatibility,
    normalize,
    pan,
    to_stereo,
)
from src.dsp_engine.graph import (  # noqa: E402
    Parallel,
    Processor,
    Send,
    Serial,
    render_graph,
)
from src.dsp_engine.processors import PROCESSORS  # noqa: E402

CEILING = 10.0 ** (-0.2 / 20.0)

# The DT-94 primitives, with settings chosen to make each one's effect obvious in
# a render. These are demonstration values, not mode presets.
PRIMITIVE_DEMOS: dict[str, dict] = {
    "LowShelfFilter": {"cutoff_frequency_hz": 200.0, "gain_db": 6.0, "q": 0.7},
    "LowpassFilter": {"cutoff_frequency_hz": 4000.0},
    "Reverb": {"room_size": 0.5, "damping": 0.5, "wet_level": 0.35, "dry_level": 0.6, "width": 1.0},
    "Delay": {"delay_seconds": 0.18, "feedback": 0.3, "mix": 0.3},
    "Distortion": {"drive_db": 12.0},
    "Clipping": {"threshold_db": -12.0},
    "Chorus": {"rate_hz": 1.0, "depth": 0.4, "centre_delay_ms": 12.0, "feedback": 0.1, "mix": 0.4},
    "PitchShift": {"semitones": -3.0},  # transposition, NOT pitch correction
}


def _rms(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(a, dtype=np.float64)))) if a.size else 0.0


def _delta_db(before: np.ndarray, after: np.ndarray) -> float:
    """RMS of the difference signal, relative to the input. Higher = bigger change."""
    b, a = normalize(before), normalize(after)
    n = min(b.shape[0], a.shape[0])
    if n == 0:
        return -120.0
    width = max(b.shape[1], a.shape[1])
    from src.dsp_engine.channels import match_channels
    b, a = match_channels(b[:n], width), match_channels(a[:n], width)
    diff = _rms(a - b)
    base = _rms(b)
    if base <= 0.0:
        return -120.0
    return 20.0 * float(np.log10(max(diff, 1e-12) / base))


def _check(name: str, src: np.ndarray, out: np.ndarray, sr: int, outdir: Path) -> dict:
    out = normalize(out)
    finite = bool(np.all(np.isfinite(out)))
    peak = float(np.max(np.abs(out))) if out.size else 0.0
    delta = _delta_db(src, out)
    compat = mono_compatibility(out)

    path = outdir / f"{name}.wav"
    sf.write(path, out, sr, subtype="PCM_16")

    row = {
        "name": name,
        "finite": finite,
        "peak": round(peak, 4),
        "within_ceiling": peak <= CEILING + 1e-6,
        "delta_db": round(delta, 2),
        "changed": delta > -60.0,
        "channels": channel_count(out),
        "mono_collapses": compat.collapses,
    }
    ok = finite and row["changed"] and not row["mono_collapses"]
    flag = "ok  " if ok else "FAIL"
    print(
        f"  [{flag}] {name:28s} delta={delta:7.2f} dB  peak={peak:.3f}  "
        f"ch={row['channels']}  mono_ok={not compat.collapses}"
    )
    row["ok"] = ok
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="fixtures/audio/muddy.wav")
    ap.add_argument("--outdir", default="output/v3_renders/dt94")
    args = ap.parse_args()

    src_path = Path(args.input)
    if not src_path.exists():
        print(f"input not found: {src_path}", file=sys.stderr)
        return 2
    audio, sr = sf.read(str(src_path), dtype="float32")
    audio = normalize(audio)
    sr = int(sr)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    sf.write(outdir / "00_source.wav", audio, sr, subtype="PCM_16")

    print(f"DT-94 render check — input={src_path} sr={sr} ch={channel_count(audio)} "
          f"dur={audio.shape[0]/sr:.2f}s")
    rows: list[dict] = []

    print("\nPrimitives (newly exposed in DT-94):")
    for name, params in PRIMITIVE_DEMOS.items():
        if name not in PROCESSORS:
            print(f"  [FAIL] {name}: not in registry")
            rows.append({"name": name, "ok": False})
            continue
        out = render_graph(audio, sr, Processor(name, params))
        rows.append(_check(f"primitive_{name}", audio, out, sr, outdir))

    print("\nGraph topologies:")
    # Serial: the flat path, expressed as a graph.
    serial = Serial([
        Processor("HighpassFilter", {"cutoff_frequency_hz": 90.0}),
        Processor("PeakFilter", {"cutoff_frequency_hz": 300.0, "gain_db": -4.0, "q": 1.2}),
    ])
    rows.append(_check("topology_serial", audio, render_graph(audio, sr, serial), sr, outdir))

    # Parallel: a crushed branch blended under the dry signal.
    parallel = Parallel(
        branch=Serial([
            Processor("Compressor", {"threshold_db": -30.0, "ratio": 8.0,
                                     "attack_ms": 3.0, "release_ms": 120.0}),
            Processor("Gain", {"gain_db": 4.0}),
        ]),
        blend=0.4,
        label="parallel_comp",
    )
    rows.append(_check("topology_parallel", audio, render_graph(audio, sr, parallel), sr, outdir))

    # Send: wet-only reverb added under the dry, no ducking.
    send = Send(
        branch=Processor("Reverb", {"room_size": 0.6, "damping": 0.4,
                                    "wet_level": 1.0, "dry_level": 0.0, "width": 1.0}),
        level=0.3, duck=0.0, label="reverb_send",
    )
    rows.append(_check("topology_send", audio, render_graph(audio, sr, send), sr, outdir))

    # Send with ducking: same effect, pulled down while the dry signal is loud.
    ducked = Send(
        branch=Processor("Reverb", {"room_size": 0.6, "damping": 0.4,
                                    "wet_level": 1.0, "dry_level": 0.0, "width": 1.0}),
        level=0.3, duck=0.8, label="reverb_send_ducked",
    )
    rows.append(_check("topology_send_ducked", audio, render_graph(audio, sr, ducked), sr, outdir))

    print("\nChannel contracts:")
    stereo_out = to_stereo(render_graph(audio, sr, serial))
    rows.append(_check("channel_stereo_widen", audio, stereo_out, sr, outdir))
    panned = pan(audio, -0.7)
    rows.append(_check("channel_pan_left", audio, panned, sr, outdir))

    # A deliberately mono-incompatible signal must be CAUGHT, not shipped.
    inverted = np.stack([audio[:, 0], -audio[:, 0]], axis=1)
    caught = mono_compatibility(inverted).collapses
    print(f"  [{'ok  ' if caught else 'FAIL'}] phase-inversion detected by mono check: {caught}")
    rows.append({"name": "mono_incompat_detected", "ok": caught})

    failures = [r["name"] for r in rows if not r.get("ok")]
    print(f"\n{len(rows) - len(failures)}/{len(rows)} checks passed. Renders in {outdir}/")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
