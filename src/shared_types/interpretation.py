"""Interpretation: a hypothesis about what observations mean.

An interpretation cites the observations that support and contradict it, so a
reader can trace every claim back to measured evidence. It never issues a
processing action — that is the decision engine's job (see decision.py).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Interpretation:
    """A hypothesis derived from one or more observations."""

    id: str
    issue: str  # named issue, e.g. "harshness"
    supporting_observation_ids: tuple[str, ...] = ()
    contradicting_observation_ids: tuple[str, ...] = ()
    confidence: float = 0.0
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "issue": self.issue,
            "supporting_observation_ids": list(self.supporting_observation_ids),
            "contradicting_observation_ids": list(self.contradicting_observation_ids),
            "confidence": self.confidence,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Interpretation":
        return cls(
            id=d["id"],
            issue=d["issue"],
            supporting_observation_ids=tuple(d.get("supporting_observation_ids", ())),
            contradicting_observation_ids=tuple(d.get("contradicting_observation_ids", ())),
            confidence=float(d.get("confidence", 0.0)),
            rationale=d.get("rationale", ""),
        )
