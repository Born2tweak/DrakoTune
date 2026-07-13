"""Cost-protection tests (M44): per-IP rate limits + concurrency cap.

Added after the product owner deployed publicly with no login gate and asked
for spam/abuse protection they can afford. These guard against a single
client (or a burst across many) driving up compute time on the always-on-or
-scale-to-zero Fly machine.
"""

import threading
import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from fixtures.loader import AUDIO_DIR  # noqa: E402
from src.webapp import app as app_instance  # noqa: E402
from src.webapp.ratelimit import (
    ServerBusyError,
    _SlidingWindowLimiter,
    client_ip,
    job_slot,
)

client = TestClient(app_instance)


class TestSlidingWindowLimiter:
    def test_allows_up_to_limit_then_blocks(self):
        limiter = _SlidingWindowLimiter(limit=3, window_seconds=60.0)
        results = [limiter.allow("1.2.3.4")[0] for _ in range(4)]
        assert results == [True, True, True, False]

    def test_different_keys_are_independent(self):
        limiter = _SlidingWindowLimiter(limit=1, window_seconds=60.0)
        assert limiter.allow("a")[0] is True
        assert limiter.allow("b")[0] is True
        assert limiter.allow("a")[0] is False

    def test_window_expires(self):
        limiter = _SlidingWindowLimiter(limit=1, window_seconds=0.05)
        assert limiter.allow("x")[0] is True
        assert limiter.allow("x")[0] is False
        time.sleep(0.07)
        assert limiter.allow("x")[0] is True

    def test_retry_after_is_positive_when_blocked(self):
        limiter = _SlidingWindowLimiter(limit=1, window_seconds=10.0)
        limiter.allow("x")
        allowed, retry_after = limiter.allow("x")
        assert not allowed and retry_after > 0


class TestClientIpExtraction:
    def test_prefers_fly_client_ip_header(self):
        assert client_ip({"fly-client-ip": "9.9.9.9"}, "127.0.0.1") == "9.9.9.9"

    def test_falls_back_to_x_forwarded_for(self):
        assert client_ip({"x-forwarded-for": "8.8.8.8, 1.1.1.1"}, "127.0.0.1") == "8.8.8.8"

    def test_falls_back_to_direct_connection(self):
        assert client_ip({}, "127.0.0.1") == "127.0.0.1"


class TestConcurrencyGuard:
    def test_job_slot_raises_when_saturated(self):
        from src.webapp import ratelimit

        original = ratelimit._job_semaphore
        ratelimit._job_semaphore = threading.Semaphore(1)
        try:
            with job_slot():
                with pytest.raises(ServerBusyError):
                    with job_slot():
                        pass
        finally:
            ratelimit._job_semaphore = original

    def test_slot_released_after_use(self):
        from src.webapp import ratelimit

        original = ratelimit._job_semaphore
        ratelimit._job_semaphore = threading.Semaphore(1)
        try:
            with job_slot():
                pass
            with job_slot():  # must succeed: the first slot was released
                pass
        finally:
            ratelimit._job_semaphore = original


class TestEndToEndRateLimiting:
    def test_upload_endpoint_429s_after_limit(self):
        from src.webapp.ratelimit import upload_limiter

        original_limit = upload_limiter.limit
        upload_limiter.limit = 2
        try:
            data = (AUDIO_DIR / "harsh.wav").read_bytes()
            codes = []
            for _ in range(3):
                r = client.post("/api/audio/upload", files={"file": ("v.wav", data, "audio/wav")})
                codes.append(r.status_code)
            assert codes[:2] == [200, 200]
            assert codes[2] == 429
            blocked = client.post("/api/audio/upload", files={"file": ("v.wav", data, "audio/wav")})
            assert "Retry-After" in blocked.headers
        finally:
            upload_limiter.limit = original_limit

    def test_health_endpoint_exempt_from_rate_limit(self):
        from src.webapp.ratelimit import general_limiter

        original_limit = general_limiter.limit
        general_limiter.limit = 1
        try:
            general_limiter.allow("testclient")  # consume the only slot
            # health must still respond even though the general limiter is spent
            assert client.get("/health").status_code == 200
        finally:
            general_limiter.limit = original_limit
