"""Build the DrakoTune evaluation corpus (M22, part 2).

Consumes locally downloaded Tier A datasets (per data/manifests/, after the
human download checkpoints) and produces:

  data/derived/<version>/clean/<clip_id>.wav          normalized clean clips
  data/derived/<version>/degraded/<clip>__<recipe>.wav paired degraded clips
  data/derived/<version>/corpus_manifest.json          full regenerable record
  data/corpus/<version>.json                           committed freeze summary

Selection, conversion, and degradation are deterministic (sorted inputs +
fixed seed), so the derived tree is regenerable and never committed.

    python scripts/build_corpus.py                # default: 2 recipes per clip
    python scripts/build_corpus.py --full-grid    # every recipe on every clip
    python scripts/build_corpus.py --ci-fixtures  # also refresh fixtures/audio_real/

Requires: vocalset + vocadito extracted under data/local/ (manifest local_path
set). This script downloads nothing and accepts no license.
"""

import argparse
import json
import sys
from pathlib import Path

import librosa
import numpy as np
import pyloudnorm
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fixtures.degradations import (  # noqa: E402
    DEGRADATION_LIBRARY_VERSION,
    STANDARD_GRID,
    apply_recipe,
    output_sha256,
)
from src.data_governance import load_manifest  # noqa: E402

CORPUS_BUILDER_VERSION = "1.0.0"
SR = 44100
CLIP_MIN_S = 3.0
CLIP_MAX_S = 20.0
CLEAN_TARGET_LUFS = -23.0
TRUE_PEAK_CEILING = 0.84  # ≈ -1.5 dBFS sample-peak guard after normalization
SELECTION_SEED = 20260710
VOCALSET_CLIPS_PER_SINGER = 2


def _load_normalized(path: Path) -> np.ndarray | None:
    """Load -> mono 44.1k float32, trimmed to CLIP_MAX_S, -23 LUFS, peak-safe."""
    audio, _ = librosa.load(path, sr=SR, mono=True)
    audio = audio.astype(np.float32)
    if len(audio) < SR * CLIP_MIN_S:
        return None
    audio = audio[: int(SR * CLIP_MAX_S)]
    try:
        lufs = pyloudnorm.Meter(SR).integrated_loudness(audio.astype(np.float64))
        if not np.isfinite(lufs) or lufs <= -70.0:
            return None
    except Exception:
        return None
    audio = audio * (10.0 ** ((CLEAN_TARGET_LUFS - lufs) / 20.0))
    peak = float(np.max(np.abs(audio)))
    if peak > TRUE_PEAK_CEILING:
        audio = audio * (TRUE_PEAK_CEILING / peak)
    return audio.astype(np.float32)


def select_vocalset_clips(root: Path, per_singer: int = VOCALSET_CLIPS_PER_SINGER) -> list[dict]:
    """Deterministically pick song *excerpts* per singer (technique-diverse)."""
    rng = np.random.default_rng(SELECTION_SEED)
    selected: list[dict] = []
    singers = sorted(p for p in (root / "FULL").iterdir() if p.is_dir())
    for singer_dir in singers:
        excerpts = sorted(singer_dir.glob("excerpts/*/*.wav"))
        if not excerpts:
            continue
        by_technique: dict[str, list[Path]] = {}
        for wav in excerpts:
            by_technique.setdefault(wav.parent.name, []).append(wav)
        techniques = sorted(by_technique)
        picks = rng.choice(len(techniques), size=min(per_singer, len(techniques)), replace=False)
        for idx in sorted(picks):
            technique = techniques[idx]
            wav = by_technique[technique][0]  # sorted; first file is deterministic
            selected.append({
                "source_dataset": "vocalset",
                "source_file": str(wav.relative_to(root)).replace("\\", "/"),
                "singer": singer_dir.name,
                "technique": technique,
                "clip_id": f"vocalset_{singer_dir.name}_{technique}",
            })
    return selected


def select_vocadito_clips(root: Path) -> list[dict]:
    return [{
        "source_dataset": "vocadito",
        "source_file": str(wav.relative_to(root)).replace("\\", "/"),
        "singer": None,
        "technique": None,
        "clip_id": wav.stem,
    } for wav in sorted((root / "Audio").glob("*.wav"))]


def assign_recipes(clip_ids: list[str], full_grid: bool) -> dict[str, list]:
    """Deterministic recipe assignment: full grid, or 2 per clip round-robin
    so every recipe family/severity gets roughly equal coverage."""
    if full_grid:
        return {cid: list(STANDARD_GRID) for cid in clip_ids}
    assignment: dict[str, list] = {}
    n = len(STANDARD_GRID)
    for i, cid in enumerate(sorted(clip_ids)):
        assignment[cid] = [STANDARD_GRID[(2 * i) % n], STANDARD_GRID[(2 * i + 1) % n]]
    return assignment


