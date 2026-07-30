"""DT-98 render verification: transposition and artificial doubling on real audio.

Two things are checked, both on rendered audio rather than on configuration:

  * `PitchShift` behaves as **transposition only** — a fixed interval applied to
    the whole signal. Semitone steps, octaves and cent-level detune are all the
    same operation at different magnitudes. Nothing here detects pitch or moves
    a note toward a scale; that is DT-100.
  * `Doubler` produces a **stereo image that survives mono summing**. A doubled
    vocal that cancels on a phone speaker is a defect, so every doubling render
    reports inter-channel correlation and the mono-sum level change, and the run
    fails if any of them collapses.

    python scripts/v3_render_doubling.py [--input PATH] [--outdir DIR]

Renders exist so a human can listen. They are not evidence of quality, and no
verdict in this script is perceptual.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dsp_engine.channels import (  # noqa: E402
    channel_count,
    match_channels,
    mono_compatibility,
    normalize,
)
from src.dsp_engine.graph import (  # noqa: E402
    DoubleVoice,
    Doubler,
    Processor,
    render_graph,
)
from src.dsp_engine.executor import _apply_ceiling  # noqa: E402, PLC2701
from src.modes.contracts import build_graph  # noqa: E402

CEILING = 10.0 ** (-0.2 / 20.0)

# Transposition demonstrations. The point is that one operation covers detune,
# semitone shift and octave shift — there is no separate "tuning" mode.
TRANSPOSITIONS: dict[str, float] = {
    "detune_minus_10_cents": -0.10,
    "detune_plus_10_cents": 0.10,
    "semitone_down": -1.0,
    "semitone_up": 1.0,
    "octave_down": -12.0,
    "octave_up": 12.0,
}

# Doubling configurations, widest-used first.
DOUBLES: dict[str, tuple[DoubleVoice, ...]] = {
    "double_pair_wide": (DoubleVoice(-9.0, 17.0, -0.7), DoubleVoice(11.0, 25.0, 0.7)),
    "double_pair_narrow": (DoubleVoice(-6.0, 12.0, -0.35), DoubleVoice(7.0, 19.0, 0.35)),
    "double_triple": (DoubleVoice(-9.0, 17.0, -0.8), DoubleVoice(11.0, 25.0, 0.8),
                      DoubleVoice(5.0, 31.0, 0.0)),
    "double_centre_only": (DoubleVoice(-8.0, 21.0, 0.0),),
}


def _rms(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(a, dtype=np.float64)))) if a.size else 0.0


def _delta_db(before: np.ndarray, after: np.ndarray) -> float:
    b, a = normalize(before), normalize(after)
    n = min(b.shape[0], a.shape[0])
    if n == 0:
        return -120.0
    width = max(b.shape[1], a.shape[1])
    b, a = match_channels(b[:n], width), match_channels(a[:n], width)
    base = _rms(b)
    if base <= 0.0:
        return -120.0
    return 20.0 * float(np.log10(max(_rms(a - b), 1e-12) / base))


def _check(name: str, src: np.ndarray, out: np.ndarray, sr: int, outdir: Path,
           expect_stereo: bool = False) -> dict:
    out = normalize(out)
    finite = bool(np.all(np.isfinite(out)))
    peak = float(np.max(np.abs(out))) if out.size else 0.0
    delta = _delta_db(src, out)
    compat = mono_compatibility(out)
    channels = channel_count(out)

    sf.write(outdir / f"{name}.wav", out, sr, subtype="PCM_16")

    # `render_graph` deliberately applies no output safety — the ceiling lives in
    # the executor so every path shares one. A raw graph render may therefore
    # exceed unity (transposing up an octave does). What must hold is that the
    # ceiling still brings it back, so that is checked here rather than a
    # pre-ceiling peak being reported as if it were the delivered signal.
    safe = _apply_ceiling(out)
    safe_peak = float(np.max(np.abs(safe))) if safe.size else 0.0

    row = {
        "name": name,
        "finite": finite,
        "peak_pre_ceiling": round(peak, 4),
        "peak_after_ceiling": round(safe_peak, 4),
        "ceiling_engaged": peak > CEILING + 1e-6,
        "within_ceiling": safe_peak <= CEILING + 1e-6,
        "delta_db": round(delta, 2),
        "changed": delta > -60.0,
        "channels": channels,
        "mono": compat.to_dict(),
    }
    ok = (finite and row["changed"] and row["within_ceiling"]
          and not compat.collapses
          and (channels == 2 or not expect_stereo))
    row["ok"] = ok
    ceil_note = " (ceiling engaged)" if row["ceiling_engaged"] else ""
    print(f"  [{'ok  ' if ok else 'FAIL'}] {name:26s} delta={delta:7.2f} dB  "
          f"peak={peak:.3f}->{safe_peak:.3f}{ceil_note}  ch={channels}  "
          f"corr={compat.correlation:+.3f}  mono_sum={compat.mono_sum_delta_db:+.2f} dB")
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="fixtures/audio/muddy.wav")
    ap.add_argument("--outdir", default="output/v3_renders/dt98")
    args = ap.parse_args()

    src_path = Path(args.input)
    if not src_path.exists():
        print(f"input not found: {src_path}", file=sys.stderr)
        return 2
    audio, sr = sf.read(str(src_path), dtype="float32")
    audio, sr = normalize(audio), int(sr)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    sf.write(outdir / "00_source.wav", audio, sr, subtype="PCM_16")

    print(f"DT-98 render check — input={src_path} sr={sr} "
          f"ch={channel_count(audio)} dur={audio.shape[0]/sr:.2f}s")
    rows: list[dict] = []

    print("\nTransposition (PitchShift as a fixed interval — never note correction):")
    for name, semitones in TRANSPOSITIONS.items():
        out = render_graph(audio, sr, Processor("PitchShift", {"semitones": semitones}))
        rows.append(_check(f"transpose_{name}", audio, out, sr, outdir))

    print("\nArtificial doubling (width; every render must survive mono summing):")
    for name, voices in DOUBLES.items():
        node = Doubler(voices=voices, level=0.35)
        out = render_graph(audio, sr, node)
        row = _check(name, audio, out, sr, outdir, expect_stereo=True)
        row["describe"] = node.describe()
        rows.append(row)

    print("\nModern Rap with doubling in context:")
    for intensity in ("subtle", "bold"):
        out = render_graph(audio, sr, build_graph("modern_rap", intensity))
        rows.append(_check(f"modern_rap_{intensity}", audio, out, sr, outdir))

    failed = [r["name"] for r in rows if not r["ok"]]
    summary = {
        "milestone": "DT-98",
        "input": str(src_path),
        "sample_rate": sr,
        "n_renders": len(rows),
        "failed": failed,
        "note": "Renders are for listening. No perceptual claim; PitchShift is "
                "transposition only and no chain performs pitch correction.",
        "results": rows,
    }
    (outdir / "render_report.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\n{len(rows) - len(failed)}/{len(rows)} ok; wrote {outdir}")
    if failed:
        print("FAILED:", ", ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
