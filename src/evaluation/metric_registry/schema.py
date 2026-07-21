"""Metric applicability card schema (DT-47).

Every objective/listening measure registers *when it is valid* and *what it
cannot claim*. A card separates a measurement from a quality verdict: loudness
and true-peak are safety/comparability measures, never artistic-quality
verdicts; full-reference metrics are valid only where a valid reference exists;
domain-limited metrics are inapplicable out of domain.

A threshold is recorded only when it cites evidence or a setting experiment.
Unknown perceptual thresholds are left **unset** — the registry never invents a
pass rule (Quality Target spec: "A missing threshold produces abstention or a
threshold-setting milestone, never an improvised pass rule.").
"""

from dataclasses import dataclass, field
from enum import Enum

from src.evaluation.semantics.canonical import content_hash
from src.evaluation.semantics.enums import Applicability, parse_enum


class MetricRole(str, Enum):
    """What kind of evidence a metric can contribute."""

    SIGNAL_SAFETY = "signal_safety"          # decode/finite/clip/peak/DC/duration
    COMPARABILITY = "comparability"          # loudness/level matching, not quality
    DEFECT_EVIDENCE = "defect_evidence"      # targeted recording-defect indicators
    REFERENCE = "reference"                  # full-reference comparison metrics
    PERCEPTION = "perception"                # listener-derived measures
    ARTISTIC_INTENT = "artistic_intent"      # style/identity descriptors
    DESCRIPTIVE = "descriptive"              # neutral descriptors, no verdict


class ReferenceRequirement(str, Enum):
    NONE = "none"
    CLEAN_REFERENCE = "clean_reference"       # needs a known-clean reference
    ALIGNED_PAIR = "aligned_pair"             # needs delay-aligned before/after


class ThresholdStatus(str, Enum):
    EVIDENCE_BACKED = "evidence_backed"          # cites a source/standard
    SETTING_EXPERIMENT = "setting_experiment"    # cites a threshold-setting run
    OPERATIONAL = "operational"                  # engineering guardrail, not quality
    UNSET = "unset_pending_listening_study"      # honestly unknown; no pass rule


METRIC_CARD_SCHEMA = "drakotune.metric_card"
METRIC_CARD_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class MetricCard:
    """One metric's applicability contract."""

    metric_id: str
    role: MetricRole
    unit: str
    direction: int                       # -1 lower better, +1 higher better, 0 none
    reference_requirement: ReferenceRequirement = ReferenceRequirement.NONE
    domain: tuple[str, ...] = ("vocal",)
    calibration_id: str = "uncalibrated"
    meaningful_threshold: float | None = None
    threshold_status: ThresholdStatus = ThresholdStatus.UNSET
    threshold_evidence: str | None = None
    uncertainty_method: str = "not_established"
    failure_modes: tuple[str, ...] = ()
    prohibited_interpretations: tuple[str, ...] = ()
    license: str = "first_party"
    registry_version: str = METRIC_CARD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        # Invariant: a non-operational, non-safety threshold value must cite
        # evidence; unset thresholds must not carry a value.
        if self.meaningful_threshold is not None and self.threshold_status is ThresholdStatus.UNSET:
            raise ValueError(
                f"{self.metric_id}: unset threshold must not carry a value"
            )
        if (
            self.meaningful_threshold is not None
            and self.threshold_status in (ThresholdStatus.EVIDENCE_BACKED, ThresholdStatus.SETTING_EXPERIMENT)
            and not self.threshold_evidence
        ):
            raise ValueError(
                f"{self.metric_id}: evidence-backed threshold requires threshold_evidence"
            )

    def can_support_quality_verdict(self) -> bool:
        """Only evidence/experiment-backed defect/perception/reference metrics
        may contribute to a quality verdict. Comparability, descriptive, and
        unset-threshold metrics cannot."""
        if self.role in (MetricRole.COMPARABILITY, MetricRole.DESCRIPTIVE):
            return False
        return self.threshold_status in (
            ThresholdStatus.EVIDENCE_BACKED,
            ThresholdStatus.SETTING_EXPERIMENT,
        )

    def applicability(self, *, has_reference: bool, in_domain: bool, calibration_fresh: bool) -> Applicability:
        """Decide whether this metric can be interpreted for the given input."""
        if not in_domain:
            return Applicability.OUT_OF_DOMAIN
        if self.reference_requirement in (
            ReferenceRequirement.CLEAN_REFERENCE,
            ReferenceRequirement.ALIGNED_PAIR,
        ) and not has_reference:
            return Applicability.MISSING_REQUIRED_REFERENCE
        if self.calibration_id != "uncalibrated" and not calibration_fresh:
            return Applicability.UNKNOWN  # stale calibration -> cannot interpret
        return Applicability.APPLICABLE

    def to_dict(self, *, with_hash: bool = True) -> dict:
        payload = {
            "schema": METRIC_CARD_SCHEMA,
            "schema_version": self.registry_version,
            "metric_id": self.metric_id,
            "role": self.role.value,
            "unit": self.unit,
            "direction": self.direction,
            "reference_requirement": self.reference_requirement.value,
            "domain": list(self.domain),
            "calibration_id": self.calibration_id,
            "meaningful_threshold": self.meaningful_threshold,
            "threshold_status": self.threshold_status.value,
            "threshold_evidence": self.threshold_evidence,
            "uncertainty_method": self.uncertainty_method,
            "failure_modes": list(self.failure_modes),
            "prohibited_interpretations": list(self.prohibited_interpretations),
            "license": self.license,
        }
        if with_hash:
            payload["content_hash"] = content_hash(payload)
        return payload

    @classmethod
    def from_dict(cls, d: dict) -> "MetricCard":
        return cls(
            metric_id=d["metric_id"],
            role=parse_enum(MetricRole, d["role"]),
            unit=d.get("unit", "ratio"),
            direction=int(d.get("direction", 0)),
            reference_requirement=parse_enum(
                ReferenceRequirement, d.get("reference_requirement", "none")
            ),
            domain=tuple(d.get("domain", ("vocal",))),
            calibration_id=d.get("calibration_id", "uncalibrated"),
            meaningful_threshold=d.get("meaningful_threshold"),
            threshold_status=parse_enum(ThresholdStatus, d.get("threshold_status", "unset_pending_listening_study")),
            threshold_evidence=d.get("threshold_evidence"),
            uncertainty_method=d.get("uncertainty_method", "not_established"),
            failure_modes=tuple(d.get("failure_modes", ())),
            prohibited_interpretations=tuple(d.get("prohibited_interpretations", ())),
            license=d.get("license", "first_party"),
            registry_version=d.get("schema_version", METRIC_CARD_SCHEMA_VERSION),
        )
