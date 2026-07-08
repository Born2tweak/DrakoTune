"""Decision records for the DrakoTune decision engine.

A DecisionRecord captures one deterministic ruling — what was allowed or blocked,
why, and on what evidence. A SafetyDecision is the aggregate produced by the
safety-rules layer (M07): it gates processing, enhancement, and positive gain
before any adaptive DSP is considered.

These records are the audit trail behind "every action must be explainable".
"""

from dataclasses import dataclass, field

DECISION_POLICY_VERSION = "0.1.0"  # safety rules v1

# Decision targets — the things a rule can gate.
TARGET_PROCESSING = "processing"
TARGET_ENHANCEMENT = "enhancement"
TARGET_POSITIVE_GAIN = "positive_gain"

# Outcomes.
OUTCOME_ALLOW = "allow"
OUTCOME_BLOCK = "block"
OUTCOME_WARN = "warn"


@dataclass(frozen=True)
class DecisionRecord:
    """One deterministic ruling with its rationale and evidence."""

    rule: str
    outcome: str  # allow | block | warn
    target: str  # processing | enhancement | positive_gain
    reason: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "outcome": self.outcome,
            "target": self.target,
            "reason": self.reason,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class SafetyDecision:
    """Aggregate safety gate: what may proceed, plus the records explaining why."""

    processing_allowed: bool
    enhancement_allowed: bool
    positive_gain_allowed: bool
    blocked_targets: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    records: tuple[DecisionRecord, ...] = ()
    policy_version: str = DECISION_POLICY_VERSION

    def to_dict(self) -> dict:
        return {
            "processing_allowed": self.processing_allowed,
            "enhancement_allowed": self.enhancement_allowed,
            "positive_gain_allowed": self.positive_gain_allowed,
            "blocked_targets": list(self.blocked_targets),
            "warnings": list(self.warnings),
            "records": [r.to_dict() for r in self.records],
            "policy_version": self.policy_version,
        }

    def explain(self) -> str:
        """Human-readable summary of applied (allowed) and blocked rulings."""
        lines = [f"Safety decision (policy {self.policy_version}):"]
        for r in self.records:
            mark = {"allow": "OK  ", "block": "BLOCK", "warn": "WARN"}.get(r.outcome, "?")
            lines.append(f"  [{mark}] {r.target}: {r.reason}  ({r.rule})")
        return "\n".join(lines)
