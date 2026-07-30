"""DT-100 R2 — time-varying pitch shifting, measured against known ground truth.

What is asserted here is what can be measured honestly: that a *requested* pitch
is actually reached (verified with the independent R1 estimator, not by trusting
the transformation), that duration is preserved, that a per-sample curve is
followed, and that formants move less than the resampling primitive.

What is deliberately NOT asserted is audio quality. F-17's -23.7 dB baseline was
a valid self-comparison (one algorithm against itself), but SI-SDR between two
*different* pitch shifters measures disagreement, not defect: PSOLA keeps the
spectral envelope where `PitchShift` moves it, so they must differ. Using it as a
quality score would repeat the N-018 error of trusting a metric before
establishing what it means.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.dsp_engine.pitch import estimate_f0
from src.dsp_engine.psola import (
    MAX_RATIO,
    MIN_RATIO,
    cents_to_ratio,
    pitch_marks,
    shift_pitch,
)

SR = 44100


def _tone(f0: float, seconds: float = 1.0, harmonics: int = 4) -> np.ndarray:
    t = np.arange(int(SR * seconds)) / SR
    return sum((0.3 / k) * np.sin(2 * np.pi * f0 * k * t)
               for k in range(1, harmonics + 1)).astype(np.float32)


def _measured_f0(audio: np.ndarray) -> float:
    track = estimate_f0(audio, SR)
    voiced = track.f0_hz[track.voiced]
    assert voiced.size > 0, "output has no voiced frames"
    return float(np.median(voiced))


def _cents(got: float, want: float) -> float:
    return 1200.0 * np.log2(got / want)


# ---------------------------------------------------------------------------
# Accuracy: does it reach the pitch that was asked for?
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cents", [-900, -400, -100, -25, 0, 25, 100, 400, 900, 1200])
def test_reaches_the_requested_pitch(cents):
    base = 220.0
    out = shift_pitch(_tone(base), SR, cents_to_ratio(float(cents)))
    error = _cents(_measured_f0(out), base * 2 ** (cents / 1200))
    assert abs(error) < 5.0, f"requested {cents:+} cents, missed by {error:+.2f}"


def test_resolves_a_correction_sized_shift():
    """Correction works in cents. A 10-cent request must land near 10 cents."""
    base = 220.0
    out = shift_pitch(_tone(base), SR, cents_to_ratio(10.0))
    assert abs(_cents(_measured_f0(out), base) - 10.0) < 3.0


def test_duration_is_preserved():
    audio = _tone(220.0)
    for cents in (-500.0, 0.0, 700.0):
        assert shift_pitch(audio, SR, cents_to_ratio(cents)).size == audio.size


def test_unity_ratio_leaves_pitch_and_level_alone():
    audio = _tone(196.0)
    out = shift_pitch(audio, SR, 1.0)
    assert abs(_cents(_measured_f0(out), 196.0)) < 3.0
    rms_in = float(np.sqrt(np.mean(np.square(audio, dtype=np.float64))))
    rms_out = float(np.sqrt(np.mean(np.square(out, dtype=np.float64))))
    assert 0.7 < rms_out / rms_in < 1.3


# ---------------------------------------------------------------------------
# The failure modes that were actually hit while building this
# ---------------------------------------------------------------------------

def test_pitch_marks_do_not_alternate_between_polarities():
    """Regression: snapping on |audio| put marks alternately on the positive and
    negative excursion, doubling the effective period and dropping the output an
    exact octave. Mark spacing must be steady, not alternating."""
    marks, _ = pitch_marks(_tone(220.0), SR)
    spacing = np.diff(marks[:20])
    expected = SR / 220.0
    assert np.all(np.abs(spacing - expected) < expected * 0.15), spacing
    # An alternating pattern shows up as a large odd/even difference.
    assert abs(float(np.mean(spacing[::2])) - float(np.mean(spacing[1::2]))) < 5.0


def test_octave_down_is_clamped_rather_than_returning_the_original_pitch():
    """Below ratio 0.5 grains stop overlapping and the output silently returns
    the INPUT pitch. Clamping makes the limit explicit instead of wrong."""
    base = 220.0
    out = shift_pitch(_tone(base), SR, 0.25)      # would be -2400 cents
    measured = _measured_f0(out)
    assert abs(_cents(measured, base)) > 500.0, "clamped shift did nothing at all"
    assert abs(_cents(measured, base * MIN_RATIO)) < 60.0, (
        f"expected the clamped ratio {MIN_RATIO}, measured {measured:.2f} Hz")


def test_ratio_is_clamped_to_the_validated_range():
    assert MIN_RATIO > 0.5, "grains must still overlap at the lowest allowed ratio"
    assert MAX_RATIO >= 2.0


# ---------------------------------------------------------------------------
# Time-varying behaviour — the property that makes this a corrector
# ---------------------------------------------------------------------------

def test_a_per_sample_curve_corrects_only_where_it_is_applied():
    """First half asked to move, second half left alone."""
    base, seconds = 220.0, 1.0
    audio = _tone(base, seconds)
    curve = np.ones(audio.size)
    curve[: audio.size // 2] = cents_to_ratio(200.0)
    out = shift_pitch(audio, SR, curve)

    first = _measured_f0(out[: out.size // 2 - SR // 20])
    second = _measured_f0(out[out.size // 2 + SR // 20:])
    assert abs(_cents(first, base * 2 ** (200 / 1200))) < 20.0
    assert abs(_cents(second, base)) < 20.0


def test_a_drifting_curve_is_followed():
    base = 220.0
    audio = _tone(base, 1.0)
    curve = cents_to_ratio(np.linspace(0.0, 300.0, audio.size))
    out = shift_pitch(audio, SR, curve)
    start = _measured_f0(out[: SR // 4])
    end = _measured_f0(out[-SR // 4:])
    assert _cents(end, start) > 150.0, "the curve was not followed"


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

def test_stereo_is_shifted_per_channel_not_collapsed():
    mono = _tone(220.0, 0.5)
    stereo = np.stack([mono, mono], axis=1)
    out = shift_pitch(stereo, SR, cents_to_ratio(100.0))
    assert out.ndim == 2 and out.shape[1] == 2
    assert out.shape[0] == stereo.shape[0]


def test_empty_and_tiny_inputs_do_not_raise():
    assert shift_pitch(np.zeros(0, dtype=np.float32), SR, 1.0).size == 0
    tiny = np.zeros(16, dtype=np.float32)
    assert shift_pitch(tiny, SR, 1.2).size == tiny.size


def test_silence_stays_silent_and_finite():
    out = shift_pitch(np.zeros(SR // 2, dtype=np.float32), SR, cents_to_ratio(50.0))
    assert np.all(np.isfinite(out))
    assert float(np.max(np.abs(out))) == 0.0


def test_output_is_finite_on_noise():
    rng = np.random.default_rng(3)
    noise = (0.2 * rng.standard_normal(SR // 2)).astype(np.float32)
    out = shift_pitch(noise, SR, cents_to_ratio(-50.0))
    assert np.all(np.isfinite(out)) and out.size == noise.size


def test_is_deterministic():
    audio = _tone(233.08, 0.5)
    a = shift_pitch(audio, SR, cents_to_ratio(40.0))
    b = shift_pitch(audio, SR, cents_to_ratio(40.0))
    assert np.array_equal(a, b)


def test_cents_to_ratio_matches_the_definition():
    assert cents_to_ratio(0.0) == pytest.approx(1.0)
    assert cents_to_ratio(1200.0) == pytest.approx(2.0)
    assert cents_to_ratio(-1200.0) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Formant behaviour — the property that justifies R2 over the primitive
# ---------------------------------------------------------------------------

def _spectral_envelope(x: np.ndarray, quefrency: int = 24) -> np.ndarray:
    """Cepstrally-smoothed log envelope: formant structure without the harmonics.

    Deliberately phase-insensitive. Two pitch shifters that both sound correct
    produce different waveforms, so a phase-sensitive comparison (SI-SDR) says
    nothing useful about which one moved the formants.
    """
    spectrum = np.abs(np.fft.rfft(x * np.hanning(x.size))) + 1e-12
    cepstrum = np.fft.irfft(np.log(spectrum))
    cepstrum[quefrency:-quefrency] = 0.0
    return np.real(np.fft.rfft(cepstrum))[: spectrum.size]


def _envelope_shift_db(before: np.ndarray, after: np.ndarray, sr: int = SR) -> float:
    n = min(before.size, after.size, sr * 2)
    a, b = _spectral_envelope(before[:n]), _spectral_envelope(after[:n])
    freqs = np.fft.rfftfreq(n, 1.0 / sr)[: a.size]
    band = (freqs >= 200.0) & (freqs <= 5000.0)
    delta = 20 * np.log10(np.exp(b[band])) - 20 * np.log10(np.exp(a[band]))
    return float(np.sqrt(np.mean(delta ** 2)))


def test_psola_moves_formants_less_than_the_resampling_primitive():
    """PSOLA re-spaces grains, so the spectral envelope stays put; `PitchShift`
    resamples, so the envelope travels with the pitch (the "chipmunk" character).
    """
    from pedalboard import Pedalboard, PitchShift

    audio = _tone(220.0, 1.0, harmonics=8)
    cents = 700.0
    psola = shift_pitch(audio, SR, cents_to_ratio(cents))
    primitive = np.asarray(
        Pedalboard([PitchShift(semitones=cents / 100.0)])(audio.reshape(1, -1), SR)
    ).reshape(-1)

    moved_psola = _envelope_shift_db(audio, psola)
    moved_primitive = _envelope_shift_db(audio, primitive)
    assert moved_psola < moved_primitive, (
        f"PSOLA moved the envelope {moved_psola:.2f} dB vs "
        f"PitchShift {moved_primitive:.2f} dB")
