"""Product-experience smoke checks (M14).

Structural/accessibility assertions on the rendered HTML: viewport + lang for
mobile, skip link, audio-first before/after players with labels and native
(keyboard) controls, scannable findings with confidence badges, and clear
blocked/failed banners. These stand in for visual verification in CI.
"""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from fixtures.loader import AUDIO_DIR  # noqa: E402
from src.webapp import app  # noqa: E402

client = TestClient(app)


def _result_html(name: str) -> str:
    data = (AUDIO_DIR / f"{name}.wav").read_bytes()
    job_id = client.post("/api/audio/upload", files={"file": (f"{name}.wav", data, "audio/wav")}).json()["job_id"]
    return client.get(f"/jobs/{job_id}").text


class TestAccessibilityBasics:
    def test_pages_declare_lang_and_viewport(self):
        for html_text in (client.get("/").text, _result_html("harsh")):
            assert '<html lang="en"' in html_text
            assert 'name="viewport"' in html_text

    def test_skip_link_present(self):
        assert 'class="skip"' in client.get("/").text

    def test_upload_input_is_labeled(self):
        text = client.get("/").text
        assert '<label for="file"' in text and 'id="file"' in text


class TestAudioFirst:
    def test_result_leads_with_before_after_players(self):
        text = _result_html("harsh")
        assert "Before / After" in text
        assert text.count("<audio") == 2
        assert 'aria-label="Original vocal"' in text and 'aria-label="Processed vocal"' in text

    def test_audio_has_native_keyboard_controls(self):
        text = _result_html("harsh")
        assert "controls" in text  # native audio controls are keyboard-accessible


class TestScannableFindings:
    def test_confidence_badges_present(self):
        text = _result_html("harsh")
        assert "Findings" in text
        assert any(cls in text for cls in ("badge-high", "badge-medium", "badge-low"))

    def test_sections_present(self):
        text = _result_html("harsh")
        for section in ("Findings", "What DrakoTune did", "Evaluation", "Limitations"):
            assert section in text


class TestClearStates:
    def test_blocked_shows_alert_banner(self):
        text = _result_html("silence")
        assert 'role="alert"' in text
        assert "blocked" in text.lower()

    def test_clipped_shows_enhancement_limited_notice(self):
        text = _result_html("clipped")
        # Enhancement is blocked for severe clipping; the UI must say so.
        assert 'role="alert"' in text and "limited for safety" in text
