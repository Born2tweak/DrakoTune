"""DT-48 multiaxis verdict engine suite.

Acceptance (Field 13): harsh fixture cannot receive an unqualified pass; every
status/reason stable; subgroup/harm/unknown block correctly. Verification
(Field 14): truth-table/property tests, the five reproduced listening exploits
(N-002..N-006), and a collateral-harm fixture (N-001). Adversarial (Field 16):
duplicate rows, ties, panel cancellation, side bias, missing metric, rights
expiry, all targets improve but hard harm.
"""

import pytest

from src.evaluation.semantics.enums import (
    Applicability,
    ClaimClass,
    EvidenceTier,
    ResultStatus,
    RightsPermission,
)
from src.evaluation.verdict import (
    EvaluationBundle,
    ListeningSummary,
    MetricObservation,
    PanelCounts,
    adjudicate,
)


def _bundle(**kw):
    base = dict(
        bundle_id="b1",
        intent="repair",
        applicability=Applicability.APPLICABLE,
        evidence_tier=EvidenceTier.T1_SYNTHETIC_REGRESSION,
        signal_safe=True,
        rights_state=RightsPermission.ALLOWED,
    )
    base.update(kw)
    return EvaluationBundle(**base)


# --------------------------------------------------------------------------
# Truth table over core outcomes
# --------------------------------------------------------------------------

def test_clean_target_pass_is_engineering_only():
    b = _bundle(measurements=(MetricObservation("harshness_ratio", effect=-0.10, is_target=True),))
    v = adjudicate(b)
    assert v.status is ResultStatus.PASSED
    assert v.claim_eligibility.is_eligible(ClaimClass.ENGINEERING)
    assert not v.claim_eligibility.is_eligible(ClaimClass.INDEPENDENT_PERCEPTUAL)


def test_unsafe_signal_overrides_everything():
    b = _bundle(
        signal_safe=False,
        measurements=(MetricObservation("harshness_ratio", effect=-0.5, is_target=True),),
    )
    v = adjudicate(b)
    assert v.status is ResultStatus.UNSAFE
    assert not v.claim_eligibility.is_eligible(ClaimClass.ENGINEERING)


def test_target_failed():
    b = _bundle(measurements=(MetricObservation("harshness_ratio", effect=+0.02, is_target=True),))
    assert adjudicate(b).status is ResultStatus.FAILED


def test_missing_metric_is_not_applicable():
    b = _bundle(measurements=())
    assert adjudicate(b).status is ResultStatus.NOT_APPLICABLE


def test_errored_target_metric_is_error():
    b = _bundle(measurements=(MetricObservation("harshness_ratio", errored=True, is_target=True),))
    assert adjudicate(b).status is ResultStatus.ERROR


def test_unknown_rights_blocks_engineering_claim():
    b = _bundle(
        rights_state=RightsPermission.UNKNOWN,
        measurements=(MetricObservation("harshness_ratio", effect=-0.10, is_target=True),),
    )
    v = adjudicate(b)
    assert v.status is ResultStatus.PASSED
    assert not v.claim_eligibility.is_eligible(ClaimClass.ENGINEERING)


def test_verdict_is_deterministic_and_serializes():
    b = _bundle(measurements=(MetricObservation("harshness_ratio", effect=-0.10, is_target=True),))
    v1, v2 = adjudicate(b), adjudicate(b)
    assert v1.to_dict() == v2.to_dict()
    assert v1.to_dict()["rule_set_id"] == "verdict_rules_v1"


# --------------------------------------------------------------------------
# N-001 collateral harm — harsh fixture cannot get an unqualified pass
# --------------------------------------------------------------------------

def test_harsh_fixture_target_pass_with_harm_is_harmful_tradeoff():
    # harshness target improves, but mud and sibilance worsen (the real harsh.wav shape)
    b = _bundle(
        measurements=(
            MetricObservation("harshness_ratio", effect=-0.10, is_target=True),
            MetricObservation("mud_ratio", effect=+5.2, is_target=False),
            MetricObservation("sibilance_frame_p95", effect=+0.0074, is_target=False),
        ),
    )
    v = adjudicate(b)
    assert v.status is ResultStatus.HARMFUL_TRADEOFF
    assert not v.claim_eligibility.is_eligible(ClaimClass.ENGINEERING)


def test_all_targets_improve_but_hard_harm_still_blocks():
    b = _bundle(
        measurements=(
            MetricObservation("harshness_ratio", effect=-0.2, is_target=True),
            MetricObservation("rumble_fraction", effect=-0.1, is_target=True),
            MetricObservation("mud_ratio", effect=+3.0, is_target=False),
        ),
    )
    assert adjudicate(b).status is ResultStatus.HARMFUL_TRADEOFF


# --------------------------------------------------------------------------
# Listening exploits N-002..N-006
# --------------------------------------------------------------------------

def _listening(**kw):
    base = dict(
        panels={"general": PanelCounts(a_wins=1, b_wins=1)},
        distinct_listeners=4,
        distinct_items=4,
        total_rows=2,
        processed_side="b",
        assignment_balanced=True,
        equivalence_prespecified=False,
        cancelled=False,
    )
    base.update(kw)
    return ListeningSummary(**base)


