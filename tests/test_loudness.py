"""Loudness and dynamics diagnostics tests (M05).

Covers quiet vs dynamic vs dense signals, full-file vs frame windows, silence
handling / confidence degradation, and determinism.
"""

import numpy as np
import pytest

from src.diagnostics import diagnose_loudness, measure_loudness
from src.diagnostics.loudness import LOUDNESS_ANALYZER_VERSION
from fixtures.loader import AUDIO_DIR

SR = 44100


def _values(observations) -> dict:
    return {o.metric: o.value for o in observations}


def _sine(freq: float, amp: float, seconds: float = 1.0) -> np.ndarray:
    t = np.linspace(0, seconds, int(SR * seconds), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


class TestLoudness:
    def test_quiet_signal_low_rms(self):
        obs, _, _ = measure_loudness(_sine(220, 0.02), SR)
        assert _values(obs)["rms_dbfs"] < -30

    def test_loud_signal_higher_rms(self):
        quiet = _values(measure_loudness(_sine(220, 0.02), SR)[0])["rms_dbfs"]
        loud = _values(measure_loudness(_sine(220, 0.5), SR)[0])["rms_dbfs"]
        assert loud > quiet + 10

    def test_sine_crest_factor_near_3db(self):
        obs, _, _ = measure_loudness(_sine(440, 0.5), SR)
        assert _values(obs)["crest_factor_db"] == pytest.approx(3.01, abs=0.3)


class TestDynamics:
    def test_dynamic_signal_has_wide_range(self):
        loud = _sine(440, 0.8, seconds=0.5)
        quiet = _sine(440, 0.05, seconds=0.5)
        sig = np.concatenate([loud, quiet, loud, quiet])
        obs, _, _ = measure_loudness(sig, SR)
        vals = _values(obs)
        assert vals["dynamic_range_db"] > 10
        assert vals["consistency_cv"] > 0.2

    def test_constant_signal_is_consistent(self):
        obs, _, _ = measure_loudness(_sine(440, 0.4, seconds=2.0), SR)
        vals = _values(obs)
        assert vals["dynamic_range_db"] < 3
        assert vals["consistency_cv"] < 0.1


class TestWindowsAndSilence:
    def test_observations_distinguish_full_and_frame(self):
        obs, _, _ = measure_loudness(_sine(300, 0.4), SR)
        windows = {o.metric: o.window for o in obs}
        assert windows["rms_dbfs"] == "full"
        assert windows["crest_factor_db"] == "full"
        assert windows["dynamic_range_db"] == "frame"
        assert windows["consistency_cv"] == "frame"

    def test_silence_degrades_confidence_and_flags(self):
        obs, flags, ctx = measure_loudness(_sine(300, 0.4, seconds=0.02), SR)
        # Very short -> few voiced frames -> low-confidence dynamics.
        dyn = next(o for o in obs if o.metric == "dynamic_range_db")
        assert dyn.confidence <= 0.6
        assert "insufficient_voiced_content" in flags or ctx["voiced_frames"] < 20

    def test_silence_handling_documented_in_context(self):
        _, _, ctx = measure_loudness(_sine(300, 0.4), SR)
        assert ctx["silence_frame_dbfs"] == -60.0
        assert ctx["lufs_implemented"] is False
        assert "voiced_frames" in ctx


class TestIntegration:
    def test_diagnose_loudness_on_fixture(self):
        result = diagnose_loudness(str(AUDIO_DIR / "clean_tone.wav"), asset_id="clean")
        assert result.analyzer_version == LOUDNESS_ANALYZER_VERSION
        assert len(result.observations) == 4

    def test_deterministic(self):
        sig = _sine(300, 0.4)
        assert _values(measure_loudness(sig, SR)[0]) == _values(measure_loudness(sig, SR)[0])
