"""Per-defect objective benchmark over an evaluation corpus (M23).

For every degraded clip in the corpus, runs the requested engines and measures,
against the paired clean reference and loudness-matched:

  si_sdr_in / si_sdr_out (dB, delta = improvement toward the clean reference)
  seg_snr_in / seg_snr_out
  defect-band energy delta (the band the recipe family targets)
  output true peak, output clipping ratio

Results aggregate per (family, severity, engine) into
reports/evaluations/<corpus>/<run_id>/benchmark.json + summary.md (no audio).

This is objective evidence only: it makes no perceptual claim (ADR 0004).
Engines: v2 (decision engine), legacy (adaptive chain), generic (Alpha-1 chain).

    python scripts/benchmark.py                     # all engines, full corpus
    python scripts/benchmark.py --engines v2 --limit 10
"""

import argparse
import json
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.dsp.diagnose import diagnose as legacy_diagnose  # noqa: E402
from src.dsp.pipeline import process_audio as legacy_process  # noqa: E402
from src.dsp_engine import execute_plan  # noqa: E402
from src.evaluation.ab_export import LoudnessMatchError, loudness_matched_pair  # noqa: E402
from src.evaluation.reference_metrics import segmental_snr, si_sdr  # noqa: E402
from src.orchestration import analyze_and_plan  # noqa: E402

BENCHMARK_VERSION = "1.0.0"
SR = 44100

# Family -> spectral band whose energy the defect concentrates in (Hz).
FAMILY_BANDS = {
    "noise": (6000, 16000),      # noise floor shows up broadband; HF is signal-sparse
    "hum": (40, 200),
    "clipping": (4000, 12000),   # clipping splatter harmonics
    "reverb": None,              # no single band; SI-SDR carries it
    "harshness": (3000, 5000),
    "sibilance": (5500, 12000),
    "proximity": (60, 250),
    "low_level": None,
    "codec": None,
}


def _band_energy_ratio(audio: np.ndarray, lo: float, hi: float) -> float:
    spectrum = np.abs(np.fft.rfft(audio.astype(np.float64))) ** 2
    freqs = np.fft.rfftfreq(len(audio), 1.0 / SR)
    total = float(np.sum(spectrum)) + 1e-20
    return float(np.sum(spectrum[(freqs >= lo) & (freqs <= hi)])) / total


def _flatten(audio: np.ndarray) -> np.ndarray:
    return audio[:, 0] if audio.ndim == 2 else audio


def run_engine(engine: str, degraded_path: Path) -> np.ndarray:
    """Process one file with one engine; returns mono float32."""
    if engine == "v2":
        bundle = analyze_and_plan(str(degraded_path))
        audio, _ = sf.read(degraded_path, dtype="float32")
        processed, _ = execute_plan(audio, SR, bundle.plan)
        return _flatten(processed).astype(np.float32)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.wav"
        if engine == "legacy":
            profile = legacy_diagnose(str(degraded_path))
            legacy_process(str(degraded_path), str(out), profile=profile)
        elif engine == "generic":
            legacy_process(str(degraded_path), str(out))
        else:
            raise ValueError(f"unknown engine: {engine}")
        audio, _ = sf.read(out, dtype="float32")
    return _flatten(audio).astype(np.float32)


def measure_pair(clean: np.ndarray, degraded: np.ndarray, processed: np.ndarray,
                 family: str) -> dict:
    """Loudness-matched reference metrics for one (clean, degraded, processed) triple."""
    result: dict = {}
    try:
        in_pair = loudness_matched_pair(clean, degraded, SR)
        out_pair = loudness_matched_pair(clean, processed, SR)
    except LoudnessMatchError as exc:
        return {"error": f"loudness_match: {exc}"}

    result["si_sdr_in"] = si_sdr(in_pair.a, in_pair.b)
    result["si_sdr_out"] = si_sdr(out_pair.a, out_pair.b)
    result["si_sdr_delta"] = result["si_sdr_out"] - result["si_sdr_in"]
    result["seg_snr_in"] = segmental_snr(in_pair.a, in_pair.b, SR)
    result["seg_snr_out"] = segmental_snr(out_pair.a, out_pair.b, SR)
    result["seg_snr_delta"] = result["seg_snr_out"] - result["seg_snr_in"]

    band = FAMILY_BANDS.get(family)
    if band is not None:
        lo, hi = band
        result["defect_band_in"] = _band_energy_ratio(in_pair.b, lo, hi)
        result["defect_band_out"] = _band_energy_ratio(out_pair.b, lo, hi)
        result["defect_band_delta"] = result["defect_band_out"] - result["defect_band_in"]

    result["output_peak"] = float(np.max(np.abs(processed)))
    result["output_clipping_ratio"] = float(np.mean(np.abs(processed) >= 0.999))
    return result


