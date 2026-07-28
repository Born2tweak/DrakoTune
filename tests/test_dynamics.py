"""DT-96 processor tests.

Each processor is asserted on the property it exists for, not merely on "output
changed". A processor that changes the signal in the wrong direction would pass
a change test and fail the user.
"""

import numpy as np
import pytest

from src.dsp_engine.dynamics import (
    dynamic_eq,
    saturate,
    suppress_resonances,
    vocal_rider,
)

SR = 44100


def _rms(a):
    return float(np.sqrt(np.mean(np.square(a, dtype=np.float64)))) if a.size else 0.0


def _tone(freq, seconds, amp=0.4, sr=SR):
    t = np.arange(int(sr * seconds), dtype=np.float32) / sr
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def _uneven_phrases():
    """Loud phrase, quiet phrase, silence — what a rider must even out."""
    return np.concatenate([
        _tone(200, 0.6, 0.5),
        np.zeros(int(SR * 0.2), dtype=np.float32),
        _tone(200, 0.6, 0.06),   # much quieter phrase
        np.zeros(int(SR * 0.2), dtype=np.float32),
    ])


class TestVocalRider:
    def test_reduces_level_spread_between_phrases(self):
        audio = _uneven_phrases()
        out = vocal_rider(audio, SR, max_boost_db=12.0, max_cut_db=12.0)
        loud_in, quiet_in = _rms(audio[: int(SR * 0.6)]), _rms(audio[int(SR * 0.8): int(SR * 1.4)])
        loud_out, quiet_out = _rms(out[: int(SR * 0.6)]), _rms(out[int(SR * 0.8): int(SR * 1.4)])
        assert loud_in / quiet_in > 4.0, "fixture is not actually uneven"
        assert loud_out / quiet_out < loud_in / quiet_in, "rider did not reduce the spread"

    def test_does_not_amplify_silence(self):
        """Riding silence upward would turn a noise floor into audible hiss."""
        rng = np.random.default_rng(4)
        quiet_noise = rng.normal(0, 0.0005, int(SR * 0.5)).astype(np.float32)
        audio = np.concatenate([_tone(200, 0.5, 0.5), quiet_noise])
        out = vocal_rider(audio, SR, max_boost_db=12.0)
        assert _rms(out[int(SR * 0.5):]) <= _rms(quiet_noise) * 1.5

    def test_respects_boost_and_cut_limits(self):
        audio = _uneven_phrases()
        out = vocal_rider(audio, SR, max_boost_db=3.0, max_cut_db=3.0)
        ratio = _rms(out) / max(_rms(audio), 1e-12)
        assert 10 ** (-6 / 20) < ratio < 10 ** (6 / 20)

    def test_gain_envelope_is_smooth(self):
        """A stepped rider gain is heard as distortion, not level movement."""
        audio = _uneven_phrases()
        out = vocal_rider(audio, SR)
        nz = np.abs(audio) > 1e-6
        implied = np.zeros_like(audio)
        implied[nz] = out[nz] / audio[nz]
        assert float(np.max(np.abs(np.diff(implied[nz])))) < 0.5

    def test_empty_and_silent_inputs(self):
        assert vocal_rider(np.zeros(0, dtype=np.float32), SR).size == 0
        silent = np.zeros(SR // 2, dtype=np.float32)
        assert np.allclose(vocal_rider(silent, SR), silent)


class TestDynamicEQ:
    def test_reduces_a_band_that_is_excessive(self):
        """A tone sitting in the band should come down relative to one outside it."""
        audio = (_tone(300, 1.0, 0.5) + _tone(3000, 1.0, 0.1)).astype(np.float32)
        out = dynamic_eq(audio, SR, band_lo_hz=200.0, band_hi_hz=500.0,
                         threshold_ratio=1.0, max_reduction_db=12.0)
        assert _rms(out) < _rms(audio)

    def test_leaves_content_outside_the_band(self):
        audio = _tone(8000, 1.0, 0.4)
        out = dynamic_eq(audio, SR, band_lo_hz=200.0, band_hi_hz=500.0,
                         threshold_ratio=1.0, max_reduction_db=12.0)
        assert _rms(out) == pytest.approx(_rms(audio), rel=0.1)

    def test_respects_max_reduction(self):
        audio = _tone(300, 1.0, 0.5)
        out = dynamic_eq(audio, SR, band_lo_hz=200.0, band_hi_hz=500.0,
                         threshold_ratio=1.0, max_reduction_db=3.0)
        assert _rms(out) > _rms(audio) * 10 ** (-6 / 20)

    def test_preserves_length(self):
        audio = _tone(300, 0.75, 0.4)
        assert dynamic_eq(audio, SR).shape[0] == audio.shape[0]


class TestResonanceSuppressor:
    def test_reduces_a_planted_resonance(self):
        """Broadband bed plus one strong persistent narrow peak."""
        rng = np.random.default_rng(9)
        bed = rng.normal(0, 0.05, int(SR * 1.5)).astype(np.float32)
        audio = (bed + _tone(1200, 1.5, 0.35)).astype(np.float32)
        out = suppress_resonances(audio, SR, max_reduction_db=12.0, prominence_ratio=1.5)

        def band_energy(x, lo, hi):
            spec = np.abs(np.fft.rfft(x))
            freqs = np.fft.rfftfreq(len(x), 1 / SR)
            return float(np.sum(spec[(freqs >= lo) & (freqs <= hi)] ** 2))

        assert band_energy(out, 1150, 1250) < band_energy(audio, 1150, 1250)

    def test_leaves_flat_material_alone(self):
        """No resonance present means nothing should be attacked."""
        rng = np.random.default_rng(2)
        noise = rng.normal(0, 0.1, int(SR)).astype(np.float32)
        out = suppress_resonances(noise, SR, prominence_ratio=3.0)
        assert _rms(out) == pytest.approx(_rms(noise), rel=0.15)

    def test_preserves_length(self):
        audio = _tone(1000, 0.8, 0.4)
        assert suppress_resonances(audio, SR).shape[0] == audio.shape[0]


class TestSaturation:
    def test_adds_harmonic_content(self):
        audio = _tone(500, 1.0, 0.5)
        out = saturate(audio, SR, drive_db=12.0, mix=1.0)
        spec = np.abs(np.fft.rfft(out))
        freqs = np.fft.rfftfreq(len(out), 1 / SR)

        def at(f):
            return float(np.max(spec[(freqs > f - 30) & (freqs < f + 30)]))

        base_spec = np.abs(np.fft.rfft(audio))
        base_h3 = float(np.max(base_spec[(freqs > 1470) & (freqs < 1530)]))
        assert at(1500) > base_h3 * 5

    def test_mix_zero_is_identity(self):
        audio = _tone(500, 0.5, 0.4)
        assert np.allclose(saturate(audio, SR, drive_db=12.0, mix=0.0), audio, atol=1e-6)

    def test_level_matched_so_mix_changes_character_not_loudness(self):
        audio = _tone(500, 0.5, 0.4)
        dry, wet = _rms(audio), _rms(saturate(audio, SR, drive_db=12.0, mix=1.0))
        assert wet == pytest.approx(dry, rel=0.15)

    def test_oversampling_reduces_aliasing(self):
        """The point of oversampling: harmonics stay above, not folded below.

        A high tone driven hard aliases energy down to low frequencies at 1x. At 4x that
        inharmonic energy below the fundamental should be measurably lower.
        """
        audio = _tone(9000, 0.5, 0.6)
        naive = saturate(audio, SR, drive_db=18.0, mix=1.0, oversample=1)
        over = saturate(audio, SR, drive_db=18.0, mix=1.0, oversample=4)

        def below_fundamental(x):
            spec = np.abs(np.fft.rfft(x))
            freqs = np.fft.rfftfreq(len(x), 1 / SR)
            return float(np.sum(spec[freqs < 8000] ** 2))

        assert below_fundamental(over) < below_fundamental(naive)

    def test_does_not_exceed_unity_wildly(self):
        audio = _tone(500, 0.5, 0.9)
        out = saturate(audio, SR, drive_db=18.0, mix=1.0)
        assert float(np.max(np.abs(out))) < 2.0
        assert np.all(np.isfinite(out))

    def test_preserves_length(self):
        audio = _tone(500, 0.7, 0.4)
        assert saturate(audio, SR).shape[0] == audio.shape[0]
