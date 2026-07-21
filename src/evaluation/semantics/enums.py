"""Canonical evidence-semantics enums (DT-45).

This module is the single source of truth for the DrakoTune evidence
vocabulary. It replaces the ambiguous binary pass/fail semantics of the legacy
``EvaluationResult`` with typed states that keep the distinctions the project
must never blur:

- ``unknown``, ``not_applicable``, ``error``, and ``indeterminate`` are distinct
  (a missing measurement is never a pass, and an inapplicable metric is never a
  fail).
- A hard safety or collateral-harm failure cannot be averaged away into a pass.
- Claim eligibility is a separate axis from measurement outcome.

Values are taken verbatim from
``AURELIAN/03_CANONICAL/IMPLEMENTATION_SCHEMA_EXAMPLES.md`` ("Canonical enums").
Unknown enum values are schema errors, never silent aliases — see
:func:`parse_enum`.
"""

from enum import Enum
from typing import TypeVar


class ResultStatus(str, Enum):
    """Outcome of a result or multi-axis verdict.

    The nine canonical statuses. ``passed`` is reserved for an applicable,
    successful, harm-free outcome; every other state names *why* a pass was not
    earned rather than collapsing to a bare ``failed``.
    """

    PASSED = "passed"
    FAILED = "failed"
    UNSAFE = "unsafe"
    HARMFUL_TRADEOFF = "harmful_tradeoff"
    INDETERMINATE = "indeterminate"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"
    CANCELLED = "cancelled"
    QUARANTINED = "quarantined"


class Applicability(str, Enum):
    """Whether a measurement/task can be interpreted at all."""

    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"
    OUT_OF_DOMAIN = "out_of_domain"
    MISSING_REQUIRED_REFERENCE = "missing_required_reference"
    INVALID_INPUT = "invalid_input"


class MeasurementStatus(str, Enum):
    """Outcome of computing a single metric."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"
    NOT_APPLICABLE = "not_applicable"
    QUARANTINED = "quarantined"


class EvidenceTier(str, Enum):
    """Strength ladder for evidence. Higher tiers require more.

    Claim eligibility can never exceed the evidence tier that produced it;
    synthetic/regression evidence supports engineering statements only.
    """

    T0_UNIT_SAFETY = "T0_unit_safety"
    T1_SYNTHETIC_REGRESSION = "T1_synthetic_regression"
    T2_HELD_OUT_REAL_DATA = "T2_held_out_real_data"
    T3_INDEPENDENT_LISTENING = "T3_independent_listening"
    T4_REPLICATED_PRODUCT_EVIDENCE = "T4_replicated_product_evidence"


class RightsPermission(str, Enum):
    """Purpose-specific rights state for an asset/use.

    DT-45 defines the vocabulary only; DT-49 builds the enforcement graph.
    ``unknown`` fails closed — it never authorizes use or supports a claim.
    """

    ALLOWED = "allowed"
    PROHIBITED = "prohibited"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class GrantStatus(str, Enum):
    """Lifecycle of a rights grant (vocabulary; DT-49 enforces)."""

    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"
    SUPERSEDED = "superseded"
    QUARANTINED = "quarantined"


class ClaimClass(str, Enum):
    """The four claim elevation classes.

    engineering -> bounded_performance -> independent_perceptual ->
    product_generalized. Each elevation requires strictly more evidence.
    """

    ENGINEERING = "engineering"
    BOUNDED_PERFORMANCE = "bounded_performance"
    INDEPENDENT_PERCEPTUAL = "independent_perceptual"
    PRODUCT_GENERALIZED = "product_generalized"


class ClaimStatus(str, Enum):
    """Lifecycle of a claim. Only approved_* statuses may render as approved."""

    CANDIDATE = "candidate"
    APPROVED_INTERNAL = "approved_internal"
    APPROVED_PUBLIC = "approved_public"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    RETRACTED = "retracted"
    REJECTED = "rejected"


class EligibilityState(str, Enum):
    """Whether a claim class is supported by the evidence at hand."""

    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"


class ExperimentStatus(str, Enum):
    """Lifecycle of an experiment package (vocabulary; DT-56/57 enforce)."""

    DRAFT = "draft"
    FROZEN = "frozen"
    COLLECTING = "collecting"
    ANALYSIS_LOCKED = "analysis_locked"
    COMPLETE = "complete"
    INVALIDATED = "invalidated"
    CANCELLED = "cancelled"
    QUARANTINED = "quarantined"


class MilestoneStatus(str, Enum):
    """Allowed milestone statuses (mirrors MILESTONE_REGISTRY.yaml)."""

    PROPOSED = "proposed"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETE = "complete"
    FAILED_EXPERIMENT = "failed_experiment"
    SUPERSEDED = "superseded"


class HumanGateCategory(str, Enum):
    """Consequential actions reserved for human authority."""

    SPENDING = "spending"
    PEOPLE_CONTACT = "people_contact"
    CONTRACT_CONSENT = "contract_consent"
    RIGHTS_LEGAL_PRIVACY = "rights_legal_privacy"
    CREDENTIALS_IDENTITY = "credentials_identity"
    CONFIRMATORY_METHOD_FREEZE = "confirmatory_method_freeze"
    UNBLINDING = "unblinding"
    MATERIAL_AUDIO_PROMOTION = "material_audio_promotion"
    LICENSE_LEGAL = "license_legal"
    DISTRIBUTION_POSTURE = "distribution_posture"
    PUBLIC_CLAIMS = "public_claims"
    SIGNING_DISTRIBUTION = "signing_distribution"
    PRODUCTION_CHANGE = "production_change"
    PRODUCTION_RELEASE = "production_release"
    PRODUCT_SCOPE = "product_scope"
    IRREVERSIBLE_DELETION = "irreversible_deletion"


# Statuses that can never carry an unqualified quality pass. Used by the legacy
# mapper and verdict consumers to fail closed.
NON_PASS_STATUSES = frozenset(
    {
        ResultStatus.FAILED,
        ResultStatus.UNSAFE,
        ResultStatus.HARMFUL_TRADEOFF,
        ResultStatus.INDETERMINATE,
        ResultStatus.NOT_APPLICABLE,
        ResultStatus.ERROR,
        ResultStatus.CANCELLED,
        ResultStatus.QUARANTINED,
    }
)

# Claim statuses that render as "approved" on any surface.
APPROVED_CLAIM_STATUSES = frozenset(
    {ClaimStatus.APPROVED_INTERNAL, ClaimStatus.APPROVED_PUBLIC}
)


_E = TypeVar("_E", bound=Enum)


def parse_enum(enum_cls: type[_E], value: object) -> _E:
    """Parse ``value`` into ``enum_cls`` or raise ``ValueError``.

    Unknown values are schema errors, not aliases. The caller is expected to
    translate the ``ValueError`` into a canonical ``unknown_enum`` validation
    error. ``None`` is rejected here so "missing" is handled explicitly by the
    caller as ``missing_required_field`` rather than being coerced.
    """
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)  # type: ignore[arg-type]
    except ValueError as exc:
        allowed = ", ".join(e.value for e in enum_cls)
        raise ValueError(
            f"unknown_enum: {value!r} is not a valid {enum_cls.__name__} "
            f"(allowed: {allowed})"
        ) from exc
