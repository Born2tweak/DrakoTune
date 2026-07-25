"""DT-55B/C/D real-corpus runner (LOCAL ONLY; authorized by D-029).

Reads the gitignored manifest, refuses anything without consent_ref=D-029 or with a
rejected class, decodes analysis copies (ffmpeg -> 44.1k mono WAV, cached under
data/restricted/analysis/), verifies pairs by signal evidence, aligns phrases,
profiles raw->wet deltas, renders the current champion on each raw, and ranks the
remaining champion->wet gap. Outputs:
  - data/restricted/analysis/…            (audio + per-phrase JSON; NEVER committed)
  - reports/evaluations/paired-corpus/<runid>/gap_report.{json,md}  (metrics only)

No perceptual claim. Deltas from lossy sources are directional guidance only.

Usage: python scripts/paired_corpus_run.py [--limit N]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.dsp.preprocess import _find_ffmpeg  # noqa: E402
from src.dsp_engine import execute_plan  # noqa: E402
from src.orchestration import analyze_and_plan  # noqa: E402
from src.paired_corpus import align_pair, classify_pair, phrase_features, profile_pair  # noqa: E402
from src.paired_corpus.deltas import gap_noise_floor_db  # noqa: E402

SR = 44100
MANIFEST = REPO / "data" / "restricted" / "private_corpus_manifest.json"
ANALYSIS = REPO / "data" / "restricted" / "analysis"
REPORTS = REPO / "reports" / "evaluations" / "paired-corpus"
HUMAN_CONFIRMATION = "owner_asserted_exact_pairs_2026-07-24"   # transcript: pairing confirmed YES


def decode(src: Path, digest: str) -> Path:
    """ffmpeg -> cached 44.1k mono 16-bit analysis WAV (originals untouched)."""
    out = ANALYSIS / f"{digest[:16]}.wav"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [_find_ffmpeg(), "-y", "-v", "error", "-i", str(src),
         "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", str(out)],
        check=True,
    )
    return out


def load(path: Path) -> np.ndarray:
    audio, sr = sf.read(path, dtype="float32")
    assert sr == SR
    return audio if audio.ndim == 1 else audio[:, 0]


def authorized_files(manifest: dict) -> dict[str, dict]:
    """Fail-closed: only approved_local_internal_eval WITH a consent_ref pass."""
    ok = {}
    for rec in manifest["files"]:
        if rec["rights_class"] == "approved_local_internal_eval" and rec["consent_ref"]:
            ok[rec["filename"]] = rec
    return ok


def build_pairs(manifest: dict, allowed: dict[str, dict]) -> list[dict]:
    pairs = []
    for key, names in manifest["candidate_pair_groups"].items():
        members = [allowed[n] for n in names if n in allowed]
        raws = [m for m in members if m["role_hint"] == "raw"]
        wets = [m for m in members if m["role_hint"] != "raw"]
        if len(raws) >= 1 and len(wets) >= 1:
            pairs.append({"pair_id": key, "raw": raws[0], "wet": wets[0]})
    return pairs


GAP_AXES = [
    "crest_db", "lowmid_250_500", "box_300_700", "harsh_2500_5000",
    "sib_5500_12000", "air_10000_16000", "tilt_db_per_oct",
]


def champion_render(raw_wav: Path) -> np.ndarray:
    bundle = analyze_and_plan(str(raw_wav), preset="clean")
    audio = load(raw_wav)
    processed, _ = execute_plan(audio, SR, bundle.plan)
    out = processed[:, 0] if processed.ndim == 2 else processed
    return out.astype(np.float32), len(bundle.plan.actions)


def _oracle_markdown(rows: list[dict], agg) -> str:
    lines = [
        "# DT-55E oracle probe — evidence report", "",
        "Authorization D-029 (local/internal/eval-only). **Diagnostic only**: the",
        "probe forces the planner's OWN treatments to engage and measures distance",
        "to the aligned wet target. No threshold tuned, nothing promoted, no",
        "perceptual claim. Sources are lossy — distances are directional.", "",
        "`inconclusive_alignment` pairs are EXCLUDED from every aggregate below.", "",
        "## Per-pair evidence", "",
        "| pair | champ acts | phrases | champ→wet | oracle→wet | improvement | "
        "active processors | conf | classification |",
        "|---|--:|--:|--:|--:|--:|---|--:|---|",
    ]
    for r in rows:
        if "error" in r:
            lines.append(f"| {r['pair_id']} | | | | | | error: {r['error'][:40]} | | — |")
            continue
        if "classification" not in r:
            lines.append(f"| {r['pair_id']} | | | | | | | | {r.get('verdict','—')} |")
            continue
        procs = ", ".join(r["active_processors"]) or "—"
        cd, od = r["champion_distance"], r["oracle_distance"]
        fmt = (lambda v: "inf" if v == float("inf") or v is None else f"{v:.3f}")
        lines.append(
            f"| {r['pair_id']} | {r['champion_actions']} | {r['n_measured_phrases']} "
            f"| {fmt(cd)} | {fmt(od)} | {r['improvement_pct']:+.1f}% | {procs} "
            f"| {r['confidence']:.2f} | **{r['classification']}** |")
    lines += [
        "", "## Aggregate (valid pairs only)", "",
        f"- pairs total: **{agg.n_total}**; valid: **{agg.n_valid}**; "
        f"excluded as inconclusive: **{agg.n_excluded}**",
        f"- median improvement: **{agg.median_improvement_pct:+.2f}%**",
        f"- mean improvement: **{agg.mean_improvement_pct:+.2f}%** "
        f"(bootstrap 95% CI {agg.ci95_mean_improvement_pct[0]:+.2f}% .. "
        f"{agg.ci95_mean_improvement_pct[1]:+.2f}%)",
        f"- champion abstention rate: **{agg.abstention_rate:.0%}**; "
        f"engagement rate: **{agg.engagement_rate:.0%}**", "",
        "### Classification counts", "",
    ]
    lines += [f"- `{k}`: {v}" for k, v in agg.classification_counts.items()]
    lines += ["", "### Processor activation frequency (best candidate per valid pair)", ""]
    lines += ([f"- `{k}`: {v}" for k, v in agg.processor_activation_counts.items()]
              or ["- (none)"])
    return "\n".join(lines) + "\n"


def run_oracle(pairs: list[dict], src_folder: Path, out_dir: Path) -> None:
    """DT-55E forced-engagement probe on verified pairs (local-only, diagnostic)."""
    from src.paired_corpus.oracle import _composite, aggregate, probe_pair

    rows: list[dict] = []
    probes = []
    for i, pair in enumerate(pairs):
        pid = f"P-{i+1:02d}"
        try:
            raw_wav = decode(src_folder / pair["raw"]["filename"], pair["raw"]["sha256"])
            wet_wav = decode(src_folder / pair["wet"]["filename"], pair["wet"]["sha256"])
            raw, wet = load(raw_wav), load(wet_wav)
            ev = classify_pair(raw, wet, SR)
            if ev.verdict in ("incorrect_pair", "unusable"):
                rows.append({"pair_id": pid, "verdict": ev.verdict})
                print(f"[{i+1}/{len(pairs)}] {pid}: {ev.verdict} (not probed)", flush=True)
                continue
            amap = align_pair(raw, wet, SR)
            champ, acts = champion_render(raw_wav)
            probe = probe_pair(pid, raw, wet, amap, champ, acts)
            probes.append(probe)
            rows.append({
                "pair_id": pid, "verdict": ev.verdict, "champion_actions": acts,
                "classification": probe.classification,
                "reason": probe.reason,
                "n_measured_phrases": probe.n_measured_phrases,
                "champion_distance": probe.champion_distance,
                "oracle_distance": probe.oracle_distance,
                "improvement_pct": probe.improvement_pct,
                "best_candidate": probe.best_candidate,
                "active_processors": list(probe.active_processors),
                "confidence": probe.confidence,
                "valid": probe.valid,
                "candidates": [{
                    "name": r.name, "safe": r.safe, "peak": r.peak,
                    "n_measured_phrases": r.n_measured_phrases,
                    "composite_distance": _composite(r.axis_distance),
                    "axis_distance": r.axis_distance,
                } for r in probe.results],
            })
            print(f"[{i+1}/{len(pairs)}] {pid}: champ_acts {acts}, "
                  f"{probe.n_measured_phrases} phrases, {probe.improvement_pct:+.1f}% "
                  f"-> {probe.classification}", flush=True)
        except Exception as exc:  # noqa: BLE001
            rows.append({"pair_id": pid, "error": str(exc)})
            print(f"[{i+1}/{len(pairs)}] {pid}: ERROR {exc}", flush=True)

    agg = aggregate(probes)
    payload = {
        "authorization": "D-029 (local/internal/eval-only)",
        "limitation": "Diagnostic only; forced-engagement probe using existing "
                      "processors; NO threshold tuned, NO promotion, NO claim; lossy sources.",
        "aggregation_rule": "inconclusive_alignment pairs are excluded from all aggregates",
        "aggregate": {
            "n_total": agg.n_total, "n_valid": agg.n_valid, "n_excluded": agg.n_excluded,
            "median_improvement_pct": agg.median_improvement_pct,
            "mean_improvement_pct": agg.mean_improvement_pct,
            "ci95_mean_improvement_pct": list(agg.ci95_mean_improvement_pct),
            "abstention_rate": agg.abstention_rate,
            "engagement_rate": agg.engagement_rate,
            "classification_counts": agg.classification_counts,
            "processor_activation_counts": agg.processor_activation_counts,
        },
        "results": rows,
    }
    (out_dir / "oracle_report_anonymized.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8")
    (out_dir / "oracle_report.md").write_text(_oracle_markdown(rows, agg), encoding="utf-8")
    print("classification counts:", json.dumps(agg.classification_counts))
    print(f"valid {agg.n_valid}/{agg.n_total}, median improvement "
          f"{agg.median_improvement_pct:+.2f}%, abstention {agg.abstention_rate:.0%}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--oracle", action="store_true", help="run the DT-55E forced-engagement probe")
    args = ap.parse_args()
    if args.oracle:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        allowed = authorized_files(manifest)
        pairs = build_pairs(manifest, allowed)
        if args.limit:
            pairs = pairs[: args.limit]
        out_dir = REPORTS / time.strftime("%Y%m%d-%H%M%S-oracle")
        out_dir.mkdir(parents=True, exist_ok=True)
        run_oracle(pairs, Path(manifest["source_folder"]), out_dir)
        print(f"wrote {out_dir}")
        return 0

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    src_folder = Path(manifest["source_folder"])
    allowed = authorized_files(manifest)
    pairs = build_pairs(manifest, allowed)
    if args.limit:
        pairs = pairs[: args.limit]
    print(f"authorized files: {len(allowed)}; candidate pairs: {len(pairs)}", flush=True)

    run_id = time.strftime("%Y%m%d-%H%M%S")
    out_dir = REPORTS / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, pair in enumerate(pairs):
        pid = pair["pair_id"]
        t0 = time.time()
        try:
            raw_wav = decode(src_folder / pair["raw"]["filename"], pair["raw"]["sha256"])
            wet_wav = decode(src_folder / pair["wet"]["filename"], pair["wet"]["sha256"])
            raw, wet = load(raw_wav), load(wet_wav)
            ev = classify_pair(raw, wet, SR)
            entry = {
                "pair_id": pid, "verdict": ev.verdict,
                "envelope_corr": ev.envelope_corr, "duration_ratio": ev.duration_ratio,
                "human_confirmation": HUMAN_CONFIRMATION,
            }
            if ev.verdict == "incorrect_pair" or ev.verdict == "unusable":
                results.append(entry)
                print(f"[{i+1}/{len(pairs)}] {pid}: {ev.verdict} (corr {ev.envelope_corr})", flush=True)
                continue
            amap = align_pair(raw, wet, SR)
            prof = profile_pair(pid, raw, wet, SR, amap)
            entry["n_phrases_aligned"] = prof.n_phrases_aligned
            entry["n_phrases_total"] = prof.n_phrases_total
            entry["raw_to_wet"] = prof.summary
            # Champion render + champion->wet remaining gap on aligned phrases.
            champ, n_actions = champion_render(raw_wav)
            entry["champion_actions"] = n_actions
            gaps: dict[str, list[float]] = {k: [] for k in GAP_AXES}
            for p in amap.aligned():
                cseg = champ[int(p.raw_start_s * SR): int(p.raw_end_s * SR)]
                wseg = wet[int(p.wet_start_s * SR): int(p.wet_end_s * SR)]
                if len(cseg) < SR // 10 or len(wseg) < SR // 10:
                    continue
                fc, fw = phrase_features(cseg, SR), phrase_features(wseg, SR)
                for k in GAP_AXES:
                    gaps[k].append(fw[k] - fc[k])
            entry["champion_to_wet_gap_median"] = {
                k: round(float(np.median(v)), 5) for k, v in gaps.items() if v
            }
            entry["gap_noise_floor_champion_db"] = gap_noise_floor_db(champ, SR)
            entry["gap_noise_floor_wet_db"] = gap_noise_floor_db(wet, SR)
            # Per-phrase detail stays LOCAL (restricted), not in the committed report.
            (ANALYSIS / f"{pid.replace(' ', '_')}_phrases.json").write_text(
                json.dumps([d.__dict__ for d in prof.phrase_deltas], indent=1, default=str),
                encoding="utf-8")
            results.append(entry)
            print(f"[{i+1}/{len(pairs)}] {pid}: {ev.verdict}, corr {ev.envelope_corr}, "
                  f"{prof.n_phrases_aligned}/{prof.n_phrases_total} phrases, "
                  f"champ_actions {n_actions} ({time.time()-t0:.0f}s)", flush=True)
        except Exception as exc:  # noqa: BLE001 — one bad pair must not kill the run
            results.append({"pair_id": pid, "error": str(exc)})
            print(f"[{i+1}/{len(pairs)}] {pid}: ERROR {exc}", flush=True)

    payload = {
        "run_id": run_id, "authorization": "D-029 (local/internal/eval-only)",
        "limitation": "Lossy MP3 sources; directional guidance only; NO perceptual claim.",
        "n_pairs": len(pairs), "results": results,
    }
    (out_dir / "gap_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Markdown summary (metrics only).
    lines = [
        f"# Paired-corpus gap report {run_id}", "",
        "Authorization D-029 (local/internal/eval-only). Lossy sources — directional",
        "guidance only. **No perceptual claim.** Deltas are median wet−champion per",
        "aligned phrase (negative band/crest = wet is lower/tighter there).", "",
        "| pair | verdict | corr | phrases | champ acts | d_crest | d_lowmid | d_harsh | d_sib | d_tilt |",
        "|---|---|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for r in results:
        if "error" in r or "champion_to_wet_gap_median" not in r:
            lines.append(f"| {r['pair_id']} | {r.get('verdict', r.get('error','?'))[:28]} | | | | | | | | |")
            continue
        g = r["champion_to_wet_gap_median"]
        lines.append(
            f"| {r['pair_id']} | {r['verdict']} | {r['envelope_corr']:.2f} "
            f"| {r['n_phrases_aligned']}/{r['n_phrases_total']} | {r['champion_actions']} "
            f"| {g.get('crest_db',0):+.2f} | {g.get('lowmid_250_500',0):+.4f} "
            f"| {g.get('harsh_2500_5000',0):+.4f} | {g.get('sib_5500_12000',0):+.4f} "
            f"| {g.get('tilt_db_per_oct',0):+.2f} |")
    (out_dir / "gap_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