def build(version: str, full_grid: bool, ci_fixtures: bool) -> dict:
    repo = Path(__file__).resolve().parent.parent
    sources = {}
    for dataset_id in ("vocalset", "vocadito"):
        manifest = load_manifest(repo / "data" / "manifests" / f"{dataset_id}.json")
        if manifest.local_path is None:
            raise SystemExit(
                f"{dataset_id}: manifest has no local_path — complete the human "
                "download checkpoint first (docs/data/DATASET_GOVERNANCE.md §4)."
            )
        sources[dataset_id] = repo / manifest.local_path

    clips = select_vocalset_clips(sources["vocalset"]) + select_vocadito_clips(sources["vocadito"])

    out_root = repo / "data" / "derived" / version
    clean_dir, degraded_dir = out_root / "clean", out_root / "degraded"
    clean_dir.mkdir(parents=True, exist_ok=True)
    degraded_dir.mkdir(parents=True, exist_ok=True)

    records, skipped = [], []
    for clip in clips:
        src = sources[clip["source_dataset"]] / clip["source_file"]
        audio = _load_normalized(src)
        if audio is None:
            skipped.append({**clip, "reason": "too short or unmeasurable loudness"})
            continue
        clean_path = clean_dir / f"{clip['clip_id']}.wav"
        sf.write(clean_path, audio, SR, subtype="PCM_16")
        records.append({**clip, "duration_s": round(len(audio) / SR, 2),
                        "clean_sha256": output_sha256(audio), "degradations": []})

    assignment = assign_recipes([r["clip_id"] for r in records], full_grid)
    for record in records:
        clean_audio, _ = sf.read(clean_dir / f"{record['clip_id']}.wav", dtype="float32")
        for recipe in assignment[record["clip_id"]]:
            degraded = apply_recipe(clean_audio, SR, recipe)
            peak = float(np.max(np.abs(degraded)))
            if recipe.family != "clipping" and peak > 0.999:  # clipping is the only intentional overload
                degraded = degraded * (0.999 / peak)
            name = f"{record['clip_id']}__{recipe.id}.wav"
            sf.write(degraded_dir / name, degraded, SR, subtype="PCM_16")
            record["degradations"].append({
                "recipe": recipe.to_dict(), "file": f"degraded/{name}",
                "sha256": output_sha256(degraded.astype(np.float32)),
            })

    manifest = {
        "corpus_version": version,
        "builder_version": CORPUS_BUILDER_VERSION,
        "degradation_library_version": DEGRADATION_LIBRARY_VERSION,
        "selection_seed": SELECTION_SEED,
        "clean_target_lufs": CLEAN_TARGET_LUFS,
        "sample_rate": SR,
        "full_grid": full_grid,
        "sources": {k: str(v.relative_to(repo)).replace("\\", "/") for k, v in sources.items()},
        "clips": records,
        "skipped": skipped,
    }
    (out_root / "corpus_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Committed freeze summary: composition + digests, no local paths beyond data/.
    freeze = {
        "corpus_version": version,
        "builder_version": CORPUS_BUILDER_VERSION,
        "degradation_library_version": DEGRADATION_LIBRARY_VERSION,
        "selection_seed": SELECTION_SEED,
        "clip_count": len(records),
        "degraded_pair_count": sum(len(r["degradations"]) for r in records),
        "skipped_count": len(skipped),
        "sources": {k: {"dataset": k, "tier": "A"} for k in sources},
        "clip_digests": {r["clip_id"]: r["clean_sha256"] for r in records},
    }
    corpus_dir = repo / "data" / "corpus"
    corpus_dir.mkdir(exist_ok=True)
    (corpus_dir / f"{version}.json").write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")

    if ci_fixtures:
        _write_ci_fixtures(repo, records, clean_dir)
    return manifest


def _write_ci_fixtures(repo: Path, records: list[dict], clean_dir: Path) -> None:
    """Copy 3 short Tier A clean clips (≤1 MB each) into fixtures/audio_real/."""
    fixture_dir = repo / "fixtures" / "audio_real"
    fixture_dir.mkdir(exist_ok=True)
    vocalset = [r for r in records if r["source_dataset"] == "vocalset"][:2]
    vocadito = [r for r in records if r["source_dataset"] == "vocadito"][:1]
    for record in vocalset + vocadito:
        audio, _ = sf.read(clean_dir / f"{record['clip_id']}.wav", dtype="float32")
        sf.write(fixture_dir / f"{record['clip_id']}.wav", audio[: SR * 10], SR, subtype="PCM_16")
    (fixture_dir / "README.md").write_text(
        "# Real-vocal CI fixtures (Tier A)\n\n"
        "Short clean clips derived from CC BY 4.0 datasets for CI use\n"
        "(governance: docs/data/DATASET_GOVERNANCE.md §5; credits:\n"
        "data/licenses/ATTRIBUTIONS.md — VocalSet, vocadito).\n"
        "Regenerate: python scripts/build_corpus.py --ci-fixtures\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the DrakoTune evaluation corpus")
    parser.add_argument("--version", default="corpus-v1")
    parser.add_argument("--full-grid", action="store_true",
                        help="apply every recipe to every clip (default: 2 per clip)")
    parser.add_argument("--ci-fixtures", action="store_true",
                        help="also refresh fixtures/audio_real/ (3 short Tier A clips)")
    args = parser.parse_args()
    manifest = build(args.version, args.full_grid, args.ci_fixtures)
    print(f"corpus {args.version}: {len(manifest['clips'])} clean clips, "
          f"{sum(len(r['degradations']) for r in manifest['clips'])} degraded pairs, "
          f"{len(manifest['skipped'])} skipped")


if __name__ == "__main__":
    main()
