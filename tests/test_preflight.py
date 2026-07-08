"""Preflight validation tests (M03).

Covers valid audio, silence, too-short, missing file, decode failure, the
severe-clipping warning, and the enforce/rollback behavior of ensure_processable.
"""

import numpy as np
import pytest
import soundfile as sf

from fixtures.loader import AUDIO_DIR
from src.ingestion import (
    PREFLIGHT_VERSION,
    PreflightError,
    ensure_processable,
    preflight,
)


def _fixture_path(name: str) -> str:
    return str(AUDIO_DIR / f"{name}.wav")


class TestValid:
    def test_clean_fixture_passes(self):
        report = preflight(_fixture_path("clean_tone"))
        assert report.passed
        assert report.blockers == ()
        assert report.metrics["sample_rate"] == 44100
        assert report.metrics["channels"] == 1
        assert report.metrics["duration_seconds"] == pytest.approx(1.0, abs=0.01)
        assert report.preflight_version == PREFLIGHT_VERSION

    def test_valid_report_serializes(self):
        report = preflight(_fixture_path("harsh"))
        d = report.to_dict()
        assert d["passed"] is True
        assert "metrics" in d and d["preflight_version"] == PREFLIGHT_VERSION


class TestBlockers:
    def test_silence_is_blocked(self):
        report = preflight(_fixture_path("silence"))
        assert not report.passed
        assert "silent_or_near_silent" in report.blockers

    def test_missing_file_is_blocked(self):
        report = preflight("does/not/exist.wav")
        assert not report.passed
        assert "file_not_found" in report.blockers

    def test_too_short_is_blocked(self, tmp_path):
        path = tmp_path / "tiny.wav"
        sf.write(str(path), np.zeros(int(44100 * 0.05), dtype="float32") + 0.2, 44100)
        report = preflight(str(path))
        assert not report.passed
        assert "too_short" in report.blockers

    def test_corrupt_file_is_blocked(self, tmp_path):
        path = tmp_path / "corrupt.wav"
        path.write_bytes(b"this is not a real wav file")
        report = preflight(str(path))
        assert not report.passed
        assert "decode_failed" in report.blockers


class TestWarnings:
    def test_clipped_fixture_warns_but_passes(self):
        report = preflight(_fixture_path("clipped"))
        assert report.passed  # clipping is a warning, not a blocker
        assert "severe_clipping" in report.warnings


class TestEnforcement:
    def test_ensure_raises_on_blocked(self):
        with pytest.raises(PreflightError) as exc:
            ensure_processable(_fixture_path("silence"), enforce=True)
        assert "silent_or_near_silent" in exc.value.report.blockers

    def test_ensure_rollback_does_not_raise(self):
        # enforce=False is the documented rollback path.
        report = ensure_processable(_fixture_path("silence"), enforce=False)
        assert not report.passed  # still reported...
        assert "silent_or_near_silent" in report.blockers  # ...just not raised

    def test_ensure_passes_valid(self):
        report = ensure_processable(_fixture_path("clean_tone"), enforce=True)
        assert report.passed
