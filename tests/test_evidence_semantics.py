"""DT-45 evidence semantics and claim quarantine — semantic suite.

Covers the three acceptance criteria:
1. all legacy outputs map without silent pass;
2. nine canonical statuses serialize;
3. quarantined claims cannot render as approved.

Plus the failure/adversarial matrix (Field 16): NaN, absent metric, skipped
test, conflicting outcomes, target pass + harm, unknown rights.
"""

import math

import pytest

from src.evaluation.semantics import (
    APPROVED_CLAIM_STATUSES,
    Applicability,
    AxisResult,
    Claim,
    ClaimClass,
    ClaimEligibility,
    ClaimQuarantineRegistry,
    ClaimStatus,
    EligibilityState,
    EvidenceResult,
    EvidenceTier,
    MeasurementStatus,
    Producer,
    ResultStatus,
    SchemaValidationError,
    canonical_bytes,
    content_hash,
    load_default_registry,
    map_legacy_evaluation,
    max_claim_class_for_tier,
    parse_enum,
    verify_hash,
)
from src.evaluation.semantics.records import (
    AXIS_COLLATERAL_HARM,
    AXIS_SIGNAL_SAFETY,
    AXIS_TARGET_EFFICACY,
)
from src.shared_types import EvaluationResult

# --------------------------------------------------------------------------
# Canonical vocabulary
# --------------------------------------------------------------------------

NINE_STATUSES = [
    "passed",
    "failed",
    "unsafe",
    "harmful_tradeoff",
    "indeterminate",
    "not_applicable",
    "error",
    "cancelled",
    "quarantined",
]


def test_nine_canonical_statuses_exist_and_serialize():
    values = [s.value for s in ResultStatus]
    assert sorted(values) == sorted(NINE_STATUSES)
    assert len(values) == 9
    # round-trip each through parse_enum
    for v in NINE_STATUSES:
        assert parse_enum(ResultStatus, v).value == v


def test_unknown_enum_is_rejected_not_aliased():
    with pytest.raises(ValueError, match="unknown_enum"):
        parse_enum(ResultStatus, "mostly_passed")


def test_distinct_missing_states():
    # unknown / not_applicable / error / indeterminate must be distinct values.
    distinct = {
        Applicability.UNKNOWN.value,
        ResultStatus.NOT_APPLICABLE.value,
        ResultStatus.ERROR.value,
        ResultStatus.INDETERMINATE.value,
    }
    assert len(distinct) == 4


# --------------------------------------------------------------------------
# Canonical serialization + hashing
# --------------------------------------------------------------------------

def test_canonical_bytes_key_order_invariant():
    a = {"b": 1, "a": 2, "content_hash": "sha256:x"}
    b = {"a": 2, "b": 1}
    assert canonical_bytes(a) == canonical_bytes(b)  # hash field omitted, keys sorted


def test_content_hash_deterministic_and_verifiable():
    payload = {"a": 1, "nested": {"y": 2, "x": 3}}
    h = content_hash(payload)
    assert h.startswith("sha256:")
    payload_with = dict(payload, content_hash=h)
    assert verify_hash(payload_with)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_canonical_rejects_nonfinite(bad):
    with pytest.raises(SchemaValidationError):
        canonical_bytes({"metric": bad})


# --------------------------------------------------------------------------
# EvidenceResult validation invariants
# --------------------------------------------------------------------------

def _passed_result(**kw):
    base = dict(
        result_id="r1",
        created_at="2026-07-21T12:00:00Z",
        status=ResultStatus.PASSED,
        applicability=Applicability.APPLICABLE,
        evidence_tier=EvidenceTier.T1_SYNTHETIC_REGRESSION,
    )
    base.update(kw)
    return EvidenceResult(**base)


def test_passed_result_roundtrips_and_hashes():
    r = _passed_result().validated()
    d = r.to_dict()
    assert d["status"] == "passed"
    assert verify_hash(d)
    back = EvidenceResult.from_dict(d)
    assert back.status is ResultStatus.PASSED
    assert back.content_hash() == r.content_hash()


def test_passed_with_harm_axis_is_rejected():
    r = _passed_result(axes={AXIS_COLLATERAL_HARM: AxisResult(ResultStatus.FAILED, ("mud",))})
    with pytest.raises(SchemaValidationError):
        r.validated()


def test_passed_requires_applicable():
    r = _passed_result(applicability=Applicability.OUT_OF_DOMAIN)
    with pytest.raises(SchemaValidationError):
        r.validated()


def test_invalid_timestamp_rejected():
    r = _passed_result(created_at="2026-07-21 12:00:00")  # no tz
    errs = r.validate()
    assert any(e.error_code.value == "invalid_timestamp" for e in errs)


def test_empty_result_id_rejected():
    r = _passed_result(result_id="")
    errs = r.validate()
    assert any(e.error_code.value == "invalid_identity" for e in errs)


