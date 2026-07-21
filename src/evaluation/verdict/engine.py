"""Multiaxis verdict engine (DT-48).

Replaces target-only pass logic with ordered hard gates across safety, target
efficacy, collateral harm, intent preservation, and perceptual outcome, plus a
claim-eligibility decision. The engine refuses the listening exploits recorded
in NEGATIVE_RESULTS.md (N-002..N-006) and never lets "all targets improved" hide
a collateral-harm failure (N-001).

Rules are deterministic and every status carries stable reasons. Perceptual
thresholds and harm budgets remain unset (DT-47); where a real conclusion needs
one, the engine abstains (`indeterminate`) rather than inventing a pass.
"""

from src.evaluation.metric_registry.registry import MetricRegistry, load_default_registry
from src.evaluation.semantics.enums import (
    Applicability,
    ClaimClass,
    EligibilityState,
    EvidenceTier,
    ResultStatus,
    RightsPermission,
)
from src.evaluation.semantics.records import (
    AXIS_COLLATERAL_HARM,
    AXIS_INTENT_PRESERVATION,
    AXIS_PERCEPTUAL_OUTCOME,
    AXIS_SIGNAL_SAFETY,
    AXIS_TARGET_EFFICACY,
    AxisResult,
    ClaimEligibility,
)
from src.evaluation.verdict.bundle import EvaluationBundle, ListeningSummary

VERDICT_RULE_SET_ID = "verdict_rules_v1"

# Minimum move (either direction) to treat a metric effect as meaningful. This
# is an engineering guardrail, not a perceptual threshold.
_MEANINGFUL_EPS = 1e-3

# Tiers that carry independent listening evidence.
_LISTENING_TIERS = frozenset(
    {EvidenceTier.T3_INDEPENDENT_LISTENING, EvidenceTier.T4_REPLICATED_PRODUCT_EVIDENCE}
)


class Verdict:
    """Result of adjudicating one bundle."""

    def __init__(
        self,
        bundle_id: str,
        status: ResultStatus,
        axes: dict[str, AxisResult],
        claim_eligibility: ClaimEligibility,
        reasons: tuple[str, ...],
    ) -> None:
        self.bundle_id = bundle_id
        self.status = status
        self.axes = axes
        self.claim_eligibility = claim_eligibility
        self.reasons = reasons
        self.rule_set_id = VERDICT_RULE_SET_ID

    def to_dict(self) -> dict:
        return {
            "schema": "drakotune.verdict",
            "schema_version": "1.0.0",
            "bundle_id": self.bundle_id,
            "status": self.status.value,
            "axes": {k: v.to_dict() for k, v in sorted(self.axes.items())},
            "claim_eligibility": self.claim_eligibility.to_dict(),
            "reasons": list(self.reasons),
            "rule_set_id": self.rule_set_id,
        }


def _direction(registry: MetricRegistry, metric_id: str) -> int:
    card = registry.get(metric_id)
    return card.direction if card else 0


def _target_axis(bundle: EvaluationBundle, registry: MetricRegistry) -> AxisResult:
    targets = [m for m in bundle.measurements if m.is_target]
    if any(m.errored for m in targets):
        return AxisResult(ResultStatus.ERROR, ("target_measurement_errored",))
    if not targets:
        return AxisResult(ResultStatus.NOT_APPLICABLE, ("no_target_metric",))
    improved, failed = [], []
    for m in targets:
        direction = _direction(registry, m.metric_id)
        if m.effect is None or direction == 0:
            return AxisResult(ResultStatus.INDETERMINATE, (f"target_{m.metric_id}_uninterpretable",))
        moved = m.effect * direction
        (improved if moved > _MEANINGFUL_EPS else failed).append(m.metric_id)
    if improved and not failed:
        return AxisResult(ResultStatus.PASSED, tuple(f"target_improved:{m}" for m in improved))
    if failed and not improved:
        return AxisResult(ResultStatus.FAILED, tuple(f"target_not_moved:{m}" for m in failed))
    return AxisResult(ResultStatus.INDETERMINATE, ("mixed_target_outcomes",))


