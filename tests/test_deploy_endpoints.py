"""Deploy-support endpoints: health check, upload cap, pilot banner (Fly hosting)."""

import importlib

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

# src.webapp.__init__ rebinds the name `app` to the FastAPI instance, so a
# plain `import src.webapp.app` yields the instance. Fetch the real module
# (for its _MAX_UPLOAD_BYTES global) via importlib.
app_module = importlib.import_module("src.webapp.app")
client = TestClient(app_module.app)


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["service"] == "drakotune"


def test_health_runs_no_dsp():
    # A liveness probe must not touch the audio stack.
    assert "audio_urls" not in client.get("/health").json()


def test_oversized_upload_rejected(monkeypatch):
    monkeypatch.setattr(app_module, "_MAX_UPLOAD_BYTES", 100)
    r = client.post("/api/audio/upload",
                    files={"file": ("big.wav", b"x" * 500, "audio/wav")})
    assert r.status_code == 413 and r.json()["error"] == "file_too_large"


def test_normal_upload_not_blocked_by_cap():
    # Guards against an off-by-unit error in the limit (MB vs bytes).
    assert app_module._MAX_UPLOAD_BYTES >= 1_000_000


def test_pilot_banner_present_on_pages():
    assert "Experimental pilot" in client.get("/").text
