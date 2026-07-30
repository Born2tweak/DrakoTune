"""DT-98 pitch-correction spike: measure the DT-100 pipeline before designing it.

DT-100 proposes contour -> key/scale target -> correction curve -> resynthesis ->
formants. Every stage of that has a failure mode that only shows up on real
audio, so this spike *runs* the stages that can be run today and reports numbers
rather than asserting feasibility.

What it measures, on rights-clean Tier A vocal fixtures:

  1. **Contour** - can `librosa.pyin` track a sung line? Voiced fraction, median
     confidence, octave-jump rate, and cost per second of audio (N-012 flagged
     memory/time scaling as a real constraint, so a stage that costs 5x realtime
     is a design input, not a detail).
  2. **Target** - how far is the tracked contour from equal-tempered pitch
     already? That distribution decides whether correction has anything to do and
     how hard a "hard tune" setting would have to pull.
  3. **Resynthesis** - the honest blocker. `PitchShift` applies ONE fixed
     interval to a whole buffer. Correction needs a *time-varying* shift. This
     measures what a naive frame-wise implementation costs in artifacts, which is
     the number that justifies (or refuses) building a real PSOLA/phase-vocoder
     stage.

No perceptual claim. This is a feasibility probe whose output is a design input.

    python scripts/v3_pitch_spike.py [--outdir DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dsp_engine.channels import normalize, to_mono  # noqa: E402
from src.evaluation.reference_metrics import si_sdr  # noqa: E402

FIXTURES = (
    "fixtures/audio_real/vocalset_female1_straight.wav",
    "fixtures/audio_real/vocalset_female1_vibrato.wav",
    "fixtures/audio_real/vocadito_1.wav",
)
FMIN, FMAX = 65.0, 1000.0        # E2..~C6 covers sung rap and melodic vocals
OCTAVE_JUMP_CENTS = 700.0        # a jump beyond a fifth between frames is tracking failure


def _cents_from_equal_temperament(f0: np.ndarray) -> np.ndarray:
    """Signed cents from each frame's nearest equal-tempered semitone (A440)."""
    voiced = f0[np.isfinite(f0) & (f0 > 0)]
    if voiced.size == 0:
        return np.zeros(0)
    midi = 69.0 + 12.0 * np.log2(voiced / 440.0)
    return (midi - np.round(midi)) * 100.0


def probe_contour(path: str) -> dict:
    import librosa

    audio, sr = sf.read(path, dtype="float32")
    mono = to_mono(normalize(audio))[:, 0]
    duration = len(mono) / sr

    t0 = time.perf_counter()
    f0, voiced_flag, voiced_prob = librosa.pyin(
        mono.astype(np.float64), fmin=FMIN, fmax=FMAX, sr=sr)
    elapsed = time.perf_counter() - t0

    voiced = np.isfinite(f0) & (f0 > 0)
    n_voiced = int(np.sum(voiced))
    cents = _cents_from_equal_temperament(f0)

    # Octave/tracking errors: frame-to-frame jumps within a voiced run.
    jumps = 0
    idx = np.flatnonzero(voiced)
    if idx.size > 1:
        consecutive = idx[1:][np.diff(idx) == 1]
        prev = consecutive - 1
        delta = np.abs(1200.0 * np.log2(f0[consecutive] / f0[prev]))
        jumps = int(np.sum(delta > OCTAVE_JUMP_CENTS))

    return {
        "file": Path(path).name,
        "duration_s": round(duration, 2),
        "pyin_seconds": round(elapsed, 2),
        "realtime_factor": round(elapsed / duration, 2),
        "frames": int(f0.size),
        "voiced_fraction": round(n_voiced / max(f0.size, 1), 4),
        "median_voiced_prob": round(float(np.median(voiced_prob[voiced])), 4)
        if n_voiced else 0.0,
        "octave_jumps": jumps,
        "octave_jump_rate": round(jumps / max(n_voiced, 1), 5),
        "cents_from_et": {
            "median_abs": round(float(np.median(np.abs(cents))), 1) if cents.size else 0.0,
            "p90_abs": round(float(np.percentile(np.abs(cents), 90)), 1) if cents.size else 0.0,
            "max_abs": round(float(np.max(np.abs(cents))), 1) if cents.size else 0.0,
        },
    }


