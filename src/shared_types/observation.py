"""Observation: a measurement-backed statement of fact.

Observations carry no interpretation. "Band energy ratio in 2.5-6kHz is 0.4"
is an observation; "the vocal is harsh" is an interpretation (see
interpretation.py). Keeping them separate is a non-negotiable scientific rule.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Observation:
    """A single measured fact with provenance and confidence."""

    id: str
    metric: str
    value: float
    units: str
    window: str = "full"  # "full", "frame", or e.g. "0.0-1.0s"
    confidence: float = 1.0
    evidence: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "metric": self.metric,
            "value": self.value,
            "units": self.units,
            "window": self.window,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Observation":
        return cls(
            id=d["id"],
            metric=d["metric"],
            value=float(d["value"]),
            units=d["units"],
            window=d.get("window", "full"),
            confidence=float(d.get("confidence", 1.0)),
            evidence=d.get("evidence", ""),
        )
