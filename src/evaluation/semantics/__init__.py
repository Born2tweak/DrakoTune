"""Evidence semantics and claim quarantine (DT-45).

This package is the canonical evidence vocabulary for DrakoTune. It replaces the
legacy binary pass/fail evaluation semantics with a typed status/eligibility
model, enforces claim quarantine so unsupported claims cannot render as
approved, and maps legacy records forward with no silent pass.

See ``AURELIAN/05_ROADMAP/MILESTONES/DT_45_52.md`` (DT-45) and
``AURELIAN/03_CANONICAL/IMPLEMENTATION_SCHEMA_EXAMPLES.md``.
"""

from src.evaluation.semantics.canonical import (
    CONTENT_HASH_FIELD,
    canonical_bytes,
    content_hash,
    verify_hash,
)
from src.evaluation.semantics.claims import (
    CLAIM_INVENTORY_PATH,
    CLAIM_SCHEMA,
    CLAIM_SCHEMA_VERSION,
    Claim,
    ClaimQuarantineRegistry,
    load_default_registry,
)
from src.evaluation.semantics.enums import (
    APPROVED_CLAIM_STATUSES,
    NON_PASS_STATUSES,
    Applicability,
    ClaimClass,
    ClaimStatus,
    EligibilityState,
    EvidenceTier,
    GrantStatus,
    HumanGateCategory,
    MeasurementStatus,
    MilestoneStatus,
    ResultStatus,
    RightsPermission,
    parse_enum,
)
from src.evaluation.semantics.errors import (
    ErrorCode,
    QuarantineAction,
    SchemaValidationError,
    ValidationError,
)
from src.evaluation.semantics.legacy import map_legacy_evaluation
from src.evaluation.semantics.records import (
    SEMANTICS_SCHEMA,
    SEMANTICS_SCHEMA_VERSION,
    AxisResult,
    ClaimEligibility,
    EvidenceResult,
    Measurement,
    Producer,
    Uncertainty,
    max_claim_class_for_tier,
)

__all__ = [
    # enums
    "ResultStatus",
    "Applicability",
    "MeasurementStatus",
    "EvidenceTier",
    "RightsPermission",
    "GrantStatus",
    "ClaimClass",
    "ClaimStatus",
    "EligibilityState",
    "MilestoneStatus",
    "HumanGateCategory",
    "NON_PASS_STATUSES",
    "APPROVED_CLAIM_STATUSES",
    "parse_enum",
    # errors
    "ErrorCode",
    "QuarantineAction",
    "ValidationError",
    "SchemaValidationError",
    # canonical
    "canonical_bytes",
    "content_hash",
    "verify_hash",
    "CONTENT_HASH_FIELD",
    # records
    "EvidenceResult",
    "Measurement",
    "AxisResult",
    "ClaimEligibility",
    "Producer",
    "Uncertainty",
    "max_claim_class_for_tier",
    "SEMANTICS_SCHEMA",
    "SEMANTICS_SCHEMA_VERSION",
    # claims
    "Claim",
    "ClaimQuarantineRegistry",
    "load_default_registry",
    "CLAIM_INVENTORY_PATH",
    "CLAIM_SCHEMA",
    "CLAIM_SCHEMA_VERSION",
    # legacy mapping
    "map_legacy_evaluation",
]