def probe_naive_resynthesis(path: str, shift_cents: float = 30.0) -> dict:
    """Cost of a time-varying shift built from the fixed-interval primitive.

    A correction curve is per-frame. `PitchShift` is per-buffer. The only way to
    approximate one with the other is to slice, shift each slice, and concatenate
    — which is exactly the naive approach a DT-100 design must beat. Measuring
    its artifacts is what makes "build a real resynthesis stage" an evidence-based
    decision rather than an assumption.
    """
    from pedalboard import Pedalboard, PitchShift

    audio, sr = sf.read(path, dtype="float32")
    mono = to_mono(normalize(audio))[:, 0]

    hop = int(0.046 * sr)          # ~46 ms, a typical correction frame
    pieces = []
    t0 = time.perf_counter()
    for start in range(0, len(mono), hop):
        block = mono[start:start + hop]
        if block.size == 0:
            continue
        board = Pedalboard([PitchShift(semitones=shift_cents / 100.0)])
        pieces.append(np.asarray(board(block.reshape(1, -1), sr)).reshape(-1))
    elapsed = time.perf_counter() - t0
    out = np.concatenate(pieces) if pieces else np.zeros(0, dtype=np.float32)

    n = min(len(out), len(mono))
    # A uniform shift of the same size, done in ONE call, is the artifact-free
    # reference: same pitch change, no block boundaries.
    board = Pedalboard([PitchShift(semitones=shift_cents / 100.0)])
    whole = np.asarray(board(mono.reshape(1, -1), sr)).reshape(-1)
    m = min(n, len(whole))

    return {
        "file": Path(path).name,
        "block_ms": round(hop / sr * 1000.0, 1),
        "blocks": len(pieces),
        "seconds": round(elapsed, 2),
        "realtime_factor": round(elapsed / (len(mono) / sr), 2),
        # Against the single-call shift: how much damage the block boundaries do.
        "si_sdr_vs_uniform_shift_db": round(float(si_sdr(whole[:m], out[:m])), 2),
        "length_error_samples": int(len(out) - len(mono)),
    }


def probe_resolution_cost(path: str, seconds: float = 2.0,
                          resolutions: tuple[float, ...] = (0.1, 0.05, 0.02),
                          ) -> list[dict]:
    """How fine can the contour get, and what does each step cost?

    This is the stage that decides whether DT-100 is buildable on `pyin` at all.
    Correction has to resolve a few cents; `pyin` searches a quantized candidate
    grid, so precision is bought directly with time and memory. `resolution=0.01`
    (1 cent) is deliberately NOT in the default list — it raised `MemoryError` on
    a 2-second excerpt on the development machine, which is the finding.
    """
    import librosa

    audio, sr = sf.read(path, dtype="float32")
    mono = to_mono(normalize(audio))[:, 0].astype(np.float64)[: int(sr * seconds)]
    duration = len(mono) / sr
    rows: list[dict] = []
    for res in resolutions:
        row: dict = {"resolution": res, "excerpt_s": round(duration, 2)}
        try:
            t0 = time.perf_counter()
            f0, _, _ = librosa.pyin(mono, fmin=FMIN, fmax=FMAX, sr=sr, resolution=res)
            elapsed = time.perf_counter() - t0
            voiced = f0[np.isfinite(f0) & (f0 > 0)]
            unique = np.unique(voiced)
            grid = (float(np.median(np.log2(unique[1:] / unique[:-1]) * 1200.0))
                    if unique.size > 1 else 0.0)
            cents = _cents_from_equal_temperament(f0)
            row |= {
                "ok": True,
                "grid_cents": round(grid, 2),
                "median_abs_cents": round(float(np.median(np.abs(cents))), 2),
                "realtime_factor": round(elapsed / duration, 2),
            }
        except MemoryError as exc:                     # the finding, not a crash
            row |= {"ok": False, "error": f"MemoryError: {exc}"}
        rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="output/v3_renders/dt98")
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    missing = [f for f in FIXTURES if not Path(f).exists()]
    if missing:
        print(f"missing fixtures: {missing}", file=sys.stderr)
        return 2

    print("DT-98 pitch spike — contour tracking")
    contours = []
    for path in FIXTURES:
        row = probe_contour(path)
        contours.append(row)
        print(f"  {row['file']:34s} voiced={row['voiced_fraction']:.0%}  "
              f"conf={row['median_voiced_prob']:.2f}  jumps={row['octave_jumps']:3d}  "
              f"|cents|med={row['cents_from_et']['median_abs']:5.1f}  "
              f"p90={row['cents_from_et']['p90_abs']:5.1f}  "
              f"{row['realtime_factor']:.2f}x realtime")

    print("\nNaive time-varying resynthesis from the fixed-interval primitive")
    resynth = []
    for path in FIXTURES:
        row = probe_naive_resynthesis(path)
        resynth.append(row)
        print(f"  {row['file']:34s} {row['blocks']:4d} blocks  "
              f"SI-SDR vs uniform shift = {row['si_sdr_vs_uniform_shift_db']:7.2f} dB  "
              f"{row['realtime_factor']:.2f}x realtime")

    print("\nContour resolution vs cost (the stage that decides DT-100's estimator)")
    resolution = probe_resolution_cost(FIXTURES[0])
    for row in resolution:
        if row["ok"]:
            print(f"  resolution={row['resolution']:<5} grid={row['grid_cents']:6.2f}c  "
                  f"median|cents|={row['median_abs_cents']:5.2f}  "
                  f"{row['realtime_factor']:6.2f}x realtime")
        else:
            print(f"  resolution={row['resolution']:<5} {row['error']}")

    report = {
        "milestone": "DT-98",
        "purpose": "feasibility probe for DT-100; design input, not a claim",
        "pyin": {"fmin": FMIN, "fmax": FMAX},
        "contour": contours,
        "resolution_cost": resolution,
        "naive_resynthesis": resynth,
    }
    (outdir / "pitch_spike.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {outdir / 'pitch_spike.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
