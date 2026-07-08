"""EvaluationResult: before/after measurement of a processed vocal.

Evaluation must not confuse louder with better. It stores raw before/after
metrics, their deltas, and which checks passed or failed. The evaluation engine
(M10) populates it; this type only defines the shape.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvaluationResult:
    """Before/after metrics, deltas, and pass/fail checks for one processing run."""

    id: str
    before_metrics: dict = field(default_factory=dict)
    after_metrics: dict = field(default_factory=dict)
    deltas: dict = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    passed_checks: tuple[str, ...] = ()
    failed_checks: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "before_metrics": dict(self.before_metrics),
            "after_metrics": dict(self.after_metrics),
            "deltas": dict(self.deltas),
            "warnings": list(self.warnings),
            "passed_checks": list(self.passed_checks),
            "failed_checks": list(self.failed_checks),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EvaluationResult":
        return cls(
            id=d["id"],
            before_metrics=dict(d.get("before_metrics", {})),
            after_metrics=dict(d.get("after_metrics", {})),
            deltas=dict(d.get("deltas", {})),
            warnings=tuple(d.get("warnings", ())),
            passed_checks=tuple(d.get("passed_checks", ())),
            failed_checks=tuple(d.get("failed_checks", ())),
        )
