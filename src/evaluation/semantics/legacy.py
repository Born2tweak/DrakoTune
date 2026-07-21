"""Legacy evaluation -> typed evidence mapping (DT-45 compatibility layer).

The legacy ``EvaluationResult`` collapses everything into ``passed_checks`` /
``failed_checks`` tuples plus free-text warnings. This mapper reads those old
records without mutating them and produces a typed ``EvidenceResult`` under the
central rule of DT-45: **no silent pass**. A missing metric becomes
``not_applicable``; a non-finite metric becomes ``error``; a target benefit that
coexists with collateral harm becomes ``harmful_tradeoff``; conflicting outcomes
become ``indeterminate``. Synthetic/regression evidence supports engineering
eligibility only, and only when rights are known.
"""

import math
from datetime import datetime, timezone

from src.evaluation.semantics.enums import (
    Applicability,
    ClaimClass,
    EligibilityState,
    EvidenceTier,
    MeasurementStatus,
    ResultStatus,
)
from src.evaluation.semantics.records import (
    AXIS_COLLATERAL_HARM,
    AXIS_SIGNAL_SAFETY,
    AXIS_TARGET_EFFICACY,
    AxisResult,
    ClaimEligibility,
    EvidenceResult,
    Measurement,
    Producer,
)

# Warnings that indicate collateral harm (not merely a comparison caveat).
_HARM_WARNINGS = ("harshness_increased",)
_HARM_WARNING_PREFIXES = ("residual_after_processing:",)


def _has_nonfinite_metric(metrics: dict) -> bool:
    return any(isinstance(v, float) and not math.isfinite(v) for v in metrics.values())


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_harm(warnings: tuple[str, ...]) -> bool:
    for w in warnings:
        if w in _HARM_WARNINGS or any(w.startswith(p) for p in _HARM_WARNING_PREFIXES):
            return True
    return False


