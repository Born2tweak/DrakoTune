"""Typed evidence records (DT-45).

The ``EvidenceResult`` is the typed replacement for the legacy
``EvaluationResult``'s ``passed_checks``/``failed_checks`` tuples. It carries the
distinctions the project must not blur: applicability, a nine-value status, an
evidence tier, per-metric measurement status, per-axis outcomes (including
collateral harm), provenance, and a separate claim-eligibility map.

DT-45 owns the *shape* and its invariants. DT-48 (Multiaxis Verdict Engine)
owns the adjudication rules that populate axes from measurements. This module
therefore validates structure and cross-field consistency but does not itself
decide clinical verdicts beyond failing closed.
"""

from dataclasses import dataclass, field

from src.evaluation.semantics.canonical import content_hash
from src.evaluation.semantics.enums import (
    APPROVED_CLAIM_STATUSES,  # noqa: F401  (re-exported for consumers)
    Applicability,
    ClaimClass,
    EligibilityState,
    EvidenceTier,
    MeasurementStatus,
    ResultStatus,
    parse_enum,
)
from src.evaluation.semantics.errors import (
    ErrorCode,
    QuarantineAction,
    SchemaValidationError,
    ValidationError,
)

SEMANTICS_SCHEMA = "drakotune.evidence_result"
SEMANTICS_SCHEMA_VERSION = "2.0.0"

# Highest claim class each evidence tier can support on its own. Claim
# eligibility can never exceed this — synthetic/regression evidence is
# engineering-only. (Quality spec: "Internal/synthetic evidence -> engineering
# eligibility only.")
_MAX_CLASS_FOR_TIER: dict[EvidenceTier, ClaimClass] = {
    EvidenceTier.T0_UNIT_SAFETY: ClaimClass.ENGINEERING,
    EvidenceTier.T1_SYNTHETIC_REGRESSION: ClaimClass.ENGINEERING,
    EvidenceTier.T2_HELD_OUT_REAL_DATA: ClaimClass.BOUNDED_PERFORMANCE,
    EvidenceTier.T3_INDEPENDENT_LISTENING: ClaimClass.INDEPENDENT_PERCEPTUAL,
    EvidenceTier.T4_REPLICATED_PRODUCT_EVIDENCE: ClaimClass.PRODUCT_GENERALIZED,
}

_CLASS_RANK: dict[ClaimClass, int] = {
    ClaimClass.ENGINEERING: 0,
    ClaimClass.BOUNDED_PERFORMANCE: 1,
    ClaimClass.INDEPENDENT_PERCEPTUAL: 2,
    ClaimClass.PRODUCT_GENERALIZED: 3,
}

# Canonical outcome-axis names (Quality Target spec).
AXIS_SIGNAL_SAFETY = "signal_safety"
AXIS_TARGET_EFFICACY = "target_efficacy"
AXIS_COLLATERAL_HARM = "collateral_harm"
AXIS_INTENT_PRESERVATION = "intent_preservation"
AXIS_PERCEPTUAL_OUTCOME = "perceptual_outcome"
AXIS_CONFIDENCE_APPLICABILITY = "confidence_applicability"
AXIS_OPERATIONAL = "operational"

# Axis statuses that forbid an overall ``passed``.
_AXIS_BLOCKS_PASS = frozenset(
    {
        ResultStatus.FAILED,
        ResultStatus.UNSAFE,
        ResultStatus.HARMFUL_TRADEOFF,
        ResultStatus.INDETERMINATE,
        ResultStatus.ERROR,
        ResultStatus.QUARANTINED,
    }
)


@dataclass(frozen=True)
class Uncertainty:
    """How a measurement's uncertainty was (or was not) established."""

    method: str = "not_applicable_deterministic_fixture"
    lower: float | None = None
    upper: float | None = None

    def to_dict(self) -> dict:
        return {"method": self.method, "lower": self.lower, "upper": self.upper}

    @classmethod
    def from_dict(cls, d: dict) -> "Uncertainty":
        return cls(
            method=d.get("method", "unknown"),
            lower=d.get("lower"),
            upper=d.get("upper"),
        )


