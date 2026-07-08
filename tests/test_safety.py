"""Technical-safety diagnostics tests (M04).

Verifies deterministic metrics, that clipping is measured independently of peak
level, integrity flags, stored analyzer settings, and confidence presence.
"""

import numpy as np
import pytest

from fixtures.loader import AUDIO_DIR
from src.diagnostics import diagnose_safety, measure_safety
from src.diagnostics.safety import SAFETY_ANALYZER_VERSION

SR = 44100


def _values(observations) -> dict:
    return {o.metric: o.value for o in observations}


def _sine(freq: float, amp: float, seconds: float = 1.0, dc: float = 0.0) -> np.ndarray:
    t = np.linspace(0, seconds, int(SR * seconds), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t) + dc).astype(np.float32)


class TestCleanVsClipped:
    def test_clean_fixture_has_no_clipping(self):
        result = diagnose_safety(str(AUDIO_DIR / "clean_tone.wav"), asset_id="clean")
        vals = _values(result.observations)
        assert vals["clipping_ratio"] < 1e-4
        assert "clipping" not in result.integrity_flags
        assert result.analyzer_version == SAFETY_ANALYZER_VERSION

    def test_clipped_fixture_flags_clipping(self):
        result = diagnose_safety(str(AUDIO_DIR / "clipped.wav"), asset_id="clip")
        vals = _values(result.observations)
        assert vals["clipping_ratio"] > 0.1
        assert "clipping" in result.integrity_flags

    def test_clipping_is_distinct_from_peak(self):
        """A hot-but-clean signal has a high peak yet near-zero clipping."""
        hot_clean = _sine(440, amp=0.98)
        obs, flags, _ = measure_safety(hot_clean, SR)
        vals = _values(obs)
        assert vals["peak_dbfs"] > -0.5      # very hot
        assert vals["clipping_ratio"] < 1e-4  # but not clipped
        assert "clipping" not in flags


class TestMetrics:
    def test_dc_offset_flagged(self):
        obs, flags, _ = measure_safety(_sine(300, 0.3, dc=0.1), SR)
        vals = _values(obs)
        assert vals["dc_offset"] == pytest.approx(0.1, abs=0.01)
        assert "dc_offset" in flags

    def test_duration_measured(self):
        obs, _, _ = measure_safety(_sine(300, 0.3, seconds=0.5), SR)
        assert _values(obs)["duration_seconds"] == pytest.approx(0.5, abs=0.01)

    def test_all_observations_have_valid_confidence(self):
        obs, _, _ = measure_safety(_sine(300, 0.3), SR)
        assert obs
        for o in obs:
            assert 0.0 <= o.confidence <= 1.0
            assert o.units

    def test_analyzer_settings_stored(self):
        result = diagnose_safety(str(AUDIO_DIR / "harsh.wav"), asset_id="h")
        ctx = result.measurement_context
        assert ctx["analyzer_version"] == SAFETY_ANALYZER_VERSION
        assert ctx["true_peak_oversample"] == 4
        assert "thresholds" in ctx

    def test_deterministic(self):
        sig = _sine(300, 0.4)
        a = _values(measure_safety(sig, SR)[0])
        b = _values(measure_safety(sig, SR)[0])
        assert a == b

    def test_empty_signal_safe(self):
        obs, flags, _ = measure_safety(np.zeros(0, dtype=np.float32), SR)
        assert "empty_audio" in flags
        assert _values(obs)["duration_seconds"] == 0.0
