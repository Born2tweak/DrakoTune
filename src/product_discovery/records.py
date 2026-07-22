"""Pseudonymized discovery-record schema (DT-53).

A discovery record captures what one participant said/did during an approved
interview or workflow observation — but **never direct identity**. Records carry
a pseudonym, an explicit consent state, a retention deadline, and a deletion
path, so the consent/retention/deletion discipline is enforceable by code before
any synthesis is trusted (Field 18: minimize/pseudonymize; explicit recording
consent; deletion path).

These records are a *shape*, proven on synthetic examples. Real records require
approved participant contact (human gate) and simply populate the same fields.
"""

from dataclasses import dataclass, field
from enum import Enum


class ResearchConsentState(str, Enum):
    """Consent lifecycle for one discovery record."""

    GRANTED = "granted"      # participant consented to recording + this use
    PENDING = "pending"      # collected but not yet consented — unusable
    REFUSED = "refused"      # participant declined — unusable, exclude
    WITHDRAWN = "withdrawn"  # consent later withdrawn — unusable, exclude + delete


# States whose records may be used in synthesis. Everything else fails closed.
USABLE_CONSENT_STATES = frozenset({ResearchConsentState.GRANTED})


@dataclass(frozen=True)
class ResearchNote:
    """One pseudonymized discovery record."""

    note_id: str
    participant_pseudonym: str
    consent_state: ResearchConsentState
    recorded_at: str
    retention_until: str | None
    deletion_path: bool
    primary_job: str = ""
    pain_points: tuple[str, ...] = ()
    observed_behaviors: tuple[str, ...] = ()
    quotes: tuple[str, ...] = ()
    contradicts: tuple[str, ...] = ()  # note_ids this record conflicts with
    schema: str = "drakotune.discovery_note"
    schema_version: str = "1.0.0"

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "note_id": self.note_id,
            "participant_pseudonym": self.participant_pseudonym,
            "consent_state": self.consent_state.value,
            "recorded_at": self.recorded_at,
            "retention_until": self.retention_until,
            "deletion_path": self.deletion_path,
            "primary_job": self.primary_job,
            "pain_points": list(self.pain_points),
            "observed_behaviors": list(self.observed_behaviors),
            "quotes": list(self.quotes),
            "contradicts": list(self.contradicts),
        }

    def is_within_retention(self, at_time: str) -> bool:
        """True if the record has not passed its retention deadline."""
        return self.retention_until is None or at_time < self.retention_until