def run(corpus_version: str, engines: list[str], limit: int | None) -> Path:
    corpus_root = REPO / "data" / "derived" / corpus_version
    manifest = json.loads((corpus_root / "corpus_manifest.json").read_text(encoding="utf-8"))

    pairs = []
    for clip in manifest["clips"]:
        for deg in clip["degradations"]:
            pairs.append((clip, deg))
    if limit:
        pairs = pairs[:limit]

    records = []
    started = time.time()
    for i, (clip, deg) in enumerate(pairs):
        clean, _ = sf.read(corpus_root / "clean" / f"{clip['clip_id']}.wav", dtype="float32")
        degraded_path = corpus_root / deg["file"]
        degraded, _ = sf.read(degraded_path, dtype="float32")
        recipe = deg["recipe"]
        for engine in engines:
            processed = run_engine(engine, degraded_path)
            metrics = measure_pair(clean, degraded, processed, recipe["family"])
            records.append({
                "clip_id": clip["clip_id"], "source_dataset": clip["source_dataset"],
                "family": recipe["family"], "severity": recipe["severity"],
                "recipe_id": recipe["id"], "engine": engine, **metrics,
            })
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(pairs)} pairs, {time.time() - started:.0f}s", flush=True)

    # Aggregate per (family, severity, engine).
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        if "error" not in r:
            groups[(r["family"], r["severity"], r["engine"])].append(r)
    aggregates = []
    for (family, severity, engine), rows in sorted(groups.items()):
        def mean(key):
            vals = [row[key] for row in rows if key in row and np.isfinite(row[key])]
            return round(float(np.mean(vals)), 3) if vals else None
        aggregates.append({
            "family": family, "severity": severity, "engine": engine, "n": len(rows),
            "si_sdr_delta_mean": mean("si_sdr_delta"),
            "seg_snr_delta_mean": mean("seg_snr_delta"),
            "defect_band_delta_mean": mean("defect_band_delta"),
            "output_clipping_max": max(row["output_clipping_ratio"] for row in rows),
        })

    run_id = time.strftime("%Y%m%d-%H%M%S")
    out_dir = REPO / "reports" / "evaluations" / corpus_version / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "benchmark.json").write_text(json.dumps({
        "benchmark_version": BENCHMARK_VERSION, "corpus_version": corpus_version,
        "engines": engines, "pair_count": len(pairs), "records": records,
        "aggregates": aggregates,
    }, indent=2), encoding="utf-8")

    lines = [
        f"# Benchmark {run_id} — {corpus_version}", "",
        f"Engines: {', '.join(engines)} · {len(pairs)} degraded pairs · "
        f"benchmark v{BENCHMARK_VERSION}. Objective evidence only (ADR 0004): "
        "loudness-matched, reference-based; no perceptual claim.", "",
        "| family | severity | engine | n | ΔSI-SDR (dB) | ΔsegSNR (dB) | Δdefect-band | out-clip max |",
        "|---|---|---|--:|--:|--:|--:|--:|",
    ]
    for a in aggregates:
        lines.append(
            f"| {a['family']} | {a['severity']} | {a['engine']} | {a['n']} "
            f"| {a['si_sdr_delta_mean']} | {a['seg_snr_delta_mean']} "
            f"| {a['defect_band_delta_mean']} | {a['output_clipping_max']:.4f} |"
        )
    errors = [r for r in records if "error" in r]
    lines += ["", f"Errored pairs: {len(errors)}"]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_dir}")
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Objective per-defect benchmark")
    parser.add_argument("--corpus", default="corpus-v1")
    parser.add_argument("--engines", nargs="+", default=["v2", "legacy", "generic"],
                        choices=["v2", "legacy", "generic"])
    parser.add_argument("--limit", type=int, default=None, help="limit degraded pairs (smoke runs)")
    args = parser.parse_args()
    run(args.corpus, args.engines, args.limit)


if __name__ == "__main__":
    main()
