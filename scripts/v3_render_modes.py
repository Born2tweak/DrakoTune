"""DT-95 mode renders + distinctness gate.

Renders every mode at every intensity, measures pairwise distinctness, and
applies the same hard safety checks the executor enforces. Writes audio for
optional listening.

    python scripts/v3_render_modes.py --input VOCAL.wav

Nothing here is a quality claim. Distinctness says two modes are not the same
thing; it does not say either sounds good. Renders made from the D-029 private
corpus are local/internal only and are gitignored.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dsp_engine.channels import mono_compatibility, normalize  # noqa: E402
from src.dsp_engine.graph import render_graph  # noqa: E402
from src.modes import INTENSITY_ORDER, build_graph, get_mode, list_modes  # noqa: E402
from src.modes.distinctness import compare_all  # noqa: E402

CEILING = 10.0 ** (-0.2 / 20.0)


def _rms(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(a, dtype=np.float64)))) if a.size else 0.0


def _crest_db(a: np.ndarray) -> float:
    r = _rms(a)
    if r <= 0:
        return 0.0
    return 20.0 * float(np.log10(max(float(np.max(np.abs(a))), 1e-12) / r))


def _apply_ceiling(audio: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > CEILING:
        audio = audio * np.float32(CEILING / peak)
    return np.clip(audio, -1.0, 1.0).astype(np.float32)


def _safety(src: np.ndarray, out: np.ndarray, sr: int) -> dict:
    """Hard technical safety — the checks that survive D-030 unchanged."""
    finite = bool(np.all(np.isfinite(out)))
    peak = float(np.max(np.abs(out))) if out.size else 0.0
    dur_in = src.shape[0] / sr
    dur_out = out.shape[0] / sr
    # A send tail legitimately extends duration; losing duration never is.
    duration_ok = dur_out >= dur_in - 1e-3
    src_rms, out_rms = _rms(src), _rms(out)
    level_drop_db = (
        20.0 * float(np.log10(max(out_rms, 1e-12) / max(src_rms, 1e-12)))
        if src_rms > 0 else 0.0
    )
    return {
        "finite": finite,
        "peak": round(peak, 4),
        "within_ceiling": peak <= CEILING + 1e-6,
        "duration_ok": duration_ok,
        "level_delta_db": round(level_drop_db, 2),
        # Catastrophic gating = the performance largely removed.
        "not_gated_away": level_drop_db > -20.0,
        "crest_db": round(_crest_db(out), 2),
        "mono_ok": not mono_compatibility(out).collapses,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", default="output/v3_renders/dt95")
    ap.add_argument("--label", default="source")
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
    sf.write(outdir / f"00_{args.label}_original.wav", audio, sr, subtype="PCM_16")

    print(f"DT-95 mode renders — sr={sr} dur={audio.shape[0]/sr:.1f}s ch={audio.shape[1]}")
    rows: list[dict] = []
    failures: list[str] = []

    for mode in list_modes():
        spec = get_mode(mode)
        print(f"\n{spec.title}  — {spec.summary}")
        for intensity in INTENSITY_ORDER:
            graph = build_graph(mode, intensity)
            out = _apply_ceiling(render_graph(audio, sr, graph))
            checks = _safety(audio, out, sr)
            name = f"{args.label}_{mode}_{intensity.value}"
            sf.write(outdir / f"{name}.wav", out, sr, subtype="PCM_16")

            ok = all([checks["finite"], checks["within_ceiling"], checks["duration_ok"],
                      checks["not_gated_away"], checks["mono_ok"]])
            if not ok:
                failures.append(name)
            print(f"  [{'ok  ' if ok else 'FAIL'}] {intensity.value:9s} "
                  f"peak={checks['peak']:.3f} level={checks['level_delta_db']:+6.2f} dB "
                  f"crest={checks['crest_db']:5.2f} dB")
            rows.append({"mode": mode, "intensity": intensity.value, **checks})

    print("\nPairwise distinctness (level-matched, at each mode's shipping intensity):")
    dist_rows = []
    for intensity in (INTENSITY_ORDER[1], INTENSITY_ORDER[2]):  # balanced, bold
        results = compare_all(list(list_modes()), audio, sr, intensity)
        for r in results:
            mark = "ok  " if r.distinct else "FAIL"
            if not r.distinct:
                failures.append(f"distinctness:{r.mode_a}~{r.mode_b}@{intensity.value}")
            print(f"  [{mark}] {intensity.value:9s} {r.mode_a:12s} vs {r.mode_b:12s} "
                  f"delta={r.delta_db:7.2f} dB  structural={r.structural}")
            dist_rows.append({"intensity": intensity.value, **r.to_dict()})

    (outdir / "report.json").write_text(
        json.dumps({"renders": rows, "distinctness": dist_rows}, indent=2), encoding="utf-8"
    )
    print(f"\nRenders + report.json in {outdir}/")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("All renders passed hard safety and all mode pairs are distinct.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
