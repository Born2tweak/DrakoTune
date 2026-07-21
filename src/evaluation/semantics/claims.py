"""Claim records and the claim quarantine registry (DT-45).

A *claim* is any statement DrakoTune makes about its own quality or behavior.
DT-45's job is to make it impossible for an unsupported claim — "professional",
generalized improvement, do-no-harm — to render as approved. The registry is
the enforcement point: a claim renders as approved only when its status is an
approved status **and** it has not been quarantined. Anything else renders as
its true, non-approved status.

Claim approval itself (moving a claim to ``approved_public``) is a human-only
gate and is never performed by this module.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.evaluation.semantics.canonical import content_hash
from src.evaluation.semantics.enums import (
    APPROVED_CLAIM_STATUSES,
    ClaimClass,
    ClaimStatus,
    parse_enum,
)
from src.evaluation.semantics.errors import (
    ErrorCode,
    QuarantineAction,
    SchemaValidationError,
    ValidationError,
)

CLAIM_SCHEMA = "drakotune.claim"
CLAIM_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class Claim:
    """One versioned claim record (DT-45 subset of the canonical claim schema)."""

    claim_id: str
    exact_wording: str
    claim_class: ClaimClass
    status: ClaimStatus
    surface: str = "internal"
    scope: dict = field(default_factory=dict)
    supporting_results: tuple[str, ...] = ()
    rights_decision_id: str | None = None
    limitations: tuple[str, ...] = ()
    suspension_triggers: tuple[str, ...] = ()
    owner: str = "product_claim_owner"
    expires_at: str | None = None
    quarantined: bool = False
    quarantine_reasons: tuple[str, ...] = ()
    schema: str = CLAIM_SCHEMA
    schema_version: str = CLAIM_SCHEMA_VERSION

    def to_dict(self, *, with_hash: bool = True) -> dict:
        payload = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "claim_id": self.claim_id,
            "exact_wording": self.exact_wording,
            "class": self.claim_class.value,
            "status": self.status.value,
            "surface": self.surface,
            "scope": dict(self.scope),
            "supporting_results": list(self.supporting_results),
            "rights_decision_id": self.rights_decision_id,
            "limitations": list(self.limitations),
            "suspension_triggers": list(self.suspension_triggers),
            "owner": self.owner,
            "expires_at": self.expires_at,
            "quarantined": self.quarantined,
            "quarantine_reasons": list(self.quarantine_reasons),
        }
        if with_hash:
            payload["content_hash"] = content_hash(payload)
        return payload

    @classmethod
    def from_dict(cls, d: dict) -> "Claim":
        return cls(
            claim_id=d["claim_id"],
            exact_wording=d["exact_wording"],
            claim_class=parse_enum(ClaimClass, d["class"]),
            status=parse_enum(ClaimStatus, d["status"]),
            surface=d.get("surface", "internal"),
            scope=dict(d.get("scope", {})),
            supporting_results=tuple(d.get("supporting_results", ())),
            rights_decision_id=d.get("rights_decision_id"),
            limitations=tuple(d.get("limitations", ())),
            suspension_triggers=tuple(d.get("suspension_triggers", ())),
            owner=d.get("owner", "product_claim_owner"),
            expires_at=d.get("expires_at"),
            quarantined=bool(d.get("quarantined", False)),
            quarantine_reasons=tuple(d.get("quarantine_reasons", ())),
            schema=d.get("schema", CLAIM_SCHEMA),
            schema_version=d.get("schema_version", CLAIM_SCHEMA_VERSION),
        )

    def renders_as_approved(self) -> bool:
        """True only if this claim may be shown to a reader as approved.

        The single most important invariant in DT-45: a quarantined claim, or
        any claim not in an approved status, never renders as approved.
        """
        return (not self.quarantined) and self.status in APPROVED_CLAIM_STATUSES

    def render_status(self) -> ClaimStatus:
        """The status a reader is allowed to see.

        A quarantined claim is downgraded to ``suspended`` for display so it can
        never be mistaken for an approved claim even if its stored status drifts.
        """
        if self.quarantined:
            return ClaimStatus.SUSPENDED
        return self.status


class ClaimQuarantineRegistry:
    """In-memory registry of claims with approval-gating enforcement."""

    def __init__(self, claims: list[Claim] | None = None) -> None:
        self._claims: dict[str, Claim] = {}
        for c in claims or []:
            self.add(c)

    def add(self, claim: Claim) -> None:
        if claim.claim_id in self._claims:
            raise SchemaValidationError(
                (
                    ValidationError(
                        error_code=ErrorCode.INVALID_IDENTITY,
                        field_path="claim_id",
                        message=f"duplicate claim_id {claim.claim_id!r}",
                        schema=CLAIM_SCHEMA,
                        schema_version=CLAIM_SCHEMA_VERSION,
                        record_id=claim.claim_id,
                    ),
                )
            )
        self._claims[claim.claim_id] = claim

    def get(self, claim_id: str) -> Claim:
        return self._claims[claim_id]

    def all(self) -> tuple[Claim, ...]:
        return tuple(self._claims.values())

    def quarantine(self, claim_id: str, reasons: tuple[str, ...]) -> Claim:
        """Quarantine a claim (idempotent-safe). Returns the new record."""
        old = self._claims[claim_id]
        merged = tuple(dict.fromkeys(old.quarantine_reasons + reasons))
        new = Claim(
            claim_id=old.claim_id,
            exact_wording=old.exact_wording,
            claim_class=old.claim_class,
            status=old.status,
            surface=old.surface,
            scope=old.scope,
            supporting_results=old.supporting_results,
            rights_decision_id=old.rights_decision_id,
            limitations=old.limitations,
            suspension_triggers=old.suspension_triggers,
            owner=old.owner,
            expires_at=old.expires_at,
            quarantined=True,
            quarantine_reasons=merged,
        )
        self._claims[claim_id] = new
        return new

    def approved_claims(self) -> tuple[Claim, ...]:
        """Only the claims that legitimately render as approved."""
        return tuple(c for c in self._claims.values() if c.renders_as_approved())

    def quarantined_claims(self) -> tuple[Claim, ...]:
        return tuple(c for c in self._claims.values() if c.quarantined)

    def assert_no_quarantined_approved(self) -> None:
        """Raise if any quarantined claim would render as approved.

        Belt-and-braces: ``renders_as_approved`` already excludes quarantined
        claims, but this guard is called by report/manifest rendering so a
        regression is caught loudly rather than shipping an approved-looking
        unsupported claim.
        """
        offenders = [
            c.claim_id
            for c in self._claims.values()
            if c.quarantined and c.status in APPROVED_CLAIM_STATUSES and c.renders_as_approved()
        ]
        if offenders:
            raise SchemaValidationError(
                tuple(
                    ValidationError(
                        error_code=ErrorCode.CLAIM_EVIDENCE_INELIGIBLE,
                        field_path="status",
                        message="quarantined claim rendered as approved",
                        schema=CLAIM_SCHEMA,
                        schema_version=CLAIM_SCHEMA_VERSION,
                        record_id=cid,
                        quarantine_action=QuarantineAction.QUARANTINE,
                    )
                    for cid in offenders
                )
            )

    def to_list(self) -> list[dict]:
        return [c.to_dict() for c in self._claims.values()]

    @classmethod
    def from_json_file(cls, path: str | Path) -> "ClaimQuarantineRegistry":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        claims = [Claim.from_dict(c) for c in data["claims"]]
        return cls(claims)


# Location of the seeded claim inventory (relative to repo root).
CLAIM_INVENTORY_PATH = (
    Path(__file__).resolve().parents[3]
    / "AURELIAN"
    / "07_DATA_AND_PROVENANCE"
    / "claim_inventory.json"
)


def load_default_registry() -> ClaimQuarantineRegistry:
    """Load the seeded current-claim inventory from AURELIAN provenance data."""
    return ClaimQuarantineRegistry.from_json_file(CLAIM_INVENTORY_PATH)
