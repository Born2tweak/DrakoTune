"""Web skeleton tests (M12).

Exercises upload -> job status -> playback -> report and the error paths
(blocked preflight, undecodable file, unknown job) via the FastAPI TestClient.
Skips cleanly if the optional web stack is not installed.
"""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from fixtures.loader import AUDIO_DIR  # noqa: E402
from src.webapp import app  # noqa: E402

client = TestClient(app)


def _upload(name: str, data: bytes, content_type: str = "audio/wav") -> dict:
    resp = client.post("/api/audio/upload", files={"file": (name, data, content_type)})
    assert resp.status_code == 200
    return resp.json()


class TestUploadFlow:
    def test_index_serves_upload_form(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "<form" in resp.text and "Analyze" in resp.text

    def test_upload_completes_and_reports(self):
        data = (AUDIO_DIR / "harsh.wav").read_bytes()
        payload = _upload("harsh.wav", data)
        assert payload["status"] == "completed"
        assert "before" in payload["audio_urls"] and "after" in payload["audio_urls"]
        assert payload["objectives"]
        assert payload["has_report"] is True

    def test_job_status_endpoint(self):
        data = (AUDIO_DIR / "harsh.wav").read_bytes()
        job_id = _upload("harsh.wav", data)["job_id"]
        resp = client.get(f"/api/jobs/{job_id}")
        assert resp.status_code == 200 and resp.json()["status"] == "completed"

    def test_playback_serves_wav_via_signed_url(self):
        data = (AUDIO_DIR / "harsh.wav").read_bytes()
        payload = _upload("harsh.wav", data)
        for which in ("before", "after"):
            resp = client.get(payload["audio_urls"][which])  # signed URL
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "audio/wav"
            assert resp.content[:4] == b"RIFF"

    def test_result_page_has_players_and_report(self):
        data = (AUDIO_DIR / "harsh.wav").read_bytes()
        job_id = _upload("harsh.wav", data)["job_id"]
        resp = client.get(f"/jobs/{job_id}")
        assert resp.status_code == 200
        assert "<audio" in resp.text and "Findings" in resp.text

    def test_form_upload_redirects_to_result(self):
        data = (AUDIO_DIR / "harsh.wav").read_bytes()
        resp = client.post("/upload", files={"file": ("harsh.wav", data, "audio/wav")},
                           follow_redirects=False)
        assert resp.status_code == 303
        assert resp.headers["location"].startswith("/jobs/")


class TestErrorPaths:
    def test_silent_upload_is_blocked(self):
        data = (AUDIO_DIR / "silence.wav").read_bytes()
        payload = _upload("silence.wav", data)
        assert payload["status"] == "blocked"
        assert "silent" in payload["message"]

    def test_undecodable_upload_fails(self):
        payload = _upload("junk.wav", b"this is not audio at all")
        assert payload["status"] == "failed"
        assert "decode" in payload["message"].lower()

    def test_unknown_job_404(self):
        assert client.get("/api/jobs/nope").status_code == 404
        # Unsigned audio requests are rejected (403) before existence is checked,
        # so a missing job is not distinguishable from a real one without a token.
        assert client.get("/api/audio/nope/after").status_code == 403
        assert client.get("/jobs/nope").status_code == 404
