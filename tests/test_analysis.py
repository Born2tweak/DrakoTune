"""DT-57 — preregistration + clustered tie-aware analysis + power (autonomous).

Field 14 (calibration/property/replay) and Field 16 adversarial (separation, one
cluster, perfect ties, imbalance, dropout-tied-to-outcome, post-hoc endpoint,
nonconvergence). Numpy-only; deterministic. No threshold is invented; no claim.
"""
from __future__ import annotations

import pytest

from src.analysis import (
    Convergence,
    Direction,
    EndpointKind,
    ExclusionRule,
    Hypothesis,
    ListenerSummary,
    PENDING,
    PreregistrationPlan,
    SimConfig,
    analyze,
    diagnose,
    estimate_power,
    evaluate,
    listener_summaries,
    matches_lock,
    type_one_error,
)
from src.listening import Assignment, Panel, Response, ResponseOutcome, Side, Treatment


# ---------- preregistration immutability / lock ----------

def _hyp(**kw) -> Hypothesis:
    base = dict(
        endpoint_id="E1", description="processed preferred", null_hypothesis="rate <= 0.5",
        alternative="rate > 0.5", direction=Direction.SUPERIORITY, kind=EndpointKind.PERCEPTUAL,
        is_primary=True,
    )
    base.update(kw)
    return Hypothesis(**base)


def _plan(hyps) -> PreregistrationPlan:
    return PreregistrationPlan(
        plan_id="sap-1", version="1.0.0", population="dry rap/pop lead vocal; launch strata",
        estimand="listener-mean processed-preference among decisive responses",
        hypotheses=tuple(hyps),
        exclusions=(ExclusionRule("x1", "listener", "failed catch trials", "exclude"),),
        multiplicity_method="holm across primary endpoints",
        missing_data_policy="report dropout; sensitivity worst-case + complete-case",
        stopping_rule="fixed-N, no interim analyses",
        invalid_response_policy="forged/duplicate/ambiguous -> quarantine (DT-56)",
        tie_policy="ties reported as a category, never dropped",
    )


def test_freeze_refuses_while_thresholds_pending():
    plan = _plan([_hyp()])  # min_effect_threshold + alpha are PENDING
    assert plan.unset_choices()
    with pytest.raises(ValueError):
        plan.freeze()


def test_freeze_succeeds_when_signed_and_lock_is_stable():
    plan = _plan([_hyp(min_effect_threshold="0.10", alpha="0.05")])
    lock = plan.freeze()
    assert matches_lock(plan, lock)


def test_post_hoc_endpoint_change_breaks_the_lock():
    """Swapping an endpoint after freezing changes the hash (p-hacking guard)."""
    signed = _hyp(min_effect_threshold="0.10", alpha="0.05")
    plan = _plan([signed])
    lock = plan.freeze()
    tampered = _plan([_hyp(endpoint_id="E2", min_effect_threshold="0.10", alpha="0.05")])
    assert not matches_lock(tampered, lock)


def test_unsigned_plan_never_matches_a_lock():
    plan = _plan([_hyp()])
    assert matches_lock(plan, "anything") is False


# ---------- model: clustering, ties, indeterminacy ----------

def _resp(trial, listener, outcome, panel=Panel.TARGET_USER) -> Response:
    return Response(trial, listener, panel, outcome)


def _asn(trial, listener, processed_side=Side.B) -> Assignment:
    other = Side.A if processed_side is Side.B else Side.B
    return Assignment(trial, listener,
                      {processed_side: Treatment.PROCESSED, other: Treatment.ORIGINAL}, Side.A)


def test_one_listener_many_rows_is_one_cluster():
    """N-002 at the analysis layer: 8 rows from one listener -> a single cluster."""
    rows = [_resp(f"t{i}", "L1", ResponseOutcome.PREFER_B) for i in range(8)]
    asn = {(f"t{i}", "L1"): _asn(f"t{i}", "L1") for i in range(8)}
    summaries = listener_summaries(rows, asn)
    assert len(summaries) == 1
    result = analyze(summaries)
    assert result.convergence is Convergence.INDETERMINATE  # one cluster != a study


