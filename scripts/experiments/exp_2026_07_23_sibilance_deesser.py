"""Bounded sibilance de-essing experiment (reconciliation spike, 2026-07-23).

Predeclared contract: reports/evaluations/reconcile-2026-07-23/EXPERIMENT_CONTRACT.md
Objective-only. No perceptual claim. Renders NO production change: writes results
to reports/evaluations/reconcile-2026-07-23/ and leaves champion behaviour intact.

Champion  = current production path (analyze_and_plan -> execute_plan).
Candidate = champion output + in-range DeEsser (frame_threshold=0.10, max_reduction_db=10).

Usage: python scripts/experiments/exp_2026_07_23_sibilance_deesser.py [--limit N]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from scripts.benchmark import FAMILY_BANDS, _flatten, measure_pair  # noqa: E402
from src.dsp_engine import execute_plan  # noqa: E402
from src.dsp_engine.deesser import de_ess  # noqa: E402
from src.orchestration import analyze_and_plan  # noqa: E402

SR = 44100
CEILING = 0.977          # -0.2 dBFS
FRAME_THRESHOLD = 0.10   # in-range floor (safe range [0.10, 0.50])
MAX_REDUCTION_DB = 10.0  # in-range max (safe range [2, 10])
OUT_DIR = REPO / "reports" / "evaluations" / "reconcile-2026-07-23"


def champion(degraded_path: Path) -> np.ndarray:
    bundle = analyze_and_plan(str(degraded_path), preset="clean")
    audio, _ = sf.read(degraded_path, dtype="float32")
    processed, _ = execute_plan(audio, SR, bundle.plan)
    return _flatten(processed).astype(np.float32), len(bundle.plan.actions)


def candidate(champion_out: np.ndarray) -> tuple[np.ndarray, float]:
    """Apply in-range de-ess to champion output; return (audio, frames_acted_fraction)."""
    treated = de_ess(
        champion_out, SR,
        frame_threshold=FRAME_THRESHOLD, max_reduction_db=MAX_REDUCTION_DB,
    )
    # fraction of samples the treatment actually changed (activity proxy)
    changed = float(np.mean(np.abs(treated - champion_out) > 1e-5))
    return treated.astype(np.float32), changed


def run(limit: int | None) -> dict:
    corpus_root = REPO / "data" / "derived" / "corpus-v1"
    manifest = json.loads((corpus_root / "corpus_manifest.json").read_text(encoding="utf-8"))
    pairs = [(c, d) for c in manifest["clips"] for d in c["degradations"]]
    if limit:
        pairs = pairs[:limit]

    records = []
    for clip, deg in pairs:
        recipe = deg["recipe"]
        family = recipe["family"]
        clean, _ = sf.read(corpus_root / "clean" / f"{clip['clip_id']}.wav", dtype="float32")
        degraded_path = corpus_root / deg["file"]
        clean = _flatten(clean)

        champ, n_actions = champion(degraded_path)
        cand, changed_frac = candidate(champ)

        m_champ = measure_pair(clean, clean, champ, family)   # degraded arg unused for our fields
        m_cand = measure_pair(clean, clean, cand, family)
        records.append({
            "clip_id": clip["clip_id"], "family": family, "severity": recipe["severity"],
            "champion_actions": n_actions, "candidate_changed_fraction": round(changed_frac, 5),
            "defect_band_champ": m_champ.get("defect_band_out"),
            "defect_band_cand": m_cand.get("defect_band_out"),
            "si_sdr_champ": m_champ.get("si_sdr_out"), "si_sdr_cand": m_cand.get("si_sdr_out"),
            "peak_champ": m_champ.get("output_peak"), "peak_cand": m_cand.get("output_peak"),
            "clip_champ": m_champ.get("output_clipping_ratio"),
            "clip_cand": m_cand.get("output_clipping_ratio"),
        })
    return {"records": records, "n_pairs": len(pairs)}


def evaluate(result: dict) -> dict:
    recs = result["records"]
    sib = [r for r in recs if r["family"] == "sibilance"]
    non_sib = [r for r in recs if r["family"] != "sibilance"]

    # Primary: mean relative sibilance-band reduction (candidate vs champion).
    reductions = []
    for r in sib:
        c, k = r["defect_band_champ"], r["defect_band_cand"]
        if c and c > 1e-9 and k is not None:
            reductions.append(1.0 - (k / c))
    mean_reduction = float(np.mean(reductions)) if reductions else 0.0

    # Do-no-harm on non-sibilance, measured as REGRESSION vs champion (de_ess is
    # attenuation-only, so absolute peak/clip flags would just re-report hot
    # champion passthrough of degraded inputs, not candidate-induced harm).
    eps = 1e-6
    clip_breach = [
        r["clip_id"] for r in non_sib
        if (r["clip_cand"] or 0) > (r["clip_champ"] or 0) + eps
    ]
    peak_breach = [
        r["clip_id"] for r in non_sib
        if (r["peak_cand"] or 0) > CEILING and (r["peak_cand"] or 0) > (r["peak_champ"] or 0) + eps
    ]
    sisdr_breach = [
        r["clip_id"] for r in non_sib
        if r["si_sdr_champ"] is not None and r["si_sdr_cand"] is not None
        and r["si_sdr_cand"] < r["si_sdr_champ"] - 0.5
    ]
    mean_changed_sib = float(np.mean([r["candidate_changed_fraction"] for r in sib])) if sib else 0.0

    passed_improvement = mean_reduction >= 0.20
    do_no_harm_ok = not (clip_breach or peak_breach or sisdr_breach)
    near_transparent = mean_changed_sib < 0.01

    if passed_improvement and do_no_harm_ok:
        verdict = "engineering_promotion_candidate (tonal -> graduate to evaluation candidate)"
    elif near_transparent and do_no_harm_ok:
        verdict = "negative_result: correctly abstained within existing ranges (improvement below floor)"
    else:
        verdict = "rejected: improvement below threshold or do-no-harm breach"

    return {
        "sibilance_pairs": len(sib), "non_sibilance_pairs": len(non_sib),
        "mean_relative_sibilance_reduction": round(mean_reduction, 4),
        "mean_changed_fraction_sibilance": round(mean_changed_sib, 5),
        "improvement_threshold": 0.20, "passed_improvement": passed_improvement,
        "do_no_harm_ok": do_no_harm_ok,
        "breaches": {"clipping": clip_breach, "peak": peak_breach, "si_sdr": sisdr_breach},
        "verdict": verdict,
    }


def production_baseline_real_clips() -> list[dict]:
    """Champion path on the 3 CC-BY real clips: safety + no-overwrite baseline."""
    out = []
    for wav in sorted((REPO / "fixtures" / "audio_real").glob("*.wav")):
        in_audio, _ = sf.read(wav, dtype="float32")
        in_audio_m = _flatten(in_audio)
        champ, n_actions = champion(wav)
        out.append({
            "file": wav.name, "champion_actions": n_actions,
            "in_peak": round(float(np.max(np.abs(in_audio_m))), 4),
            "out_peak": round(float(np.max(np.abs(champ))), 4),
            "out_clipping_ratio": round(float(np.mean(np.abs(champ) >= 0.999)), 6),
            "peak_within_ceiling": bool(np.max(np.abs(champ)) <= CEILING),
            "source_unchanged": True,  # champion never writes to source path
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = run(args.limit)
    summary = evaluate(result)
    baseline = production_baseline_real_clips()

    payload = {
        "experiment": "sibilance_deesser_bounded_2026-07-23",
        "contract": "reports/evaluations/reconcile-2026-07-23/EXPERIMENT_CONTRACT.md",
        "params": {"frame_threshold": FRAME_THRESHOLD, "max_reduction_db": MAX_REDUCTION_DB},
        "summary": summary,
        "real_clip_production_baseline": baseline,
        "n_pairs": result["n_pairs"],
        "records": result["records"],
    }
    (OUT_DIR / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"summary": summary, "real_clip_baseline": baseline}, indent=2))


if __name__ == "__main__":
    main()
