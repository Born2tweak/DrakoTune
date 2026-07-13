"""In-process abuse protection for a public, unauthenticated deployment.

The product owner chose to deploy fully public with no login gate, but is
cost-sensitive: audio processing is CPU/memory work billed per second on a
single always-on-or-scale-to-zero machine (fly.toml). Without limits, one
scripted client (or a viral link) could keep the machine hot indefinitely.

Two independent protections, both in-memory (consistent with the existing
in-memory job store — no Redis, no extra cost):

1. Per-client-IP sliding-window rate limits, tighter for the expensive
   upload/processing endpoints than for page views.
2. A global concurrency semaphore around the processing call itself, so even
   many different IPs cannot run more DSP jobs at once than the box can hold
   (each job is single-threaded CPU work; M36 benchmark: ~0.07x realtime on
   the reference machine, so a handful of concurrent jobs saturates 1 vCPU).

All limits are env-configurable (documented in docs/DEPLOY_FLY.md) so the
owner can tighten or loosen them post-launch without a code change.
"""

import os
import threading
import time
from collections import deque

# Requests per IP per window. Upload is the expensive endpoint; page views
# and status polling get a looser budget. Defaults are deliberately tight —
# a real user uploads a handful of files per session, not dozens per minute.
UPLOAD_LIMIT = int(os.environ.get("DRAKOTUNE_RATE_LIMIT_UPLOADS_PER_MIN", "5"))
GENERAL_LIMIT = int(os.environ.get("DRAKOTUNE_RATE_LIMIT_REQUESTS_PER_MIN", "60"))
WINDOW_SECONDS = 60.0

# How many DSP jobs may run at once, server-wide, regardless of who asked.
# Keeps a burst of requests (from one IP or many) from all hitting the CPU
# simultaneously and running up compute time / starving the health check.
MAX_CONCURRENT_JOBS = int(os.environ.get("DRAKOTUNE_MAX_CONCURRENT_JOBS", "2"))


class _SlidingWindowLimiter:
    """Per-key (IP) request timestamps; O(1) amortized check-and-record."""

    def __init__(self, limit: int, window_seconds: float = WINDOW_SECONDS):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> tuple[bool, float]:
        """Returns (allowed, retry_after_seconds)."""
        now = time.time()
        with self._lock:
            q = self._hits.setdefault(key, deque())
            cutoff = now - self.window
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= self.limit:
                retry_after = self.window - (now - q[0])
                return False, max(retry_after, 1.0)
            q.append(now)
            return True, 0.0

    def reset(self) -> None:
        """Test-only: clear all tracked state."""
        with self._lock:
            self._hits.clear()


upload_limiter = _SlidingWindowLimiter(UPLOAD_LIMIT)
general_limiter = _SlidingWindowLimiter(GENERAL_LIMIT)

_job_semaphore = threading.Semaphore(MAX_CONCURRENT_JOBS)


class ServerBusyError(Exception):
    """Raised when the concurrency cap is already at MAX_CONCURRENT_JOBS."""


class job_slot:
    """Context manager: acquire a processing slot or raise ServerBusyError.

    Non-blocking on purpose — a caller should get an immediate 503 rather
    than queue silently behind other people's audio processing.
    """

    def __enter__(self) -> "job_slot":
        if not _job_semaphore.acquire(blocking=False):
            raise ServerBusyError(
                f"already processing {MAX_CONCURRENT_JOBS} job(s); try again shortly")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        _job_semaphore.release()


def client_ip(headers, fallback: str) -> str:
    """Best-effort real client IP behind Fly's proxy.

    Fly sets Fly-Client-IP on every request; X-Forwarded-For is a fallback
    for other proxies/local runs. Never trust these for security decisions
    that matter beyond cost-shielding — they are attacker-controllable in
    principle, which is acceptable here (worst case: a spoofed IP gets its
    own rate-limit bucket, not a bypass of the global concurrency cap).
    """
    for header in ("fly-client-ip", "x-forwarded-for"):
        value = headers.get(header)
        if value:
            return value.split(",")[0].strip()
    return fallback
