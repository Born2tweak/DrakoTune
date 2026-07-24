"""Immutable listening-protocol and response schema (DT-56).

Supersedes the legacy M24/M43 CSV listening records with identity-safe, tie-aware,
blinded, correction-linked types. The design encodes the lessons of N-002..N-006
structurally:

- **N-002** (row count is not sample size): responses carry a pseudonymous
  ``listener_id``; the independent unit is the listener, enforced in ``integrity``.
- **N-003** (clean-vocal harm can pass): the outcome vocabulary keeps
  original-preference as a first-class signal, never collapsed into "not processed".
- **N-004** (ties disappear): ``TIE_NO_DIFFERENCE`` is an explicit outcome.
- **N-005** (panels pooled): every response names its ``panel``; pooling is refused
  downstream.
- **N-006** (side/order bias): the blinded ``Assignment`` records the A/B→treatment
  map and play order separately from the response, so responses live in A/B space
  and can only be resolved to treatment via the assignment (no treatment leak).

Out of scope (Field 8): statistical thresholds, recruitment, confirmatory
execution. This is the schema + integrity layer only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Side(str, Enum):
    A = "A"
    B = "B"


class Treatment(str, Enum):
    """What a side actually is. Kept in the Assignment, never in the raw Response."""

    ORIGINAL = "original"
    PROCESSED = "processed"


class ResponseOutcome(str, Enum):
    """Explicit outcomes in blinded A/B space. Ties and artifacts are first-class."""

    PREFER_A = "prefer_a"
    PREFER_B = "prefer_b"
    TIE_NO_DIFFERENCE = "tie_no_difference"   # N-004: never dropped
    BOTH_ARTIFACTS = "both_artifacts"
    CANNOT_TELL = "cannot_tell"


class Panel(str, Enum):
    """Listener strata; never pooled without a prespecified estimand (N-005)."""

    EXPERT_ENGINEER = "expert_engineer"
    TRAINED_LISTENER = "trained_listener"
    TARGET_USER = "target_user"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ListenerRef:
    """Pseudonymous listener identity. No PII; real identity is stored separately."""

    listener_id: str
    panel: Panel = Panel.UNKNOWN

    def __post_init__(self) -> None:
        if not self.listener_id or not self.listener_id.strip():
            raise ValueError("listener_id must be non-empty")


@dataclass(frozen=True)
class Trial:
    """One blinded comparison item for one clip."""

    trial_id: str
    clip_id: str
    stratum_ref: str = ""   # optional link to a DT-54 stratum assignment


@dataclass(frozen=True)
class Assignment:
    """Blinded side→treatment map + play order for one (trial, listener).

    Kept separate from the Response so raw responses never leak which side was
    processed (N-006). ``first_played`` records play order for order-bias checks.
    """

    trial_id: str
    listener_id: str
    side_to_treatment: dict[Side, Treatment]
    first_played: Side

    def __post_init__(self) -> None:
        if set(self.side_to_treatment) != {Side.A, Side.B}:
            raise ValueError("assignment must map exactly sides A and B")
        if set(self.side_to_treatment.values()) != {Treatment.ORIGINAL, Treatment.PROCESSED}:
            raise ValueError("assignment must cover both treatments exactly once")

    def treatment_of(self, side: Side) -> Treatment:
        return self.side_to_treatment[side]

    def processed_side(self) -> Side:
        for side, t in self.side_to_treatment.items():
            if t is Treatment.PROCESSED:
                return side
        raise AssertionError("unreachable: validated in __post_init__")


@dataclass(frozen=True)
class Response:
    """One immutable listening response (blinded A/B space).

    ``response_key`` uniquely identifies the (trial, listener) slot; only one
    response per key may be *active* (integrity enforces this). Corrections do not
    mutate — they append a new Response whose ``supersedes`` names the prior key.
    """

    trial_id: str
    listener_id: str
    panel: Panel
    outcome: ResponseOutcome
    perceived_artifacts: bool = False
    timestamp: str = ""
    revision: int = 0
    supersedes_revision: int | None = None
    quarantined: bool = False
    quarantine_reason: str = ""
    source: str = "web"   # "web" | "legacy_import"

    @property
    def response_key(self) -> tuple[str, str]:
        return (self.trial_id, self.listener_id)


@dataclass(frozen=True)
class Protocol:
    """A named, versioned listening protocol: its trials, panels, and seed."""

    protocol_id: str
    version: str
    trials: tuple[Trial, ...] = ()
    randomization_seed: int = 0
    panels: tuple[Panel, ...] = field(default_factory=lambda: (Panel.TARGET_USER,))

    def trial_ids(self) -> frozenset[str]:
        return frozenset(t.trial_id for t in self.trials)