@dataclass(frozen=True)
class Measurement:
    """One metric's outcome, with its own applicability and status."""

    metric_id: str
    registry_version: str = "unregistered"
    status: MeasurementStatus = MeasurementStatus.SUCCEEDED
    applicability: Applicability = Applicability.UNKNOWN
    baseline: float | None = None
    treatment: float | None = None
    effect: float | None = None
    role: str = "primary"
    uncertainty: Uncertainty = field(default_factory=Uncertainty)
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "registry_version": self.registry_version,
            "status": self.status.value,
            "applicability": self.applicability.value,
            "baseline": self.baseline,
            "treatment": self.treatment,
            "effect": self.effect,
            "role": self.role,
            "uncertainty": self.uncertainty.to_dict(),
            "reasons": list(self.reasons),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Measurement":
        return cls(
            metric_id=d["metric_id"],
            registry_version=d.get("registry_version", "unregistered"),
            status=parse_enum(MeasurementStatus, d.get("status", "not_applicable")),
            applicability=parse_enum(Applicability, d.get("applicability", "unknown")),
            baseline=d.get("baseline"),
            treatment=d.get("treatment"),
            effect=d.get("effect"),
            role=d.get("role", "primary"),
            uncertainty=Uncertainty.from_dict(d.get("uncertainty", {})),
            reasons=tuple(d.get("reasons", ())),
        )


@dataclass(frozen=True)
class AxisResult:
    """Typed outcome for one quality axis."""

    status: ResultStatus
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {"status": self.status.value, "reasons": list(self.reasons)}

    @classmethod
    def from_dict(cls, d: dict) -> "AxisResult":
        return cls(
            status=parse_enum(ResultStatus, d["status"]),
            reasons=tuple(d.get("reasons", ())),
        )


@dataclass(frozen=True)
class ClaimEligibility:
    """Which claim classes the evidence supports, with reasons.

    Absent classes default to ineligible. Eligibility is a separate axis from
    measurement outcome and can never exceed the evidence tier.
    """

    classes: dict[ClaimClass, EligibilityState] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()

    def state(self, claim_class: ClaimClass) -> EligibilityState:
        return self.classes.get(claim_class, EligibilityState.INELIGIBLE)

    def is_eligible(self, claim_class: ClaimClass) -> bool:
        return self.state(claim_class) is EligibilityState.ELIGIBLE

    def to_dict(self) -> dict:
        out: dict = {c.value: self.state(c).value for c in ClaimClass}
        out["reasons"] = list(self.reasons)
        return out

    @classmethod
    def from_dict(cls, d: dict) -> "ClaimEligibility":
        classes = {
            c: parse_enum(EligibilityState, d[c.value])
            for c in ClaimClass
            if c.value in d
        }
        return cls(classes=classes, reasons=tuple(d.get("reasons", ())))


@dataclass(frozen=True)
class Producer:
    """Provenance: what code/build/config produced this evidence."""

    code_commit: str = "unknown"
    build_id: str = "unknown"
    configuration_id: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "code_commit": self.code_commit,
            "build_id": self.build_id,
            "configuration_id": self.configuration_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Producer":
        return cls(
            code_commit=d.get("code_commit", "unknown"),
            build_id=d.get("build_id", "unknown"),
            configuration_id=d.get("configuration_id", "unknown"),
        )


def max_claim_class_for_tier(tier: EvidenceTier) -> ClaimClass:
    return _MAX_CLASS_FOR_TIER[tier]


def _rfc3339_valid(ts: str) -> bool:
    """Lightweight RFC 3339 check: requires explicit Z or +/-offset, UTC-safe."""
    from datetime import datetime

    if not isinstance(ts, str) or not ts:
        return False
    candidate = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return parsed.tzinfo is not None


