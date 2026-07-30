"""DT-100 stages 2-3 — scale target and correction curve.

Everything here is authored and bounded; nothing is searched. The tests defend
the decisions that make correction a musical operation rather than a flattening
one: the deadband exists and works, unvoiced frames are never touched, the glide
is real, correction is bounded, and the three presets differ in KIND.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.dsp_engine.correction import (
    MAX_CORRECTION_CENTS,
    NOTES,
    PRESETS,
    SCALES,
    CorrectionSettings,
    correction_cents,
    correction_curve,
    nearest_scale_target,
    scale_degrees,
)
from src.dsp_engine.pitch import estimate_f0
from src.dsp_engine.psola import shift_pitch

SR = 44100
A3 = 220.0


def _tone(f0: float, seconds: float = 1.0, harmonics: int = 4) -> np.ndarray:
    t = np.arange(int(SR * seconds)) / SR
    return sum((0.3 / k) * np.sin(2 * np.pi * f0 * k * t)
               for k in range(1, harmonics + 1)).astype(np.float32)


def _detuned(cents: float, seconds: float = 1.0) -> np.ndarray:
    return _tone(A3 * 2 ** (cents / 1200.0), seconds)


def _measured_cents_from_a3(audio: np.ndarray) -> float:
    track = estimate_f0(audio, SR)
    voiced = track.f0_hz[track.voiced]
    assert voiced.size > 0
    return 1200.0 * float(np.log2(float(np.median(voiced)) / A3))


# ---------------------------------------------------------------------------
# Scale targets
# ---------------------------------------------------------------------------

def test_scale_degrees_are_absolute_semitone_classes():
    assert scale_degrees("C", "major") == (0, 2, 4, 5, 7, 9, 11)
    assert scale_degrees("A", "minor") == tuple(sorted((9 + d) % 12
                                                       for d in SCALES["minor"]))


def test_every_scale_and_key_is_usable():
    for scale in SCALES:
        for key in NOTES:
            degrees = scale_degrees(key, scale)
            assert len(degrees) == len(set(degrees))
            assert all(0 <= d < 12 for d in degrees)


def test_unknown_scale_or_key_is_refused():
    with pytest.raises(ValueError):
        scale_degrees("C", "lydian_dominant_bebop")
    with pytest.raises(ValueError):
        scale_degrees("H", "major")


def test_nearest_target_snaps_up_across_an_octave_boundary():
    """A note just under C must snap UP to C, not down to the B below."""
    c4 = 261.63
    just_under = np.array([c4 * 2 ** (-20 / 1200.0)])
    target = nearest_scale_target(just_under, "C", "major")
    assert abs(float(target[0]) - 60.0) < 0.01       # MIDI 60 = C4


def test_nearest_target_leaves_unvoiced_frames_as_nan():
    target = nearest_scale_target(np.array([np.nan, 220.0, np.nan]), "C", "chromatic")
    assert np.isnan(target[0]) and np.isnan(target[2])
    assert np.isfinite(target[1])


def test_a_note_outside_the_scale_snaps_to_a_scale_degree():
    """C# is not in C major, so it must move to C or D, not stay put."""
    c_sharp = 277.18
    target = nearest_scale_target(np.array([c_sharp]), "C", "major")
    assert float(target[0]) in (60.0, 62.0)


# ---------------------------------------------------------------------------
# The deadband — the thing that separates correcting from flattening
# ---------------------------------------------------------------------------

def test_deviation_inside_the_deadband_is_left_completely_alone():
    track = estimate_f0(_detuned(10.0), SR)
    settings = CorrectionSettings(strength=1.0, deadband_cents=30.0, retune_ms=1.0)
    assert np.allclose(correction_cents(track, settings), 0.0)


def test_only_the_excess_beyond_the_deadband_is_corrected():
    """Correction must be continuous at the boundary, not jump the full width."""
    track = estimate_f0(_detuned(-40.0), SR)
    settings = CorrectionSettings(strength=1.0, deadband_cents=30.0, retune_ms=1.0)
    applied = correction_cents(track, settings)
    active = applied[np.abs(applied) > 0]
    assert active.size > 0
    assert abs(float(np.median(active)) - 10.0) < 4.0     # 40 - 30 = 10 cents


def test_a_zero_deadband_corrects_the_whole_error():
    track = estimate_f0(_detuned(-40.0), SR)
    settings = CorrectionSettings(strength=1.0, deadband_cents=0.0, retune_ms=1.0)
    applied = correction_cents(track, settings)
    assert abs(float(np.median(applied[np.abs(applied) > 0])) - 40.0) < 5.0


def test_vibrato_survives_a_natural_deadband():
    """A corrector without a deadband turns a sung note into a test tone."""
    seconds, depth_cents, rate = 1.0, 45.0, 5.0
    t = np.arange(int(SR * seconds)) / SR
    f_inst = A3 * 2 ** ((depth_cents / 1200.0) * np.sin(2 * np.pi * rate * t))
    audio = (0.3 * np.sin(2 * np.pi * np.cumsum(f_inst) / SR)).astype(np.float32)

    track = estimate_f0(audio, SR)
    natural = correction_cents(track, PRESETS["natural"])
    hard = correction_cents(track, PRESETS["hard"])
    assert float(np.mean(np.abs(natural))) < float(np.mean(np.abs(hard)))


