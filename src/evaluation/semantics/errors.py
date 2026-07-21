"""Validation error contract (DT-45).

Every rejection of a canonical record returns a structured error rather than a
bare exception string, so that ingestion, quarantine, and audit tooling can act
on a stable code and field path. Codes are the canonical minimum set from
``AURELIAN/03_CANONICAL/IMPLEMENTATION_SCHEMA_EXAMPLES.md`` ("Validation error
contract").

Validation never silently repairs rights, identity, protocol, or evidence-tier
ambiguity: an ambiguous record is rejected (and typically quarantined), never
coerced into a pass.
"""

from dataclasses import dataclass, field
from enum import Enum


class ErrorCode(str, Enum):
    """Canonical minimum validation error codes."""

    MISSING_REQUIRED_FIELD = "missing_required_field"
    UNKNOWN_ENUM = "unknown_enum"
    INVALID_IDENTITY = "invalid_identity"
    INVALID_TIMESTAMP = "invalid_timestamp"
    NONFINITE_NUMBER = "nonfinite_number"
    HASH_MISMATCH = "hash_mismatch"
    DUPLICATE_ACTIVE_RESPONSE = "duplicate_active_response"
    BROKEN_PROVENANCE_EDGE = "broken_provenance_edge"
    RIGHTS_NOT_AUTHORIZED = "rights_not_authorized"
    RIGHTS_EXPIRED_OR_WITHDRAWN = "rights_expired_or_withdrawn"
    SPLIT_LEAKAGE = "split_leakage"
    PROTOCOL_NOT_FROZEN = "protocol_not_frozen"
    BUILD_OR_SCOPE_MISMATCH = "build_or_scope_mismatch"
    CLAIM_EVIDENCE_INELIGIBLE = "claim_evidence_ineligible"
    UNSUPPORTED_SCHEMA_VERSION = "unsupported_schema_version"


# What a caller should do with the offending record when this error fires.
class QuarantineAction(str, Enum):
    REJECT = "reject"  # drop the record; it is malformed
    QUARANTINE = "quarantine"  # retain but mark unusable pending review


@dataclass(frozen=True)
class ValidationError:
    """One structured validation failure.

    Mirrors the canonical error contract: a stable code, a JSON-style field
    path, a safe (identity-free) message, retryability, and the quarantine
    action. ``record_id`` is included only when it was readable.
    """

    error_code: ErrorCode
    field_path: str
    message: str
    schema: str = "drakotune.evidence_result"
    schema_version: str = ""
    record_id: str | None = None
    retryable: bool = False
    quarantine_action: QuarantineAction = QuarantineAction.REJECT

    def to_dict(self) -> dict:
        return {
            "error_code": self.error_code.value,
            "field_path": self.field_path,
            "message": self.message,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "retryable": self.retryable,
            "quarantine_action": self.quarantine_action.value,
        }


@dataclass(frozen=True)
class SchemaValidationError(Exception):
    """Raised when a canonical record fails validation.

    Carries the full list of structured errors so a caller can report all
    problems at once instead of one-at-a-time.
    """

    errors: tuple[ValidationError, ...] = field(default_factory=tuple)

    def __str__(self) -> str:
        return "; ".join(f"{e.error_code.value}@{e.field_path}: {e.message}" for e in self.errors)

    def codes(self) -> tuple[ErrorCode, ...]:
        return tuple(e.error_code for e in self.errors)