@dataclass(frozen=True)
class EvidenceResult:
    """A typed evaluation result. Immutable; corrections append a new record."""

    result_id: str
    created_at: str
    status: ResultStatus
    applicability: Applicability
    evidence_tier: EvidenceTier
    task: dict = field(default_factory=dict)
    producer: Producer = field(default_factory=Producer)
    measurements: tuple[Measurement, ...] = ()
    axes: dict[str, AxisResult] = field(default_factory=dict)
    claim_eligibility: ClaimEligibility = field(default_factory=ClaimEligibility)
    reasons: tuple[str, ...] = ()
    schema: str = SEMANTICS_SCHEMA
    schema_version: str = SEMANTICS_SCHEMA_VERSION

    def to_dict(self, *, with_hash: bool = True) -> dict:
        payload = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "result_id": self.result_id,
            "created_at": self.created_at,
            "status": self.status.value,
            "applicability": self.applicability.value,
            "evidence_tier": self.evidence_tier.value,
            "task": dict(self.task),
            "producer": self.producer.to_dict(),
            "measurements": [m.to_dict() for m in self.measurements],
            "axes": {name: ax.to_dict() for name, ax in sorted(self.axes.items())},
            "claim_eligibility": self.claim_eligibility.to_dict(),
            "reasons": list(self.reasons),
        }
        if with_hash:
            payload["content_hash"] = content_hash(payload)
        return payload

    @classmethod
    def from_dict(cls, d: dict) -> "EvidenceResult":
        return cls(
            result_id=d["result_id"],
            created_at=d["created_at"],
            status=parse_enum(ResultStatus, d["status"]),
            applicability=parse_enum(Applicability, d["applicability"]),
            evidence_tier=parse_enum(EvidenceTier, d["evidence_tier"]),
            task=dict(d.get("task", {})),
            producer=Producer.from_dict(d.get("producer", {})),
            measurements=tuple(Measurement.from_dict(m) for m in d.get("measurements", [])),
            axes={name: AxisResult.from_dict(ax) for name, ax in d.get("axes", {}).items()},
            claim_eligibility=ClaimEligibility.from_dict(d.get("claim_eligibility", {})),
            reasons=tuple(d.get("reasons", ())),
            schema=d.get("schema", SEMANTICS_SCHEMA),
            schema_version=d.get("schema_version", SEMANTICS_SCHEMA_VERSION),
        )

    def content_hash(self) -> str:
        return content_hash(self.to_dict(with_hash=False))

    def validate(self) -> list[ValidationError]:
        """Return structural + cross-field validation errors (empty if valid)."""
        errors: list[ValidationError] = []

        def err(code: ErrorCode, path: str, msg: str, qa: QuarantineAction = QuarantineAction.REJECT) -> None:
            errors.append(
                ValidationError(
                    error_code=code,
                    field_path=path,
                    message=msg,
                    schema=self.schema,
                    schema_version=self.schema_version,
                    record_id=self.result_id or None,
                    quarantine_action=qa,
                )
            )

        if self.schema_version != SEMANTICS_SCHEMA_VERSION:
            err(
                ErrorCode.UNSUPPORTED_SCHEMA_VERSION,
                "schema_version",
                f"expected {SEMANTICS_SCHEMA_VERSION}, got {self.schema_version!r}",
            )
        if not self.result_id:
            err(ErrorCode.INVALID_IDENTITY, "result_id", "result_id must be a non-empty string")
        if not _rfc3339_valid(self.created_at):
            err(
                ErrorCode.INVALID_TIMESTAMP,
                "created_at",
                "created_at must be RFC 3339 with explicit Z or offset",
            )

        # Non-finite numeric guard across measurements.
        for i, m in enumerate(self.measurements):
            for fname in ("baseline", "treatment", "effect"):
                v = getattr(m, fname)
                if isinstance(v, float):
                    import math

                    if not math.isfinite(v):
                        err(
                            ErrorCode.NONFINITE_NUMBER,
                            f"measurements[{i}].{fname}",
                            "non-finite numbers are forbidden",
                            QuarantineAction.QUARANTINE,
                        )

        # An overall passed cannot coexist with a blocking axis or non-applicable input.
        if self.status is ResultStatus.PASSED:
            if self.applicability is not Applicability.APPLICABLE:
                err(
                    ErrorCode.CLAIM_EVIDENCE_INELIGIBLE,
                    "status",
                    "passed requires applicability=applicable",
                    QuarantineAction.QUARANTINE,
                )
            for name, ax in self.axes.items():
                if ax.status in _AXIS_BLOCKS_PASS:
                    err(
                        ErrorCode.CLAIM_EVIDENCE_INELIGIBLE,
                        f"axes.{name}",
                        f"overall passed contradicts axis status {ax.status.value}",
                        QuarantineAction.QUARANTINE,
                    )

        # Claim eligibility can never exceed the evidence tier.
        ceiling = _CLASS_RANK[max_claim_class_for_tier(self.evidence_tier)]
        for claim_class, state in self.claim_eligibility.classes.items():
            if state is EligibilityState.ELIGIBLE and _CLASS_RANK[claim_class] > ceiling:
                err(
                    ErrorCode.CLAIM_EVIDENCE_INELIGIBLE,
                    f"claim_eligibility.{claim_class.value}",
                    f"{claim_class.value} exceeds tier {self.evidence_tier.value}",
                    QuarantineAction.QUARANTINE,
                )
            # Eligibility also requires an overall passed outcome.
            if state is EligibilityState.ELIGIBLE and self.status is not ResultStatus.PASSED:
                err(
                    ErrorCode.CLAIM_EVIDENCE_INELIGIBLE,
                    f"claim_eligibility.{claim_class.value}",
                    f"eligible claim requires passed status, got {self.status.value}",
                    QuarantineAction.QUARANTINE,
                )
        return errors

    def validated(self) -> "EvidenceResult":
        """Return self if valid, else raise ``SchemaValidationError``."""
        errs = self.validate()
        if errs:
            raise SchemaValidationError(tuple(errs))
        return self