def map_legacy_evaluation(
    legacy,
    *,
    evidence_tier: EvidenceTier = EvidenceTier.T1_SYNTHETIC_REGRESSION,
    producer: Producer | None = None,
    rights_known: bool = False,
    created_at: str | None = None,
    result_id: str | None = None,
) -> EvidenceResult:
    """Map a legacy ``EvaluationResult`` to a typed ``EvidenceResult``.

    ``rights_known`` defaults to False so a mapped legacy result never claims
    eligibility on unknown rights. ``evidence_tier`` defaults to synthetic
    regression, which caps eligibility at the engineering class.
    """
    warnings = tuple(legacy.warnings)
    before = dict(legacy.before_metrics)
    after = dict(legacy.after_metrics)

    nonfinite = _has_nonfinite_metric(before) or _has_nonfinite_metric(after)
    clipping = "output_clipping" in warnings
    harm = _is_harm(warnings)
    has_pass = len(legacy.passed_checks) > 0
    has_fail = len(legacy.failed_checks) > 0
    conflicting = has_pass and has_fail

    # --- Axis: signal safety ---
    if clipping:
        safety = AxisResult(ResultStatus.UNSAFE, ("output_clipping",))
    elif nonfinite:
        safety = AxisResult(ResultStatus.ERROR, ("nonfinite_metric",))
    elif after:
        safety = AxisResult(ResultStatus.PASSED, ("finite_output_no_clipping_warning",))
    else:
        safety = AxisResult(ResultStatus.NOT_APPLICABLE, ("no_output_metrics",))

    # --- Axis: target efficacy ---
    if conflicting:
        efficacy = AxisResult(ResultStatus.INDETERMINATE, ("conflicting_check_outcomes",))
    elif has_pass:
        efficacy = AxisResult(ResultStatus.PASSED, tuple(legacy.passed_checks))
    elif has_fail:
        efficacy = AxisResult(ResultStatus.FAILED, tuple(legacy.failed_checks))
    else:
        efficacy = AxisResult(ResultStatus.NOT_APPLICABLE, ("no_targeted_objective_metric",))

    # --- Axis: collateral harm ---
    if harm:
        harm_reasons = tuple(
            w for w in warnings if w in _HARM_WARNINGS or w.startswith(_HARM_WARNING_PREFIXES)
        )
        collateral = AxisResult(ResultStatus.FAILED, harm_reasons or ("collateral_harm",))
    elif after:
        collateral = AxisResult(ResultStatus.PASSED, ("no_harm_warnings",))
    else:
        collateral = AxisResult(ResultStatus.NOT_APPLICABLE, ("no_output_metrics",))

    axes = {
        AXIS_SIGNAL_SAFETY: safety,
        AXIS_TARGET_EFFICACY: efficacy,
        AXIS_COLLATERAL_HARM: collateral,
    }

    # --- Overall status: fail closed, hard gates first ---
    if safety.status is ResultStatus.UNSAFE:
        status = ResultStatus.UNSAFE
    elif nonfinite:
        status = ResultStatus.ERROR
    elif efficacy.status is ResultStatus.INDETERMINATE:
        status = ResultStatus.INDETERMINATE
    elif efficacy.status is ResultStatus.PASSED and collateral.status is ResultStatus.FAILED:
        status = ResultStatus.HARMFUL_TRADEOFF
    elif efficacy.status is ResultStatus.PASSED and collateral.status is not ResultStatus.FAILED:
        status = ResultStatus.PASSED
    elif efficacy.status is ResultStatus.FAILED:
        status = ResultStatus.FAILED
    else:
        status = ResultStatus.NOT_APPLICABLE

    # --- Applicability ---
    if not after and not before:
        applicability = Applicability.INVALID_INPUT
    elif efficacy.status is ResultStatus.NOT_APPLICABLE and not has_fail:
        applicability = Applicability.NOT_APPLICABLE
    else:
        applicability = Applicability.APPLICABLE

    # --- Measurements from targeted deltas (self-describing status) ---
    measurements: list[Measurement] = []
    for label in legacy.passed_checks:
        measurements.append(
            Measurement(
                metric_id=label.split(":", 1)[0],
                status=MeasurementStatus.SUCCEEDED,
                applicability=Applicability.APPLICABLE,
                role="target_efficacy",
                reasons=(label,),
            )
        )
    for label in legacy.failed_checks:
        measurements.append(
            Measurement(
                metric_id=label.split(":", 1)[0],
                status=MeasurementStatus.SUCCEEDED,
                applicability=Applicability.APPLICABLE,
                role="target_efficacy",
                reasons=(f"did_not_move:{label}",),
            )
        )
    if nonfinite:
        measurements.append(
            Measurement(
                metric_id="nonfinite_guard",
                status=MeasurementStatus.ERROR,
                applicability=Applicability.INVALID_INPUT,
                reasons=("nonfinite_metric_value",),
            )
        )

    # --- Claim eligibility: engineering only, and only on a clean pass with
    #     known rights. Everything else ineligible with an explicit reason. ---
    reasons: list[str] = []
    engineering_eligible = (
        status is ResultStatus.PASSED
        and applicability is Applicability.APPLICABLE
        and rights_known
    )
    if status is not ResultStatus.PASSED:
        reasons.append(f"status_{status.value}")
    if not rights_known:
        reasons.append("rights_unknown")
    if evidence_tier in (EvidenceTier.T0_UNIT_SAFETY, EvidenceTier.T1_SYNTHETIC_REGRESSION):
        reasons.append("synthetic_evidence_engineering_only")

    eligibility = ClaimEligibility(
        classes={
            ClaimClass.ENGINEERING: (
                EligibilityState.ELIGIBLE if engineering_eligible else EligibilityState.INELIGIBLE
            ),
            ClaimClass.BOUNDED_PERFORMANCE: EligibilityState.INELIGIBLE,
            ClaimClass.INDEPENDENT_PERCEPTUAL: EligibilityState.INELIGIBLE,
            ClaimClass.PRODUCT_GENERALIZED: EligibilityState.INELIGIBLE,
        },
        reasons=tuple(dict.fromkeys(reasons)),
    )

    result = EvidenceResult(
        result_id=result_id or f"legacy:{legacy.id}",
        created_at=created_at or _now_rfc3339(),
        status=status,
        applicability=applicability,
        evidence_tier=evidence_tier,
        task={"source": "legacy_evaluation_result", "legacy_id": legacy.id},
        producer=producer or Producer(),
        measurements=tuple(measurements),
        axes=axes,
        claim_eligibility=eligibility,
        reasons=tuple(f"legacy_warning:{w}" for w in warnings),
    )
    return result.validated()
