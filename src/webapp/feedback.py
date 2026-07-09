"""Pilot feedback capture (M16).

Records lightweight feedback (helpful / not, plus an optional comment) tied to a
job. Kept in memory for the skeleton; if DRAKOTUNE_FEEDBACK_LOG is set, each
entry is also appended as JSONL for durable pilot collection. No PII is
requested and audio is never attached.
"""

import json
import os
import time

VALID_RATINGS = {"up", "down"}
_MAX_COMMENT = 2000

_FEEDBACK: list[dict] = []
FEEDBACK_LOG = os.environ.get("DRAKOTUNE_FEEDBACK_LOG")


def record_feedback(job_id: str, rating: str, comment: str = "") -> dict:
    """Store one feedback entry. Rating is normalized to up/down."""
    normalized = rating if rating in VALID_RATINGS else "up"
    entry = {
        "job_id": job_id,
        "rating": normalized,
        "comment": (comment or "")[:_MAX_COMMENT],
        "at": round(time.time(), 3),
    }
    _FEEDBACK.append(entry)
    if FEEDBACK_LOG:
        with open(FEEDBACK_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    return entry


def list_feedback() -> list[dict]:
    return list(_FEEDBACK)