# ---------------------------------------------------------------------------
# Safety of the curve
# ---------------------------------------------------------------------------

def test_unvoiced_frames_are_never_corrected():
    rng = np.random.default_rng(7)
    noise = (0.2 * rng.standard_normal(SR // 2)).astype(np.float32)
    track = estimate_f0(noise, SR)
    applied = correction_cents(track, PRESETS["hard"])
    assert np.all(applied[~track.voiced] == 0.0)


def test_correction_is_bounded_even_against_a_wild_target():
    track = estimate_f0(_detuned(-40.0), SR)
    settings = CorrectionSettings(strength=1.0, deadband_cents=0.0,
                                  max_correction_cents=5.0, retune_ms=1.0)
    assert np.max(np.abs(correction_cents(track, settings))) <= 5.0 + 1e-9


def test_settings_are_clamped_to_their_declared_bounds():
    validated = CorrectionSettings(strength=5.0, retune_ms=10_000.0,
                                   deadband_cents=-3.0,
                                   max_correction_cents=10_000.0).validated()
    assert validated.strength == 1.0
    assert validated.retune_ms <= 500.0
    assert validated.deadband_cents == 0.0
    assert validated.max_correction_cents == MAX_CORRECTION_CENTS


def test_invalid_scale_or_key_is_refused_not_substituted():
    with pytest.raises(ValueError):
        CorrectionSettings(scale="nonsense").validated()
    with pytest.raises(ValueError):
        CorrectionSettings(key="Q").validated()


def test_strength_zero_is_a_true_bypass():
    track = estimate_f0(_detuned(-40.0), SR)
    settings = CorrectionSettings(strength=0.0, deadband_cents=0.0, retune_ms=1.0)
    assert np.allclose(correction_cents(track, settings), 0.0)


# ---------------------------------------------------------------------------
# The curve handed to the resynthesiser
# ---------------------------------------------------------------------------

def test_curve_is_per_sample_and_finite():
    audio = _detuned(-40.0)
    track = estimate_f0(audio, SR)
    curve = correction_curve(track, PRESETS["modern"], audio.size, SR)
    assert curve.size == audio.size
    assert np.all(np.isfinite(curve)) and np.all(curve > 0)


def test_curve_is_unity_when_nothing_needs_correcting():
    audio = _detuned(0.0)
    track = estimate_f0(audio, SR)
    curve = correction_curve(track, PRESETS["natural"], audio.size, SR)
    assert np.allclose(curve, 1.0, atol=0.01)


def test_a_slow_retune_glides_instead_of_stepping():
    audio = _detuned(-60.0)
    track = estimate_f0(audio, SR)
    slow = correction_curve(track, CorrectionSettings(
        strength=1.0, deadband_cents=0.0, retune_ms=300.0), audio.size, SR)
    fast = correction_curve(track, CorrectionSettings(
        strength=1.0, deadband_cents=0.0, retune_ms=1.0), audio.size, SR)
    # The glide has not arrived yet early on; the instant one already has.
    early = SR // 20
    assert abs(slow[early] - 1.0) < abs(fast[early] - 1.0)


def test_empty_request_returns_an_empty_curve():
    track = estimate_f0(_detuned(0.0), SR)
    assert correction_curve(track, PRESETS["natural"], 0, SR).size == 0


# ---------------------------------------------------------------------------
# End to end: contour -> target -> curve -> resynthesis
# ---------------------------------------------------------------------------

def test_hard_correction_lands_on_the_note():
    audio = _detuned(-40.0)
    track = estimate_f0(audio, SR)
    curve = correction_curve(track, PRESETS["hard"], audio.size, SR)
    corrected = shift_pitch(audio, SR, curve)
    assert abs(_measured_cents_from_a3(corrected)) < 10.0


def test_the_three_presets_differ_in_kind_not_only_degree():
    """Natural barely moves a 40-cent error; hard removes it. If these collapse
    to the same behaviour, the presets are decoration."""
    audio = _detuned(-40.0)
    track = estimate_f0(audio, SR)
    results = {}
    for name in ("natural", "modern", "hard"):
        curve = correction_curve(track, PRESETS[name], audio.size, SR)
        results[name] = _measured_cents_from_a3(shift_pitch(audio, SR, curve))

    assert results["natural"] < results["modern"] < results["hard"], results
    assert abs(results["natural"]) > 25.0, "natural corrected far too much"
    assert abs(results["hard"]) < 10.0, "hard failed to reach the note"


def test_presets_are_ordered_by_how_much_they_intervene():
    assert PRESETS["natural"].deadband_cents > PRESETS["modern"].deadband_cents
    assert PRESETS["modern"].deadband_cents > PRESETS["hard"].deadband_cents
    assert PRESETS["natural"].retune_ms > PRESETS["hard"].retune_ms
    assert PRESETS["natural"].strength < PRESETS["hard"].strength