def test_eligibility_cannot_exceed_tier():
    # T1 synthetic caps at engineering; marking product_generalized eligible fails.
    r = _passed_result(
        claim_eligibility=ClaimEligibility(
            classes={ClaimClass.PRODUCT_GENERALIZED: EligibilityState.ELIGIBLE}
        )
    )
    errs = r.validate()
    assert any(e.error_code.value == "claim_evidence_ineligible" for e in errs)


def test_max_class_for_tier_ladder():
    assert max_claim_class_for_tier(EvidenceTier.T1_SYNTHETIC_REGRESSION) is ClaimClass.ENGINEERING
    assert (
        max_claim_class_for_tier(EvidenceTier.T4_REPLICATED_PRODUCT_EVIDENCE)
        is ClaimClass.PRODUCT_GENERALIZED
    )


# --------------------------------------------------------------------------
# Claim quarantine registry
# --------------------------------------------------------------------------

def test_default_inventory_only_engineering_regression_approved():
    reg = load_default_registry()
    approved = {c.claim_id for c in reg.approved_claims()}
    assert approved == {"claim_determinism_regression"}
    # everything professional / generalized / do-no-harm is quarantined
    for cid in ("claim_professional_quality", "claim_genre_robustness", "claim_clean_vocal_do_no_harm"):
        assert reg.get(cid).quarantined is True


def test_quarantined_claim_never_renders_approved():
    reg = load_default_registry()
    for claim in reg.quarantined_claims():
        assert claim.renders_as_approved() is False
        assert claim.render_status() is ClaimStatus.SUSPENDED
    reg.assert_no_quarantined_approved()


def test_quarantine_downgrades_even_an_approved_status():
    # Adversarial: a claim wrongly stamped approved_public but quarantined must
    # still refuse to render as approved.
    c = Claim(
        claim_id="c_bad",
        exact_wording="unsupported but stamped approved",
        claim_class=ClaimClass.PRODUCT_GENERALIZED,
        status=ClaimStatus.APPROVED_PUBLIC,
        quarantined=True,
        quarantine_reasons=("unsupported",),
    )
    assert c.status in APPROVED_CLAIM_STATUSES  # stored status is approved...
    assert c.renders_as_approved() is False  # ...but it does not render approved
    assert c.render_status() is ClaimStatus.SUSPENDED


def test_registry_rejects_duplicate_claim_id():
    c = Claim("dup", "w", ClaimClass.ENGINEERING, ClaimStatus.CANDIDATE)
    reg = ClaimQuarantineRegistry([c])
    with pytest.raises(SchemaValidationError):
        reg.add(Claim("dup", "w2", ClaimClass.ENGINEERING, ClaimStatus.CANDIDATE))


def test_quarantine_is_idempotent_on_reasons():
    reg = ClaimQuarantineRegistry([Claim("x", "w", ClaimClass.ENGINEERING, ClaimStatus.CANDIDATE)])
    reg.quarantine("x", ("r1",))
    reg.quarantine("x", ("r1", "r2"))
    assert reg.get("x").quarantine_reasons == ("r1", "r2")


# --------------------------------------------------------------------------
# Legacy mapping — no silent pass (acceptance criterion 1)
# --------------------------------------------------------------------------

def _legacy(**kw):
    return EvaluationResult(id=kw.pop("id", "e"), **kw)


def test_legacy_clean_pass_with_rights_is_engineering_eligible():
    ev = _legacy(passed_checks=("reduce_harshness:harshness_ratio d=-0.10",), after_metrics={"rms_dbfs": -12.0})
    r = map_legacy_evaluation(ev, rights_known=True)
    assert r.status is ResultStatus.PASSED
    assert r.claim_eligibility.is_eligible(ClaimClass.ENGINEERING)
    # never above engineering, even on a pass
    assert not r.claim_eligibility.is_eligible(ClaimClass.PRODUCT_GENERALIZED)


def test_legacy_unknown_rights_blocks_even_engineering_claim():
    ev = _legacy(passed_checks=("reduce_harshness:harshness_ratio d=-0.10",), after_metrics={"rms_dbfs": -12.0})
    r = map_legacy_evaluation(ev, rights_known=False)
    assert r.status is ResultStatus.PASSED  # measurement outcome stands
    assert not r.claim_eligibility.is_eligible(ClaimClass.ENGINEERING)
    assert "rights_unknown" in r.claim_eligibility.reasons


def test_legacy_nan_metric_maps_to_error_not_pass():
    ev = _legacy(
        passed_checks=("reduce_harshness:harshness_ratio d=-0.10",),
        after_metrics={"rms_dbfs": math.nan},
    )
    r = map_legacy_evaluation(ev, rights_known=True)
    assert r.status is ResultStatus.ERROR
    assert not r.claim_eligibility.is_eligible(ClaimClass.ENGINEERING)


def test_legacy_absent_targeted_metric_is_not_applicable():
    ev = _legacy(after_metrics={"rms_dbfs": -12.0})  # no passed/failed checks
    r = map_legacy_evaluation(ev, rights_known=True)
    assert r.status is ResultStatus.NOT_APPLICABLE
    assert r.axes[AXIS_TARGET_EFFICACY].status is ResultStatus.NOT_APPLICABLE