def test_ties_and_artifacts_are_masses_not_preferences():
    summaries = [
        ListenerSummary("L1", decisive=4, processed=3, ties=2, artifacts=1, cannot_tell=0),
        ListenerSummary("L2", decisive=4, processed=1, ties=0, artifacts=0, cannot_tell=0),
    ]
    result = analyze(summaries, n_boot=200)
    assert result.convergence is Convergence.CONVERGED
    assert result.tie_mass == 2 and result.artifact_mass == 1
    # point estimate is listener-mean of processed/decisive = mean(0.75, 0.25) = 0.5
    assert abs(result.point_estimate - 0.5) < 1e-9


def test_all_ties_is_indeterminate_no_naive_fallback():
    summaries = [ListenerSummary(f"L{i}", 0, 0, 5, 0, 0) for i in range(6)]
    result = analyze(summaries)
    assert result.convergence is Convergence.INDETERMINATE
    assert result.tie_mass == 30


def test_evaluate_uses_supplied_threshold_only():
    summaries = [ListenerSummary(f"L{i}", 10, 9, 0, 0, 0) for i in range(20)]
    result = analyze(summaries, n_boot=500)
    strong = evaluate(result, Direction.SUPERIORITY, threshold=0.5, ci_bound="lower")
    strict = evaluate(result, Direction.SUPERIORITY, threshold=0.95, ci_bound="lower")
    assert strong.outcome == "reject_null"
    assert strict.outcome == "fail_to_reject"


def test_indeterminate_result_evaluates_indeterminate():
    result = analyze([ListenerSummary("L1", 4, 4, 0, 0, 0)])
    assert evaluate(result, Direction.SUPERIORITY, 0.5, "lower").outcome == "indeterminate"


# ---------- power harness: calibration ----------

def test_strong_effect_is_well_powered():
    cfg = SimConfig(n_listeners=40, items_per_listener=25, true_pref=0.80)
    power = estimate_power(cfg, Direction.SUPERIORITY, threshold=0.5, n_sims=200, n_boot=300)
    assert power >= 0.80


def test_null_effect_controls_type_one_error():
    cfg = SimConfig(n_listeners=40, items_per_listener=25, true_pref=0.50)
    t1 = type_one_error(cfg, Direction.SUPERIORITY, threshold=0.5, n_sims=200, n_boot=300)
    assert t1 <= 0.15  # loose upper bound; one-sided 95% CI target ~0.025


def test_power_is_deterministic():
    cfg = SimConfig(20, 20, 0.75)
    a = estimate_power(cfg, Direction.SUPERIORITY, 0.5, n_sims=100, n_boot=200)
    b = estimate_power(cfg, Direction.SUPERIORITY, 0.5, n_sims=100, n_boot=200)
    assert a == b


# ---------- diagnostics / adversarial ----------

def test_perfect_separation_flagged():
    summaries = [ListenerSummary("L1", 5, 5, 0, 0, 0), ListenerSummary("L2", 5, 0, 0, 0, 0)]
    assert diagnose(summaries).perfect_separation is True


def test_single_cluster_flagged():
    assert diagnose([ListenerSummary("L1", 5, 3, 0, 0, 0)]).single_decisive_cluster is True


def test_dropout_correlated_with_outcome_flagged():
    d = diagnose(
        [ListenerSummary(f"L{i}", 5, 3, 0, 0, 0) for i in range(4)],
        dropout_by_group={"processed_heavy": (10, 8), "original_heavy": (10, 0)},
    )
    assert d.dropout_correlated_with_outcome is True


def test_high_tie_mass_flagged():
    summaries = [ListenerSummary(f"L{i}", 2, 1, 8, 0, 0) for i in range(3)]
    assert diagnose(summaries).high_tie_mass is True
