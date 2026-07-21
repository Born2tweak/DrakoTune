"""Canonical serialization and content hashing (DT-45).

A canonical record must serialize to exactly one byte string regardless of
in-memory ordering, so two runs that mean the same thing hash the same. Rules
(from the canonical spec "Identity and canonical serialization"):

- UTF-8, key-sorted, no insignificant whitespace.
- ``NaN`` / ``+Inf`` / ``-Inf`` are forbidden; missing/unknown/not-applicable
  use typed states, never a sentinel float.
- The ``content_hash`` field is omitted while hashing.
- Volatile local paths and direct identity never enter canonical bytes (the
  caller is responsible for redaction; this layer refuses non-finite numbers).
"""

import hashlib
import json
import math
from typing import Any

from src.evaluation.semantics.errors import (
    ErrorCode,
    QuarantineAction,
    SchemaValidationError,
    ValidationError,
)

CONTENT_HASH_FIELD = "content_hash"
HASH_PREFIX = "sha256:"


def assert_finite(value: Any, field_path: str) -> None:
    """Raise a canonical ``nonfinite_number`` error for NaN/Inf floats."""
    if isinstance(value, float) and not math.isfinite(value):
        raise SchemaValidationError(
            (
                ValidationError(
                    error_code=ErrorCode.NONFINITE_NUMBER,
                    field_path=field_path,
                    message="non-finite numbers are forbidden in canonical records",
                    quarantine_action=QuarantineAction.QUARANTINE,
                ),
            )
        )


def _check_finite_recursive(obj: Any, path: str) -> None:
    if isinstance(obj, float):
        assert_finite(obj, path)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _check_finite_recursive(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _check_finite_recursive(v, f"{path}[{i}]")


def canonical_bytes(payload: dict, *, omit_hash: bool = True) -> bytes:
    """Return the canonical UTF-8 byte serialization of ``payload``.

    Keys are sorted recursively (via ``sort_keys``); the ``content_hash`` field
    is omitted by default so a record can carry the hash of its own body.
    """
    body = {k: v for k, v in payload.items() if not (omit_hash and k == CONTENT_HASH_FIELD)}
    _check_finite_recursive(body, "")
    # allow_nan=False makes json itself reject any NaN/Inf that slipped through.
    return json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def content_hash(payload: dict) -> str:
    """SHA-256 of the canonical serialization, ``sha256:``-prefixed."""
    digest = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    return f"{HASH_PREFIX}{digest}"


def verify_hash(payload: dict) -> bool:
    """True iff ``payload[content_hash]`` matches the recomputed hash."""
    stored = payload.get(CONTENT_HASH_FIELD)
    return isinstance(stored, str) and stored == content_hash(payload)
