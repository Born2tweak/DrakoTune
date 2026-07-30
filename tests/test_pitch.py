"""DT-100 R1 — continuous-valued f0 estimation, against exact ground truth.

The claim this file has to defend is narrow and specific: the estimator resolves
pitch **continuously**, so it can measure the few-cent errors a corrector must
act on. F-17 recorded why that is not free — `librosa.pyin` returns f0 on a
10-cent grid at its default, and buying a finer grid costs ~20x realtime at
2 cents and runs out of memory at 1 cent.

Synthetic signals are used deliberately: their true f0 is known exactly, so
accuracy is measured rather than eyeballed.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.dsp_engine.pitch import (
    DEFAULT_THRESHOLD,
    F0Track,
    _parabolic_refine,
    estimate_f0,
)

SR = 44100


def _tone(f0: float, seconds: float = 0.5, sr: int = SR, harmonics: int = 4,
          amp: float = 0.3) -> np.ndarray:
    """A harmonic tone at exactly `f0` Hz — voice-like, with known ground truth."""
    t = np.arange(int(sr * seconds)) / sr
    sig = sum((amp / k) * np.sin(2 * np.pi * f0 * k * t) for k in range(1, harmonics + 1))
    return sig.astype(np.float32)


def _cents(estimate: float, truth: float) -> float:
    return 1200.0 * np.log2(estimate / truth)


def _median_f0(audio, **kw) -> float:
    track = estimate_f0(audio, SR, **kw)
    voiced = track.f0_hz[track.voiced]
    assert voiced.size > 0, "no voiced frames detected"
    return float(np.median(voiced))


# ---------------------------------------------------------------------------
# Accuracy against known f0
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("truth", [82.41, 110.0, 220.0, 329.63, 440.0, 880.0])
def test_estimates_known_pitches_within_a_few_cents(truth):
    error = _cents(_median_f0(_tone(truth)), truth)
    assert abs(error) < 5.0, f"{truth} Hz estimated {error:+.2f} cents off"


def test_resolves_differences_a_grid_estimator_would_quantize_away():
    """The property R1 exists for: 3-cent inputs must give 3-cent-apart outputs.

    A 10-cent candidate grid collapses these to the same value, which is what
    makes it unusable for correction (F-17).
    """
    base = 220.0
    three_cents_up = base * 2 ** (3 / 1200)
    a, b = _median_f0(_tone(base)), _median_f0(_tone(three_cents_up))
    separation = _cents(b, a)
    assert 1.5 < separation < 4.5, f"3-cent input separated by only {separation:.2f} cents"


def test_output_is_not_confined_to_a_lattice():
    """F-17's artifact: quantized estimates put every reading on a fixed lattice.

    Deviations from equal temperament across a spread of inputs must NOT collapse
    onto a small set of values.
    """
    truths = [220.0 * 2 ** (c / 1200) for c in (0, 2, 4, 7, 11, 17, 23, 31)]
    deviations = []
    for truth in truths:
        midi = 69.0 + 12.0 * np.log2(_median_f0(_tone(truth)) / 440.0)
        deviations.append(round((midi - round(midi)) * 100.0, 3))
    assert len(set(deviations)) >= len(truths) - 1, (
        f"estimates collapsed onto a lattice: {sorted(deviations)}")


def test_tracks_vibrato_rather_than_averaging_it_away():
    sr, seconds, centre, depth_cents, rate = SR, 1.0, 220.0, 60.0, 5.0
    t = np.arange(int(sr * seconds)) / sr
    f_inst = centre * 2 ** ((depth_cents / 1200.0) * np.sin(2 * np.pi * rate * t))
    phase = 2 * np.pi * np.cumsum(f_inst) / sr
    audio = (0.3 * np.sin(phase)).astype(np.float32)

    track = estimate_f0(audio, sr)
    voiced = track.f0_hz[track.voiced]
    assert voiced.size > 10
    spread = 1200.0 * np.log2(np.max(voiced) / np.min(voiced))
    # A tracker that smoothed vibrato away would report a near-flat contour.
    assert spread > 60.0, f"vibrato spread only {spread:.1f} cents"


# ---------------------------------------------------------------------------
# Voicing
# ---------------------------------------------------------------------------

def test_silence_is_unvoiced():
    track = estimate_f0(np.zeros(SR // 2, dtype=np.float32), SR)
    assert track.voiced_fraction == 0.0


def test_white_noise_is_mostly_unvoiced():
    rng = np.random.default_rng(11)
    noise = (0.2 * rng.standard_normal(SR // 2)).astype(np.float32)
    assert estimate_f0(noise, SR).voiced_fraction < 0.25


def test_tone_is_voiced_and_periodic():
    track = estimate_f0(_tone(220.0), SR)
    assert track.voiced_fraction > 0.8
    assert float(np.median(track.periodicity[track.voiced])) > 0.7


# ---------------------------------------------------------------------------
# Robustness and contract
# ---------------------------------------------------------------------------

def test_octave_errors_are_not_produced_on_a_rich_harmonic_tone():
    """The classic YIN failure is reporting f0/2. A rich tone is where it bites."""
    truth = 130.81
    track = estimate_f0(_tone(truth, seconds=0.8, harmonics=8), SR)
    voiced = track.f0_hz[track.voiced]
    halved = np.sum(np.abs(1200.0 * np.log2(voiced / (truth / 2))) < 50.0)
    assert halved / voiced.size < 0.05, f"{halved}/{voiced.size} frames an octave low"


def test_estimate_is_robust_to_moderate_noise():
    rng = np.random.default_rng(5)
    truth = 220.0
    clean = _tone(truth, seconds=0.8)
    noisy = (clean + 0.03 * rng.standard_normal(clean.size)).astype(np.float32)
    assert abs(_cents(_median_f0(noisy), truth)) < 10.0


def test_amplitude_invariance():
    truth = 196.0
    loud = _median_f0(_tone(truth, amp=0.6))
    quiet = _median_f0(_tone(truth, amp=0.02))
    assert abs(_cents(loud, quiet)) < 2.0


def test_stereo_input_is_summed_not_rejected():
    mono = _tone(220.0)
    stereo = np.stack([mono, mono], axis=1)
    assert abs(_cents(_median_f0(stereo), _median_f0(mono))) < 1.0


def test_is_deterministic():
    audio = _tone(233.08)
    a, b = estimate_f0(audio, SR), estimate_f0(audio, SR)
    assert np.array_equal(np.nan_to_num(a.f0_hz, nan=-1.0),
                          np.nan_to_num(b.f0_hz, nan=-1.0))


def test_rejects_an_impossible_range():
    with pytest.raises(ValueError):
        estimate_f0(_tone(220.0), SR, fmin=500.0, fmax=100.0)


def test_rejects_a_frame_too_short_for_fmin():
    with pytest.raises(ValueError):
        estimate_f0(_tone(220.0), SR, fmin=65.0, frame_ms=5.0)


def test_estimates_outside_the_requested_range_are_discarded():
    track = estimate_f0(_tone(220.0), SR, fmin=400.0, fmax=900.0)
    voiced = track.f0_hz[track.voiced]
    assert np.all((voiced >= 400.0) & (voiced <= 900.0))


def test_parabolic_refinement_moves_off_the_integer_lag():
    values = np.array([1.0, 0.5, 0.9])       # minimum sits left of index 1
    refined = _parabolic_refine(values, 1)
    assert refined != 1.0 and 0.5 < refined < 1.5


def test_parabolic_refinement_is_safe_at_the_edges():
    values = np.array([1.0, 0.5, 0.9])
    assert _parabolic_refine(values, 0) == 0.0
    assert _parabolic_refine(values, 2) == 2.0


def test_track_reports_its_own_shape_honestly():
    track = estimate_f0(_tone(220.0), SR)
    info = track.to_dict()
    assert info["frames"] == track.f0_hz.size == track.times_s.size
    assert 0.0 <= info["voiced_fraction"] <= 1.0
    assert abs(_cents(info["median_f0_hz"], 220.0)) < 5.0


def test_cents_from_reference_is_signed_and_zero_at_the_reference():
    track = estimate_f0(_tone(220.0), SR)
    assert abs(float(np.median(track.cents_from(220.0)))) < 5.0
    assert float(np.median(track.cents_from(110.0))) > 1100.0


def test_empty_track_helpers_do_not_raise():
    empty = F0Track(np.zeros(0), np.zeros(0), np.zeros(0), SR, 46.0, 10.0)
    assert empty.voiced_fraction == 0.0
    assert empty.cents_from(440.0).size == 0
    assert empty.to_dict()["median_f0_hz"] is None


def test_threshold_default_is_the_documented_yin_value():
    assert DEFAULT_THRESHOLD == 0.15
