"""Signed access for private audio (M13).

Audio is never publicly reachable: every playback URL is an HMAC-signed,
time-limited capability. Without a valid, unexpired signature the audio route
returns 403. This keeps user recordings private without a third-party service.

The signing secret comes from the DRAKOTUNE_SECRET environment variable. If it
is unset (dev only), a random per-process secret is generated and IS_EPHEMERAL
is True — tokens then do not survive a restart. Set DRAKOTUNE_SECRET in any
shared or production deployment.
"""

import hashlib
import hmac
import os
import secrets
import time

_env_secret = os.environ.get("DRAKOTUNE_SECRET")
IS_EPHEMERAL = _env_secret is None
_SECRET = (_env_secret or secrets.token_hex(32)).encode("utf-8")

DEFAULT_TTL_SECONDS = 3600


def _message(job_id: str, which: str, expires_at: int) -> bytes:
    return f"{job_id}:{which}:{expires_at}".encode("utf-8")


def sign(job_id: str, which: str, expires_at: int) -> str:
    return hmac.new(_SECRET, _message(job_id, which, expires_at), hashlib.sha256).hexdigest()


def signed_url(job_id: str, which: str, ttl: int = DEFAULT_TTL_SECONDS) -> str:
    expires_at = int(time.time()) + ttl
    sig = sign(job_id, which, expires_at)
    return f"/api/audio/{job_id}/{which}?exp={expires_at}&sig={sig}"


def verify(job_id: str, which: str, expires_at: int, sig: str) -> bool:
    if not sig or expires_at <= 0:
        return False
    if expires_at < int(time.time()):
        return False
    expected = sign(job_id, which, expires_at)
    return hmac.compare_digest(expected, sig)
