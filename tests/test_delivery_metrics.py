"""Delivery measurement tests (DT-97 corrective).

These pin that the numbers describe what they claim to describe. They do NOT
assert that any value is good: there is no certified perceptual objective in
this project (N-016..N-022, DEF-003), so a threshold here would be an
unsupported quality claim wearing a test's clothing.
"""

import pathlib

import numpy as np
import pytest
import soundfile as sf

from src.evaluation import delivery_metrics
from src.evaluation.delivery_metrics import (
    DELIVERY_METRICS_VERSION,
    measure_array,
    measure_delivery,
)

SR = 44100


def _tone(freq=300.0, seconds=1.0, amp=0.5, sr=SR, phase=0.0):
    t = np.arange(int(sr * seconds)) / sr
    return (np.sin(2 * np.pi * freq * t + phase) * amp).astype(np.float32)


# -- Level measurements ------------------------------------------------------
class TestLevels:
    def test_sample_peak_matches_the_signal(self):
        m = measure_array(_tone(amp=0.5), SR)
        assert m.sample_peak_dbfs == pytest.approx(-6.02, abs=0.1)

    def test_true_peak_is_at_least_the_sample_peak(self):
        """Inter-sample peaks can exceed the sample peak; they never fall below."""
        m = measure_array(_tone(freq=7000.0, amp=0.9), SR)
        assert m.true_peak_dbfs >= m.sample_peak_dbfs - 0.01

    def test_true_peak_catches_an_intersample_overshoot(self):
        """A tone at SR/4 offset in phase peaks between samples, not on them.

        This is the case a sample-peak meter misses and an encoder does not.
        """
        signal = _tone(freq=SR / 4.0, amp=0.99, phase=np.pi / 4)
        m = measure_array(signal, SR)
        assert m.true_peak_dbfs > m.sample_peak_dbfs

    def test_crest_factor_separates_peak_from_loudness(self):
        """The whole point of reporting it: same peak, very different density."""
        steady = _tone(amp=0.9)
        spiky = np.zeros(SR, dtype=np.float32)
        spiky[::2000] = 0.9
        assert measure_array(spiky, SR).crest_factor_db > \
               measure_array(steady, SR).crest_factor_db + 10.0

    def test_clipping_is_counted(self):
        clipped = np.clip(_tone(amp=2.0), -1.0, 1.0)
        assert measure_array(clipped, SR).clipped_samples > 0

    def test_clean_signal_reports_no_clipping(self):
        assert measure_array(_tone(amp=0.5), SR).clipped_samples == 0


# -- Stereo behaviour: what DT-98 doubling will be judged against ------------
class TestStereo:
    def test_mono_reports_no_stereo_fields(self):
        m = measure_array(_tone(), SR)
        assert m.channels == 1
        assert m.stereo_correlation is None
        assert m.mono_folddown_delta_db is None

    def test_identical_channels_are_fully_correlated_and_survive_folddown(self):
        mono = _tone()
        m = measure_array(np.stack([mono, mono], axis=1), SR)
        assert m.stereo_correlation == pytest.approx(1.0, abs=1e-6)
        assert m.mono_folddown_delta_db == pytest.approx(0.0, abs=0.01)

    def test_inverted_channels_cancel_on_folddown(self):
        """The failure a correlation check exists to catch."""
        mono = _tone()
        m = measure_array(np.stack([mono, -mono], axis=1), SR)
        assert m.stereo_correlation == pytest.approx(-1.0, abs=1e-6)
        assert m.mono_folddown_delta_db < -40.0

    def test_decorrelated_channels_lose_about_3db_to_mono(self):
        """Two independent sources sum incoherently: the honest wide case."""
        rng = np.random.default_rng(7)
        left = rng.normal(0, 0.2, SR).astype(np.float32)
        right = rng.normal(0, 0.2, SR).astype(np.float32)
        m = measure_array(np.stack([left, right], axis=1), SR)
        assert abs(m.stereo_correlation) < 0.05
        assert -4.0 < m.mono_folddown_delta_db < -2.0


# -- Adversarial input -------------------------------------------------------
class TestDegenerateInput:
    def test_silence_does_not_raise_and_reports_no_lufs(self):
        m = measure_array(np.zeros(SR, dtype=np.float32), SR)
        assert m.sample_peak_dbfs == -120.0
        assert m.integrated_lufs is None
        assert m.clipped_samples == 0

    def test_empty_signal_does_not_raise(self):
        m = measure_array(np.zeros(0, dtype=np.float32), SR)
        assert m.duration_seconds == 0.0
        assert m.integrated_lufs is None

    def test_single_sample_does_not_raise(self):
        """Too short for the oversampler's FFT; must degrade, not explode."""
        m = measure_array(np.array([0.5], dtype=np.float32), SR)
        assert m.true_peak_dbfs <= 0.0

    def test_signal_too_short_for_lufs_reports_none_rather_than_faking(self):
        m = measure_array(_tone(seconds=0.05), SR)
        assert m.integrated_lufs is None

    def test_silent_channel_has_no_defined_correlation(self):
        mono = _tone()
        silent = np.zeros_like(mono)
        m = measure_array(np.stack([mono, silent], axis=1), SR)
        assert m.stereo_correlation is None