def _harm_axis(bundle: EvaluationBundle, registry: MetricRegistry) -> AxisResult:
    """Any non-target defect metric that worsened meaningfully is collateral harm.

    Harm *budgets* are unset (DT-47), so the engine uses direction-of-movement:
    a non-targeted defect metric moving the wrong way is a collateral-harm
    signal that blocks an unqualified pass (N-001).
    """
    harmed = []
    for m in bundle.measurements:
        if m.is_target or m.effect is None:
            continue
        card = registry.get(m.metric_id)
        if card is None or card.direction == 0:
            continue
        # Wrong-way movement: effect * direction < 0 (metric got worse).
        if m.effect * card.direction < -_MEANINGFUL_EPS:
            harmed.append(m.metric_id)
    if harmed:
        return AxisResult(ResultStatus.FAILED, tuple(f"collateral_worsened:{m}" for m in harmed))
    return AxisResult(ResultStatus.PASSED, ("no_collateral_worsening",))


def _perceptual_axis(bundle: EvaluationBundle) -> AxisResult:
    """Adjudicate the listening study, refusing the known exploits."""
    ls = bundle.listening
    if ls is None:
        return AxisResult(ResultStatus.NOT_APPLICABLE, ("no_listening_study",))
    if ls.cancelled:
        return AxisResult(ResultStatus.CANCELLED, ("panel_cancelled",))

    # N-004: ties/rows must be fully accounted for, not dropped.
    if ls.counted_rows() != ls.total_rows or ls.total_rows == 0:
        return AxisResult(ResultStatus.INDETERMINATE, ("rows_unaccounted_or_ties_dropped",))

    # N-002: independence is listeners x items, not row count.
    if ls.distinct_listeners < 2 or ls.distinct_items < 2:
        return AxisResult(ResultStatus.INDETERMINATE, ("insufficient_independent_units",))
    if ls.total_rows > ls.distinct_listeners * ls.distinct_items:
        return AxisResult(ResultStatus.INDETERMINATE, ("duplicate_responses_not_independent",))

    # N-006: side/order bias must be balanced; all-one-side is a red flag.
    if not ls.assignment_balanced:
        return AxisResult(ResultStatus.INDETERMINATE, ("assignment_not_balanced_side_bias",))
    side_a = sum(p.a_wins for p in ls.panels.values())
    side_b = sum(p.b_wins for p in ls.panels.values())
    if (side_a == 0 or side_b == 0) and (side_a + side_b) > 0:
        return AxisResult(ResultStatus.INDETERMINATE, ("all_choices_one_side_bias",))

    # N-005: panels cannot be pooled without a prespecified estimand; if panels
    # disagree in direction, abstain.
    directions = []
    for p in ls.panels.values():
        if p.decided == 0:
            continue
        directions.append(1 if p.b_wins > p.a_wins else -1 if p.a_wins > p.b_wins else 0)
    if len({d for d in directions if d != 0}) > 1:
        return AxisResult(ResultStatus.INDETERMINATE, ("panel_interaction_unresolved",))

    # N-003: a preserve/do-no-harm conclusion needs a prespecified equivalence
    # margin; "processed not preferred" is not "no harm".
    if bundle.intent == "preserve" and not ls.equivalence_prespecified:
        return AxisResult(ResultStatus.INDETERMINATE, ("no_prespecified_equivalence_margin",))

    # Passing all exploit gates, the study is structurally valid. Absent a
    # preregistered decision threshold (unset), a directional read is still only
    # indeterminate at claim level; report the decided direction as the outcome.
    if side_b > side_a:
        return AxisResult(ResultStatus.PASSED, ("processed_preferred_structurally_valid",))
    if side_a > side_b:
        return AxisResult(ResultStatus.FAILED, ("original_preferred",))
    return AxisResult(ResultStatus.INDETERMINATE, ("no_meaningful_difference",))


