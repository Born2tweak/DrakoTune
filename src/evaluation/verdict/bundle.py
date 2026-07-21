"""Evaluation bundle inputs for the multiaxis verdict engine (DT-48).

A bundle is the typed input the verdict engine adjudicates: the declared task,
the per-metric measurements (each resolvable in the DT-47 registry), the
independent-unit counts, the evidence tier, the rights state, and — when a
listening study exists — a structured summary whose shape makes the known
listening exploits (duplicate rows, dropped ties, pooled panels, side bias)
detectable rather than hidden.

These types carry no adjudication logic; ``engine.adjudicate`` applies the rules.
"""

from dataclasses import dataclass, field

from src.evaluation.semantics.enums import (
    Applicability,
    EvidenceTier,
    RightsPermission,
    parse_enum,
)


@dataclass(frozen=True)
class MetricObservation:
    """One measured metric in a bundle.

    ``effect`` is treatment minus baseline. ``is_target`` marks the metric the
    task tried to move; every other defect metric is a collateral-harm candidate.
    """

    metric_id: str
    effect: float | None = None
    is_target: bool = False
    errored: bool = False  # measurement could not be computed (NaN/missing)

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "effect": self.effect,
            "is_target": self.is_target,
            "errored": self.errored,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MetricObservation":
        return cls(
            metric_id=d["metric_id"],
            effect=d.get("effect"),
            is_target=bool(d.get("is_target", False)),
            errored=bool(d.get("errored", False)),
        )


@dataclass(frozen=True)
class PanelCounts:
    """Choice counts for one listener panel, ties first-class."""

    a_wins: int = 0
    b_wins: int = 0
    ties: int = 0
    cannot_judge: int = 0
    technical_failure: int = 0

    @property
    def decided(self) -> int:
        return self.a_wins + self.b_wins

    @property
    def total(self) -> int:
        return self.a_wins + self.b_wins + self.ties + self.cannot_judge + self.technical_failure

    def to_dict(self) -> dict:
        return {
            "a_wins": self.a_wins,
            "b_wins": self.b_wins,
            "ties": self.ties,
            "cannot_judge": self.cannot_judge,
            "technical_failure": self.technical_failure,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PanelCounts":
        return cls(
            a_wins=int(d.get("a_wins", 0)),
            b_wins=int(d.get("b_wins", 0)),
            ties=int(d.get("ties", 0)),
            cannot_judge=int(d.get("cannot_judge", 0)),
            technical_failure=int(d.get("technical_failure", 0)),
        )


@dataclass(frozen=True)
class ListeningSummary:
    """A structured listening study summary.

    The fields exist precisely so the verdict engine can refuse the exploits in
    NEGATIVE_RESULTS.md N-002..N-006.
    """

    panels: dict[str, PanelCounts] = field(default_factory=dict)
    distinct_listeners: int = 0
    distinct_items: int = 0
    total_rows: int = 0
    processed_side: str = "a"           # which blinded side held the processed audio
    assignment_balanced: bool = False   # side/order counterbalanced
    equivalence_prespecified: bool = False  # a preregistered equivalence margin exists
    cancelled: bool = False             # panel/session cancellation

    def counted_rows(self) -> int:
        return sum(p.total for p in self.panels.values())

    def to_dict(self) -> dict:
        return {
            "panels": {k: v.to_dict() for k, v in self.panels.items()},
            "distinct_listeners": self.distinct_listeners,
            "distinct_items": self.distinct_items,
            "total_rows": self.total_rows,
            "processed_side": self.processed_side,
            "assignment_balanced": self.assignment_balanced,
            "equivalence_prespecified": self.equivalence_prespecified,
            "cancelled": self.cancelled,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ListeningSummary":
        return cls(
            panels={k: PanelCounts.from_dict(v) for k, v in d.get("panels", {}).items()},
            distinct_listeners=int(d.get("distinct_listeners", 0)),
            distinct_items=int(d.get("distinct_items", 0)),
            total_rows=int(d.get("total_rows", 0)),
            processed_side=d.get("processed_side", "a"),
            assignment_balanced=bool(d.get("assignment_balanced", False)),
            equivalence_prespecified=bool(d.get("equivalence_prespecified", False)),
            cancelled=bool(d.get("cancelled", False)),
        )


@dataclass(frozen=True)
class EvaluationBundle:
    """Typed input to the verdict engine."""

    bundle_id: str
    intent: str  # preserve | repair | control | fit | style
    applicability: Applicability
    evidence_tier: EvidenceTier
    measurements: tuple[MetricObservation, ...] = ()
    signal_safe: bool = True            # signal-integrity hard gate result
    rights_state: RightsPermission = RightsPermission.UNKNOWN
    listening: ListeningSummary | None = None
    result_id: str | None = None        # DT-46 identity, when available

    def to_dict(self) -> dict:
        return {
            "bundle_id": self.bundle_id,
            "intent": self.intent,
            "applicability": self.applicability.value,
            "evidence_tier": self.evidence_tier.value,
            "measurements": [m.to_dict() for m in self.measurements],
            "signal_safe": self.signal_safe,
            "rights_state": self.rights_state.value,
            "listening": self.listening.to_dict() if self.listening else None,
            "result_id": self.result_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EvaluationBundle":
        return cls(
            bundle_id=d["bundle_id"],
            intent=d["intent"],
            applicability=parse_enum(Applicability, d["applicability"]),
            evidence_tier=parse_enum(EvidenceTier, d["evidence_tier"]),
            measurements=tuple(MetricObservation.from_dict(m) for m in d.get("measurements", [])),
            signal_safe=bool(d.get("signal_safe", True)),
            rights_state=parse_enum(RightsPermission, d.get("rights_state", "unknown")),
            listening=ListeningSummary.from_dict(d["listening"]) if d.get("listening") else None,
            result_id=d.get("result_id"),
        )
