"""DT-47 metric applicability registry suite.

Acceptance (Field 13): every current metric has a reviewed card; inapplicable
inputs never produce a quality pass; thresholds cite evidence or a setting
experiment (else unset). Adversarial (Field 16): missing reference,
misalignment, silence, out-of-domain, loudness-as-quality, stale calibration.
"""

import pytest

from src.evaluation.metric_registry.registry import (
    CURRENT_METRICS,
    MetricRegistry,
    load_default_registry,
)
from src.evaluation.metric_registry.schema import (
    MetricCard,
    MetricRole,
    ReferenceRequirement,
    ThresholdStatus,
)
from src.evaluation.semantics.canonical import verify_hash
from src.evaluation.semantics.enums import Applicability
from scripts.build_metric_registry import build_cards


@pytest.fixture(scope="module")
def registry() -> MetricRegistry:
    return load_default_registry()


# --------------------------------------------------------------------------
# Completeness + schema
# --------------------------------------------------------------------------

def test_every_current_metric_has_a_card(registry):
    assert registry.missing_cards() == ()
    assert len(registry.all()) == len(CURRENT_METRICS)


def test_committed_registry_matches_builder(registry):
    # Guards drift between the generator and the committed JSON.
    built = {c.metric_id: c.to_dict(with_hash=False) for c in build_cards()}
    loaded = {c.metric_id: c.to_dict(with_hash=False) for c in registry.all()}
    assert built == loaded


def test_card_roundtrip_and_hash(registry):
    card = registry.get("harshness_ratio")
    d = card.to_dict()
    assert verify_hash(d)
    assert MetricCard.from_dict(d).metric_id == "harshness_ratio"


# --------------------------------------------------------------------------
# Honest thresholds: unset unless evidence/experiment backed
# --------------------------------------------------------------------------

def test_defect_and_perception_thresholds_are_unset(registry):
    for c in registry.all():
        if c.role in (MetricRole.DEFECT_EVIDENCE, MetricRole.PERCEPTION, MetricRole.REFERENCE):
            assert c.threshold_status is ThresholdStatus.UNSET
            assert c.meaningful_threshold is None
            assert not c.can_support_quality_verdict()


def test_only_true_peak_carries_evidence_backed_ceiling(registry):
    backed = [c.metric_id for c in registry.all()
              if c.threshold_status is ThresholdStatus.EVIDENCE_BACKED]
    assert backed == ["true_peak_dbtp"]
    assert registry.get("true_peak_dbtp").threshold_evidence


def test_unset_threshold_may_not_carry_a_value():
    with pytest.raises(ValueError, match="unset threshold must not carry a value"):
        MetricCard("x", MetricRole.DEFECT_EVIDENCE, "ratio", -1,
                   meaningful_threshold=0.5, threshold_status=ThresholdStatus.UNSET)


def test_evidence_backed_value_requires_citation():
    with pytest.raises(ValueError, match="requires threshold_evidence"):
        MetricCard("x", MetricRole.SIGNAL_SAFETY, "dBTP", 0,
                   meaningful_threshold=-1.0, threshold_status=ThresholdStatus.EVIDENCE_BACKED)


# --------------------------------------------------------------------------
# Loudness-as-quality is prohibited
# --------------------------------------------------------------------------

@pytest.mark.parametrize("mid", ["integrated_lufs", "rms_dbfs", "advisory_integrated_lufs"])
def test_loudness_metrics_cannot_be_quality(registry, mid):
    card = registry.get(mid)
    assert card.role is MetricRole.COMPARABILITY
    assert not card.can_support_quality_verdict()
    assert "loudness_is_not_quality" in card.prohibited_interpretations


# --------------------------------------------------------------------------
# Applicability: missing reference / out of domain / stale calibration
# --------------------------------------------------------------------------

def test_full_reference_metric_missing_reference(registry):
    card = registry.get("si_sdr")
    assert card.reference_requirement is ReferenceRequirement.ALIGNED_PAIR
    ap = card.applicability(has_reference=False, in_domain=True, calibration_fresh=True)
    assert ap is Applicability.MISSING_REQUIRED_REFERENCE
    # documented failure modes cover misalignment and silent reference
    assert any("misalignment" in f for f in card.failure_modes)


def test_out_of_domain_is_not_applicable(registry):
    card = registry.get("harshness_ratio")
    ap = card.applicability(has_reference=True, in_domain=False, calibration_fresh=True)
    assert ap is Applicability.OUT_OF_DOMAIN


def test_stale_calibration_yields_unknown():
    card = MetricCard("calibrated_metric", MetricRole.DEFECT_EVIDENCE, "ratio", -1,
                      calibration_id="cal_v1")
    fresh = card.applicability(has_reference=True, in_domain=True, calibration_fresh=True)
    stale = card.applicability(has_reference=True, in_domain=True, calibration_fresh=False)
    assert fresh is Applicability.APPLICABLE
    assert stale is Applicability.UNKNOWN  # stale calibration cannot be interpreted


# --------------------------------------------------------------------------
# Unregistered metric is observation-only
# --------------------------------------------------------------------------

def test_unregistered_metric_cannot_support_quality(registry):
    assert not registry.is_registered("made_up_metric")
    assert not registry.can_support_quality_verdict("made_up_metric")


def test_inapplicable_input_never_supports_quality_pass(registry):
    # A registered defect metric on an out-of-domain input: applicability is not
    # APPLICABLE, and the metric has no quality-capable threshold anyway.
    card = registry.get("mud_ratio")
    ap = card.applicability(has_reference=False, in_domain=False, calibration_fresh=True)
    assert ap is not Applicability.APPLICABLE
    assert not card.can_support_quality_verdict()