def test_legacy_conflicting_outcomes_map_to_indeterminate():
    ev = _legacy(
        passed_checks=("reduce_harshness:harshness_ratio d=-0.10",),
        failed_checks=("reduce_muddiness:mud_ratio d=+0.10",),
        after_metrics={"rms_dbfs": -12.0},
    )
    r = map_legacy_evaluation(ev, rights_known=True)
    assert r.status is ResultStatus.INDETERMINATE


def test_legacy_target_pass_plus_harm_is_harmful_tradeoff():
    ev = _legacy(
        passed_checks=("reduce_harshness:harshness_ratio d=-0.10",),
        warnings=("harshness_increased",),
        after_metrics={"rms_dbfs": -12.0},
    )
    r = map_legacy_evaluation(ev, rights_known=True)
    assert r.status is ResultStatus.HARMFUL_TRADEOFF
    assert r.axes[AXIS_COLLATERAL_HARM].status is ResultStatus.FAILED


def test_legacy_clipping_is_unsafe():
    ev = _legacy(
        passed_checks=("reduce_harshness:harshness_ratio d=-0.10",),
        warnings=("output_clipping",),
        after_metrics={"rms_dbfs": -1.0, "clipping_ratio": 0.01},
    )
    r = map_legacy_evaluation(ev, rights_known=True)
    assert r.status is ResultStatus.UNSAFE
    assert r.axes[AXIS_SIGNAL_SAFETY].status is ResultStatus.UNSAFE


def test_legacy_failed_only_is_failed():
    ev = _legacy(failed_checks=("reduce_harshness:harshness_ratio d=+0.02",), after_metrics={"rms_dbfs": -12.0})
    r = map_legacy_evaluation(ev, rights_known=True)
    assert r.status is ResultStatus.FAILED


# --------------------------------------------------------------------------
# No-silent-pass property over a matrix of legacy shapes
# --------------------------------------------------------------------------

_LEGACY_MATRIX = [
    _legacy(passed_checks=("a:m d=-0.1",), after_metrics={"rms_dbfs": -12.0}),
    _legacy(passed_checks=("a:m d=-0.1",), warnings=("harshness_increased",), after_metrics={"rms_dbfs": -12.0}),
    _legacy(passed_checks=("a:m d=-0.1",), warnings=("output_clipping",), after_metrics={"rms_dbfs": -1.0}),
    _legacy(passed_checks=("a:m d=-0.1",), failed_checks=("b:n d=+0.1",), after_metrics={"rms_dbfs": -12.0}),
    _legacy(after_metrics={"rms_dbfs": math.inf}, passed_checks=("a:m d=-0.1",)),
    _legacy(after_metrics={"rms_dbfs": -12.0}),
    _legacy(failed_checks=("b:n d=+0.1",), after_metrics={"rms_dbfs": -12.0}),
]


@pytest.mark.parametrize("ev", _LEGACY_MATRIX)
def test_no_silent_pass_property(ev):
    """A mapped result is PASSED only when it is applicable, safe, harm-free,
    and finite. Otherwise it names a non-pass status."""
    r = map_legacy_evaluation(ev, rights_known=True)
    if r.status is ResultStatus.PASSED:
        assert r.applicability is Applicability.APPLICABLE
        assert r.axes[AXIS_SIGNAL_SAFETY].status is not ResultStatus.UNSAFE
        assert r.axes[AXIS_COLLATERAL_HARM].status is not ResultStatus.FAILED
        assert r.axes[AXIS_TARGET_EFFICACY].status is ResultStatus.PASSED
    else:
        # non-pass results grant no eligible claim at all
        assert not r.claim_eligibility.is_eligible(ClaimClass.ENGINEERING)


@pytest.mark.parametrize("ev", _LEGACY_MATRIX)
def test_mapped_result_never_exceeds_engineering(ev):
    r = map_legacy_evaluation(ev, rights_known=True, evidence_tier=EvidenceTier.T1_SYNTHETIC_REGRESSION)
    for higher in (
        ClaimClass.BOUNDED_PERFORMANCE,
        ClaimClass.INDEPENDENT_PERCEPTUAL,
        ClaimClass.PRODUCT_GENERALIZED,
    ):
        assert not r.claim_eligibility.is_eligible(higher)


@pytest.mark.parametrize("ev", _LEGACY_MATRIX)
def test_every_mapped_result_validates_and_hashes(ev):
    r = map_legacy_evaluation(ev, rights_known=True)
    assert r.validate() == []
    assert verify_hash(r.to_dict())


# --------------------------------------------------------------------------
# Read compatibility: legacy EvaluationResult type is untouched
# --------------------------------------------------------------------------

def test_legacy_evaluation_result_still_roundtrips():
    ev = EvaluationResult(
        id="compat",
        before_metrics={"harshness_ratio": 0.7},
        after_metrics={"harshness_ratio": 0.5},
        deltas={"harshness_ratio": -0.2},
        passed_checks=("reduce_harshness:harshness_ratio d=-0.20",),
    )
    d = ev.to_dict()
    back = EvaluationResult.from_dict(d)
    assert back == ev
