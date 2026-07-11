"""Prepare a blinded, loudness-matched listening session (M24).

Builds a session directory from a corpus: randomized A/B pairs (degraded vs
processed), identical catch trials, clean-input do-no-harm pairs, blind file
names, and a session config that maps blind ids back to truth (kept separate
from the listener response sheet). Design: ADR 0004 + validation plan §5.

    python scripts/listening_prepare.py --pairs 40 --listeners-file responses_template.csv

Output layout (data/derived/listening/<session_id>/):
  stimuli/<trial>_<A|B>.wav      blinded, loudness-matched 16-bit WAVs
  session_key.json               truth mapping — DO NOT give to listeners
  responses_template.csv         one row per trial for each listener to fill
  INSTRUCTIONS.md                listener instructions + artifact checklist
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.evaluation.ab_export import LoudnessMatchError, loudness_matched_pair  # noqa: E402
from src.orchestration import analyze_and_plan  # noqa: E402
from src.dsp_engine import execute_plan  # noqa: E402

SESSION_VERSION = "1.0.0"
SR = 44100
CATCH_FRACTION = 0.10          # identical A/B pairs (attention screening)
CLEAN_FRACTION = 0.10          # clean-input do-no-harm pairs

ARTIFACT_CHECKLIST = [
    "pumping", "gated_breath_or_word_cut", "lisp_or_dulled_s", "hollow_comb_tone",
    "added_noise", "distortion", "lost_presence_or_air", "robotic_unnatural", "other",
]


def _process_v2(path: Path) -> np.ndarray:
    bundle = analyze_and_plan(str(path))
    audio, _ = sf.read(path, dtype="float32")
    processed, _ = execute_plan(audio, SR, bundle.plan)
    return (processed[:, 0] if processed.ndim == 2 else processed).astype(np.float32)


def build_session(corpus_version: str, n_pairs: int, seed: int) -> Path:
    rng = np.random.default_rng(seed)
    corpus_root = REPO / "data" / "derived" / corpus_version
    manifest = json.loads((corpus_root / "corpus_manifest.json").read_text(encoding="utf-8"))

    degraded = [(clip, deg) for clip in manifest["clips"] for deg in clip["degradations"]]
    order = rng.permutation(len(degraded))

    session_id = time.strftime("%Y%m%d-%H%M%S") + f"-s{seed}"
    root = REPO / "data" / "derived" / "listening" / session_id
    stim = root / "stimuli"
    stim.mkdir(parents=True)

    trials: list[dict] = []
    trial_no = 0

    def add_trial(a: np.ndarray, b: np.ndarray, truth: dict) -> None:
        nonlocal trial_no
        trial_no += 1
        tid = f"t{trial_no:03d}"
        try:
            pair = loudness_matched_pair(a, b, SR)
        except LoudnessMatchError as exc:
            trials.append({"trial": tid, "skipped": str(exc), **truth})
            return
        # Randomize which side is which — the blind.
        swap = bool(rng.integers(0, 2))
        first, second = (pair.b, pair.a) if swap else (pair.a, pair.b)
        sf.write(stim / f"{tid}_A.wav", first, SR, subtype="PCM_16")
        sf.write(stim / f"{tid}_B.wav", second, SR, subtype="PCM_16")
        trials.append({"trial": tid, "processed_is": ("A" if (truth["kind"] != "catch") and swap else
                                                      "B" if truth["kind"] != "catch" else "neither"),
                       "loudness": pair.to_dict(), **truth})

    # Main defect trials: degraded (unprocessed) vs v2-processed.
    n_main = min(n_pairs, len(degraded))
    for idx in order[:n_main]:
        clip, deg = degraded[idx]
        degraded_audio, _ = sf.read(corpus_root / deg["file"], dtype="float32")
        processed = _process_v2(corpus_root / deg["file"])
        add_trial(degraded_audio, processed, {
            "kind": "defect", "clip_id": clip["clip_id"],
            "family": deg["recipe"]["family"], "severity": deg["recipe"]["severity"],
        })

    # Clean do-no-harm trials: clean vs v2(clean).
    clean_clips = rng.choice(manifest["clips"], size=max(2, int(n_main * CLEAN_FRACTION)), replace=False)
    for clip in clean_clips:
        clean_path = corpus_root / "clean" / f"{clip['clip_id']}.wav"
        clean_audio, _ = sf.read(clean_path, dtype="float32")
        add_trial(clean_audio, _process_v2(clean_path), {
            "kind": "clean", "clip_id": clip["clip_id"], "family": "none", "severity": "clean",
        })

    # Catch trials: identical A/B (expect "no difference").
    catch_clips = rng.choice(manifest["clips"], size=max(2, int(n_main * CATCH_FRACTION)), replace=False)
    for clip in catch_clips:
        audio, _ = sf.read(corpus_root / "clean" / f"{clip['clip_id']}.wav", dtype="float32")
        add_trial(audio, audio.copy(), {
            "kind": "catch", "clip_id": clip["clip_id"], "family": "none", "severity": "identical",
        })

    # Shuffle trial presentation order in the response sheet.
    live = [t for t in trials if "skipped" not in t]
    sheet_order = rng.permutation(len(live))

    (root / "session_key.json").write_text(json.dumps({
        "session_version": SESSION_VERSION, "session_id": session_id, "seed": seed,
        "corpus_version": corpus_version, "engine": "v2",
        "trials": trials,
    }, indent=2), encoding="utf-8")

    with open(root / "responses_template.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["listener_id", "listener_type", "trial", "preference(A/B/none)",
                         "strength(1-5)"] + [f"artifact_{a}" for a in ARTIFACT_CHECKLIST] + ["notes"])
        for i in sheet_order:
            writer.writerow(["", "", live[i]["trial"]] + [""] * (2 + len(ARTIFACT_CHECKLIST) + 1))

    (root / "INSTRUCTIONS.md").write_text(
        "# DrakoTune listening session — listener instructions\n\n"
        "For each trial, listen to `<trial>_A.wav` and `<trial>_B.wav` (headphones,\n"
        "comfortable fixed volume; do not adjust volume between A and B).\n\n"
        "1. Preference: which version sounds better overall? Answer A, B, or none.\n"
        "2. Strength: 1 (barely) to 5 (much better). Leave blank if none.\n"
        "3. Artifacts: mark 1 in a column if you hear that problem in the version\n"
        "   you did NOT prefer being introduced by the other (or in either, if none).\n"
        "4. Notes: anything else.\n\n"
        "Some pairs are identical on purpose; answer honestly — 'none' is a valid\n"
        "and expected answer. You are not told which file is processed.\n",
        encoding="utf-8",
    )
    print(f"session {session_id}: {len(live)} live trials "
          f"({sum(1 for t in live if t['kind'] == 'defect')} defect, "
          f"{sum(1 for t in live if t['kind'] == 'clean')} clean, "
          f"{sum(1 for t in live if t['kind'] == 'catch')} catch), "
          f"{len(trials) - len(live)} skipped")
    print(f"-> {root}")
    return root


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a blinded listening session")
    parser.add_argument("--corpus", default="corpus-v1")
    parser.add_argument("--pairs", type=int, default=40, help="defect trials")
    parser.add_argument("--seed", type=int, default=20260711)
    args = parser.parse_args()
    build_session(args.corpus, args.pairs, args.seed)


if __name__ == "__main__":
    main()
