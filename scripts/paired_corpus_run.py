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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

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
