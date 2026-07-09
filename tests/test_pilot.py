"""Pilot readiness tests (M16).

Covers the end-to-end workflow, visible limitations, privacy page, and feedback
capture — the acceptance criteria for a controlled pilot.
"""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from fixtures.loader import AUDIO_DIR  # noqa: E402
from src.webapp import app  # noqa: E402
from src.webapp.feedback import list_feedback, record_feedback  # noqa: E402

client = TestClient(app)


def _upload(name: str) -> dict:
    data = (AUDIO_DIR / f"{name}.wav").read_bytes()
    return client.post("/api/audio/upload", files={"file": (f"{name}.wav", data, "audio/wav")}).json()


class TestVisibleLimitations:
    def test_landing_states_what_it_is_not(self):
        text = client.get("/").text
        assert "isn" in text  # "What this is — and isn't"
        assert "not a professional" in text.lower()
        assert 'href="/privacy"' in text

    def test_footer_links_privacy_everywhere(self):
        for path in ("/", "/privacy"):
            assert 'href="/privacy"' in client.get(path).text

    def test_privacy_page_renders(self):
        text = client.get("/privacy").text
        assert client.get("/privacy").status_code == 200
        assert "third-party" in text and "Privacy" in text


class TestFeedback:
    def test_api_feedback_records(self):
        before = len(list_feedback())
        resp = client.post("/api/feedback", data={"job_id": "job1", "rating": "up", "comment": "nice"})
        assert resp.status_code == 200 and resp.json()["ok"] is True
        assert len(list_feedback()) == before + 1

    def test_invalid_rating_normalized(self):
        entry = record_feedback("job2", "banana", "x")
        assert entry["rating"] == "up"

    def test_form_feedback_redirects(self):
        resp = client.post("/feedback", data={"job_id": "jobX", "rating": "down"},
                           follow_redirects=False)
        assert resp.status_code == 303
        assert resp.headers["location"] == "/jobs/jobX?thanks=1"

    def test_result_page_has_feedback_form(self):
        job_id = _upload("harsh")["job_id"]
        text = client.get(f"/jobs/{job_id}").text
        assert 'action="/feedback"' in text and 'name="rating"' in text


class TestEndToEnd:
    def test_full_pilot_flow(self):
        # upload -> completed -> playback -> report+feedback -> feedback -> delete
        payload = _upload("harsh")
        assert payload["status"] == "completed"
        job_id = payload["job_id"]

        assert client.get(payload["audio_urls"]["after"]).status_code == 200

        page = client.get(f"/jobs/{job_id}").text
        assert "Before / After" in page and "Findings" in page and "Feedback" in page

        before = len(list_feedback())
        client.post("/api/feedback", data={"job_id": job_id, "rating": "up", "comment": "clear"})
        assert len(list_feedback()) == before + 1

        assert client.delete(f"/api/jobs/{job_id}").status_code == 200
        assert client.get(f"/api/jobs/{job_id}").status_code == 404