def _listen_bundle(ls, intent="repair", tier=EvidenceTier.T3_INDEPENDENT_LISTENING):
    return _bundle(
        intent=intent,
        evidence_tier=tier,
        measurements=(MetricObservation("harshness_ratio", effect=-0.1, is_target=True),),
        listening=ls,
    )


def test_n002_duplicate_rows_one_listener_not_independent():
    ls = _listening(
        panels={"general": PanelCounts(b_wins=8)},
        distinct_listeners=1, distinct_items=1, total_rows=8,
    )
    v = adjudicate(_listen_bundle(ls))
    assert v.axes["perceptual_outcome"].status is ResultStatus.INDETERMINATE
    assert v.status is ResultStatus.INDETERMINATE


def test_n003_clean_preserve_needs_prespecified_equivalence():
    ls = _listening(panels={"general": PanelCounts(a_wins=1, b_wins=1)}, total_rows=2,
                    equivalence_prespecified=False)
    v = adjudicate(_listen_bundle(ls, intent="preserve"))
    assert v.axes["perceptual_outcome"].status is ResultStatus.INDETERMINATE
    assert "no_prespecified_equivalence_margin" in v.axes["perceptual_outcome"].reasons


def test_n004_dropped_ties_are_detected():
    # total_rows says 10 but panels only account for 8 -> ties dropped
    ls = _listening(panels={"general": PanelCounts(a_wins=4, b_wins=4)}, total_rows=10)
    v = adjudicate(_listen_bundle(ls))
    assert v.axes["perceptual_outcome"].status is ResultStatus.INDETERMINATE
    assert "rows_unaccounted_or_ties_dropped" in v.axes["perceptual_outcome"].reasons


def test_n005_panel_disagreement_not_pooled():
    ls = _listening(
        panels={
            "experts": PanelCounts(a_wins=4),   # experts prefer original (A)
            "general": PanelCounts(b_wins=4),   # general prefer processed (B)
        },
        distinct_listeners=8, distinct_items=4, total_rows=8,
    )
    v = adjudicate(_listen_bundle(ls))
    assert v.axes["perceptual_outcome"].status is ResultStatus.INDETERMINATE
    assert "panel_interaction_unresolved" in v.axes["perceptual_outcome"].reasons


def test_n006_side_bias_all_one_side():
    ls = _listening(
        panels={"general": PanelCounts(a_wins=8)},  # everyone chose side A
        distinct_listeners=8, distinct_items=4, total_rows=8,
        assignment_balanced=False,
    )
    v = adjudicate(_listen_bundle(ls))
    assert v.axes["perceptual_outcome"].status is ResultStatus.INDETERMINATE


def test_panel_cancellation_is_cancelled():
    ls = _listening(cancelled=True)
    v = adjudicate(_listen_bundle(ls))
    assert v.status is ResultStatus.CANCELLED


# --------------------------------------------------------------------------
# Rights expiry blocks claims
# --------------------------------------------------------------------------

def test_rights_expiry_blocks_all_claims():
    b = _bundle(
        rights_state=RightsPermission.EXPIRED,
        measurements=(MetricObservation("harshness_ratio", effect=-0.1, is_target=True),),
    )
    v = adjudicate(b)
    for cc in ClaimClass:
        assert not v.claim_eligibility.is_eligible(cc)


# --------------------------------------------------------------------------
# A structurally valid independent study can reach independent-perceptual
# eligibility only with rights + no harm + listening tier
# --------------------------------------------------------------------------

def test_valid_independent_study_can_be_perceptually_eligible():
    ls = _listening(
        panels={"general": PanelCounts(b_wins=6, a_wins=1, ties=1)},
        distinct_listeners=6, distinct_items=6, total_rows=8,
        assignment_balanced=True,
    )
    b = _bundle(
        evidence_tier=EvidenceTier.T3_INDEPENDENT_LISTENING,
        rights_state=RightsPermission.ALLOWED,
        measurements=(MetricObservation("harshness_ratio", effect=-0.1, is_target=True),),
        listening=ls,
    )
    v = adjudicate(b)
    assert v.status is ResultStatus.PASSED
    assert v.claim_eligibility.is_eligible(ClaimClass.INDEPENDENT_PERCEPTUAL)
    assert not v.claim_eligibility.is_eligible(ClaimClass.PRODUCT_GENERALIZED)


def test_independent_study_with_harm_is_not_perceptually_eligible():
    ls = _listening(
        panels={"general": PanelCounts(b_wins=6, a_wins=1, ties=1)},
        distinct_listeners=6, distinct_items=6, total_rows=8,
    )
    b = _bundle(
        evidence_tier=EvidenceTier.T3_INDEPENDENT_LISTENING,
        rights_state=RightsPermission.ALLOWED,
        measurements=(
            MetricObservation("harshness_ratio", effect=-0.1, is_target=True),
            MetricObservation("mud_ratio", effect=+4.0, is_target=False),
        ),
        listening=ls,
    )
    v = adjudicate(b)
    assert v.status is ResultStatus.HARMFUL_TRADEOFF
    assert not v.claim_eligibility.is_eligible(ClaimClass.INDEPENDENT_PERCEPTUAL)