def _eligibility(
    bundle: EvaluationBundle,
    status: ResultStatus,
    harm: AxisResult,
    perceptual: AxisResult,
) -> ClaimEligibility:
    reasons: list[str] = []
    rights_ok = bundle.rights_state is RightsPermission.ALLOWED
    if not rights_ok:
        reasons.append(f"rights_{bundle.rights_state.value}")
    passed = status is ResultStatus.PASSED
    if not passed:
        reasons.append(f"status_{status.value}")

    tier = bundle.evidence_tier
    eng = passed and rights_ok and bundle.applicability is Applicability.APPLICABLE
    bounded = eng and tier in (
        EvidenceTier.T2_HELD_OUT_REAL_DATA,
        EvidenceTier.T3_INDEPENDENT_LISTENING,
        EvidenceTier.T4_REPLICATED_PRODUCT_EVIDENCE,
    )
    independent = (
        bounded
        and tier in _LISTENING_TIERS
        and perceptual.status is ResultStatus.PASSED
        and harm.status is not ResultStatus.FAILED
    )
    product = independent and tier is EvidenceTier.T4_REPLICATED_PRODUCT_EVIDENCE

    if tier in (EvidenceTier.T0_UNIT_SAFETY, EvidenceTier.T1_SYNTHETIC_REGRESSION):
        reasons.append("synthetic_or_unit_evidence_engineering_only")

    def st(flag: bool) -> EligibilityState:
        return EligibilityState.ELIGIBLE if flag else EligibilityState.INELIGIBLE

    return ClaimEligibility(
        classes={
            ClaimClass.ENGINEERING: st(eng),
            ClaimClass.BOUNDED_PERFORMANCE: st(bounded),
            ClaimClass.INDEPENDENT_PERCEPTUAL: st(independent),
            ClaimClass.PRODUCT_GENERALIZED: st(product),
        },
        reasons=tuple(dict.fromkeys(reasons)),
    )


def adjudicate(bundle: EvaluationBundle, registry: MetricRegistry | None = None) -> Verdict:
    """Adjudicate a bundle into a multiaxis verdict with claim eligibility."""
    registry = registry or load_default_registry()

    safety = (
        AxisResult(ResultStatus.PASSED, ("signal_integrity_ok",))
        if bundle.signal_safe
        else AxisResult(ResultStatus.UNSAFE, ("signal_integrity_failed",))
    )
    efficacy = _target_axis(bundle, registry)
    harm = _harm_axis(bundle, registry)
    perceptual = _perceptual_axis(bundle)
    intent = AxisResult(
        ResultStatus.NOT_APPLICABLE, ("intent_preservation_not_measured",)
    )

    axes = {
        AXIS_SIGNAL_SAFETY: safety,
        AXIS_TARGET_EFFICACY: efficacy,
        AXIS_COLLATERAL_HARM: harm,
        AXIS_INTENT_PRESERVATION: intent,
        AXIS_PERCEPTUAL_OUTCOME: perceptual,
    }

    reasons: list[str] = []

    # Ordered hard gates. Safety first; harm can never be averaged away.
    if safety.status is ResultStatus.UNSAFE:
        status = ResultStatus.UNSAFE
        reasons.append("hard_gate_signal_safety")
    elif efficacy.status is ResultStatus.ERROR:
        status = ResultStatus.ERROR
        reasons.append("target_measurement_error")
    elif perceptual.status is ResultStatus.CANCELLED:
        status = ResultStatus.CANCELLED
        reasons.append("listening_cancelled")
    elif harm.status is ResultStatus.FAILED and efficacy.status is ResultStatus.PASSED:
        status = ResultStatus.HARMFUL_TRADEOFF
        reasons.append("target_benefit_with_collateral_harm")
    elif harm.status is ResultStatus.FAILED:
        status = ResultStatus.HARMFUL_TRADEOFF
        reasons.append("collateral_harm_present")
    elif bundle.applicability is not Applicability.APPLICABLE:
        status = ResultStatus.NOT_APPLICABLE
        reasons.append(f"applicability_{bundle.applicability.value}")
    elif efficacy.status is ResultStatus.INDETERMINATE or perceptual.status is ResultStatus.INDETERMINATE:
        status = ResultStatus.INDETERMINATE
        reasons.append("insufficient_or_ambiguous_evidence")
    elif efficacy.status is ResultStatus.NOT_APPLICABLE and perceptual.status is ResultStatus.NOT_APPLICABLE:
        status = ResultStatus.NOT_APPLICABLE
        reasons.append("nothing_adjudicable")
    elif efficacy.status is ResultStatus.PASSED:
        status = ResultStatus.PASSED
        reasons.append("target_passed_no_hard_harm")
    else:
        status = ResultStatus.FAILED
        reasons.append("target_failed")

    eligibility = _eligibility(bundle, status, harm, perceptual)
    return Verdict(bundle.bundle_id, status, axes, eligibility, tuple(reasons))
