"""Private-storage / signed-access tests (M13).

Verifies audio is never publicly reachable: unsigned, tampered, and expired
requests are rejected; only valid signed URLs succeed. Also covers job deletion
(retention) and the signing primitives.
"""

import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from fixtures.loader import AUDIO_DIR  # noqa: E402
from src.webapp import app  # noqa: E402
from src.webapp.security import DEFAULT_TTL_SECONDS, sign, signed_url, verify  # noqa: E402

client = TestClient(app)


def _completed_job() -> dict:
    data = (AUDIO_DIR / "harsh.wav").read_bytes()
    return client.post("/api/audio/upload", files={"file": ("harsh.wav", data, "audio/wav")}).json()


class TestSignedAccess:
    def test_unsigned_request_forbidden(self):
        job_id = _completed_job()["job_id"]
        resp = client.get(f"/api/audio/{job_id}/after")  # no token
        assert resp.status_code == 403

    def test_tampered_signature_forbidden(self):
        payload = _completed_job()
        url = payload["audio_urls"]["after"]
        tampered = url[:-1] + ("0" if url[-1] != "0" else "1")
        assert client.get(tampered).status_code == 403

    def test_expired_signature_forbidden(self):
        job_id = _completed_job()["job_id"]
        past = int(time.time()) - 10
        sig = sign(job_id, "after", past)
        resp = client.get(f"/api/audio/{job_id}/after?exp={past}&sig={sig}")
        assert resp.status_code == 403

    def test_wrong_which_signature_forbidden(self):
        job_id = _completed_job()["job_id"]
        exp = int(time.time()) + 60
        sig_for_before = sign(job_id, "before", exp)
        # Reuse a "before" signature on the "after" resource -> rejected.
        resp = client.get(f"/api/audio/{job_id}/after?exp={exp}&sig={sig_for_before}")
        assert resp.status_code == 403

    def test_valid_signed_url_succeeds(self):
        payload = _completed_job()
        assert client.get(payload["audio_urls"]["after"]).status_code == 200

    def test_public_dict_has_no_raw_paths(self):
        payload = _completed_job()
        # audio_urls are signed API routes, never filesystem paths.
        for url in payload["audio_urls"].values():
            assert url.startswith("/api/audio/") and "sig=" in url


class TestRetention:
    def test_delete_removes_job_and_audio(self):
        payload = _completed_job()
        job_id = payload["job_id"]
        assert client.get(payload["audio_urls"]["after"]).status_code == 200
        assert client.delete(f"/api/jobs/{job_id}").status_code == 200
        # After deletion the job is gone (404) and audio is unavailable.
        assert client.get(f"/api/jobs/{job_id}").status_code == 404
        assert client.get(payload["audio_urls"]["after"]).status_code == 404

    def test_delete_unknown_404(self):
        assert client.delete("/api/jobs/nope").status_code == 404


class TestPrimitives:
    def test_verify_roundtrip(self):
        exp = int(time.time()) + DEFAULT_TTL_SECONDS
        assert verify("job1", "after", exp, sign("job1", "after", exp))

    def test_verify_rejects_expired_and_empty(self):
        assert not verify("j", "after", int(time.time()) - 1, sign("j", "after", int(time.time()) - 1))
        assert not verify("j", "after", 0, "")

    def test_signed_url_shape(self):
        url = signed_url("abc", "before")
        assert url.startswith("/api/audio/abc/before?exp=") and "sig=" in url