# -- Contract ----------------------------------------------------------------
class TestContract:
    def test_measurement_is_deterministic(self):
        signal = _tone(amp=0.4)
        assert measure_array(signal, SR).to_dict() == measure_array(signal, SR).to_dict()

    def test_reads_a_written_file(self, tmp_path):
        path = tmp_path / "d.wav"
        sf.write(str(path), _tone(amp=0.5), SR, subtype="PCM_16")
        m = measure_delivery(str(path))
        assert m.channels == 1
        assert m.duration_seconds == pytest.approx(1.0, abs=0.01)

    def test_payload_carries_no_score_or_verdict(self):
        """Guard against the exact drift this module's docstring forbids.

        If someone later adds a "quality"/"grade"/"pass" key, that is an
        unsupported claim and this test is where it stops.
        """
        payload = measure_array(_tone(), SR).to_dict()
        forbidden = ("score", "quality", "grade", "rating", "pass", "verdict", "ok")
        assert not [k for k in payload if any(f in k.lower() for f in forbidden)]
        assert payload["version"] == DELIVERY_METRICS_VERSION


class TestTruePeakIsBlockedNotWholeFile:
    """Regression for the 2026-08-04 production OOM.

    `_oversample` was called once on the entire file. For a 138-second stereo
    render that is a 24.3-million-point complex spectrum plus the irfft output
    and several full-length copies, per channel, at a length with no small prime
    factors. It measured 3.87 GB for a single call and OOM-killed the container.

    The fix processes fixed-size blocks with real context at each edge. These
    tests pin both halves of that: the memory bound, and that the number it
    reports did not change.
    """

    def test_no_single_oversample_call_sees_the_whole_file(self, monkeypatch):
        """The memory bound, stated as a property rather than a byte count."""
        seen = []
        original = delivery_metrics._oversample

        def spy(column, factor):
            seen.append(column.shape[0])
            return original(column, factor)

        monkeypatch.setattr(delivery_metrics, "_oversample", spy)

        sr = 44100
        long_signal = np.zeros(int(sr * 60), dtype=np.float32)  # 60 s
        long_signal[::1000] = 0.5
        delivery_metrics._true_peak(long_signal)

        assert seen, "oversampling never ran"
        ceiling = delivery_metrics._TRUE_PEAK_BLOCK + 2 * delivery_metrics._TRUE_PEAK_MARGIN
        assert max(seen) <= ceiling, (
            f"a single oversample call saw {max(seen)} samples, above the "
            f"{ceiling}-sample block ceiling -- whole-file behaviour is back")
        assert max(seen) < long_signal.shape[0], "the whole file was oversampled at once"

    def test_blocked_result_matches_whole_file_on_real_audio(self):
        """Correctness: blocking must not move the reported number.

        Real program material only. A sustained near-full-scale pure tone is
        pathological for both implementations -- the whole-file version imposes
        circular periodicity and under-reports it -- so it is not a valid oracle.
        """
        def whole_file(audio, factor=4):
            work = audio.reshape(-1, 1) if audio.ndim == 1 else audio
            return max(
                float(np.max(np.abs(delivery_metrics._oversample(
                    work[:, ch].astype(np.float64), factor))))
                for ch in range(work.shape[1]))

        fixtures = sorted(pathlib.Path("fixtures/audio_real").glob("*.wav"))
        assert fixtures, "no real fixtures to check against"
        for wav in fixtures:
            audio, _ = sf.read(str(wav), dtype="float32")
            blocked, oracle = delivery_metrics._true_peak(audio), whole_file(audio)
            delta_db = 20 * np.log10(max(blocked, 1e-12) / max(oracle, 1e-12))
            assert abs(delta_db) < 0.001, f"{wav.name}: {delta_db:+.6f} dB drift"

    def test_a_peak_on_a_block_boundary_is_still_found(self):
        """The interior/margin bookkeeping must not skip or double-count samples."""
        block = delivery_metrics._TRUE_PEAK_BLOCK
        signal = np.zeros(block * 3, dtype=np.float32)
        signal[block] = 0.95           # exactly on a boundary
        signal[block * 2 - 1] = 0.85   # just before the next
        assert delivery_metrics._true_peak(signal) >= 0.95
