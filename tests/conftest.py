"""Shared pytest fixtures.

Resets the in-process rate limiters before every test. Several webapp test
modules share one module-level TestClient and fire many requests from the
same client identity in a single test/session — without a reset, the M44
cost-protection limits (added for the public Fly deployment) would trip
across unrelated tests. Production behavior is unaffected: this only clears
state kept in src.webapp.ratelimit, which is process-local by design.
"""

import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    try:
        from src.webapp.ratelimit import general_limiter, upload_limiter
    except ImportError:
        yield
        return
    upload_limiter.reset()
    general_limiter.reset()
    yield
    upload_limiter.reset()
    general_limiter.reset()
