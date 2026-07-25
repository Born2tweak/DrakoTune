"""DT-55E — forced-engagement oracle probe, validated on surrogates.

Two ground-truth cases prove the engagement-vs-missing-capability split:
  - IN-CAPABILITY wet (low-mid cut + compression, both in the registry): forcing
    engagement must get closer than the champion passthrough.
  - OUT-OF-CAPABILITY wet (heavy reverb the registry cannot add/remove): even the
    full forced chain leaves a large residual -> never `engagement_gap`.

Plus exhaustive coverage of the classifier: every one of the four categories,
both boundaries, and the alignment-failure path that MUST NOT be attributed
(regression for the bug where empty alignment maps were labelled a tuning gap).
No gated audio; no promotion; safety (ceiling/clipping) asserted.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.paired_corpus import align_pair, make_surrogate_pair
from src.paired_corpus.alignment import AlignmentMap
from src.paired_corpus.oracle import (
    CANDIDATES,
    CLASSIFICATIONS,
    DATA_LIMITATION,
    DEFAULT_STRENGTH,
    ENGAGEMENT_GAP,
    INCONCLUSIVE_ALIGNMENT,
    MISSING_PROCESSOR,
    CandidateResult,
    OracleProbe,
    _classify,
    _confidence,
    aggregate,
    build_plan,
    candidate_name,
    candidate_processors,
    probe_pair,
    range_binding,
)
from src.paired_corpus.surrogates import SR, degrade_to_raw, make_performance


def _champion_passthrough(raw):
    # The champion abstains on this material (N-015) -> model it as passthrough.
    return raw.copy(), 0


# --------------------------------------------------------------------------
# Plan construction
# --------------------------------------------------------------------------

def test_build_plan_uses_existing_processors_in_range():
    plan = build_plan("forced_full")
    procs = [a.processor for a in plan.actions]
    assert "PeakFilter" in procs and "HighpassFilter" in procs and "NoiseGate" in procs
    # muddiness cut is negative gain within PeakFilter's safe range
    mud = next(a for a in plan.actions if a.objective_id == "obj.muddiness")
    assert -12.0 <= mud.parameters["gain_db"] <= 0.0


def test_candidate_processors_reports_activation():
    assert candidate_processors("champion") == ()
    assert "NoiseGate" in candidate_processors("forced_full")


# --------------------------------------------------------------------------
# Classifier — every path, both boundaries
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("champ_d", "best_d", "n", "expected"),
    [
        # too few measurable phrases -> never attributed, whatever the numbers say
        (10.0, 1.0, 0, INCONCLUSIVE_ALIGNMENT),
        (10.0, 1.0, 2, INCONCLUSIVE_ALIGNMENT),
        # the historical bug: empty alignment -> inf distances
        (float("inf"), float("inf"), 9, INCONCLUSIVE_ALIGNMENT),
        (10.0, float("inf"), 9, INCONCLUSIVE_ALIGNMENT),
        (0.0, 0.0, 9, INCONCLUSIVE_ALIGNMENT),
        # engagement gap: >= 10% closed
        (10.0, 5.0, 20, ENGAGEMENT_GAP),
        (10.0, 9.0, 20, ENGAGEMENT_GAP),          # exactly 10% -> inclusive boundary
        # missing processor: <= 2% moved (including worse-than-champion)
        (10.0, 10.0, 20, MISSING_PROCESSOR),
        (10.0, 9.8, 20, MISSING_PROCESSOR),        # exactly 2% -> inclusive boundary
        (10.0, 12.0, 20, MISSING_PROCESSOR),
        # data limitation: real but unattributable movement in the 2-10% band
        (10.0, 9.5, 20, DATA_LIMITATION),
        (10.0, 9.05, 20, DATA_LIMITATION),
    ],
)
def test_classify_covers_every_path(champ_d, best_d, n, expected):
    classification, reason = _classify(champ_d, best_d, n)
    assert classification == expected
    assert classification in CLASSIFICATIONS
    assert reason                                    # every verdict is explained


def test_confidence_is_zero_for_inconclusive_and_scales_with_evidence():
    assert _confidence(0.0, 0, INCONCLUSIVE_ALIGNMENT) == 0.0
    weak = _confidence(0.5, 3, ENGAGEMENT_GAP)       # decisive but few phrases
    strong = _confidence(0.5, 40, ENGAGEMENT_GAP)
    assert 0.0 < weak < strong <= 1.0
    # sitting exactly on a boundary is maximally uncertain
    assert _confidence(0.10, 40, ENGAGEMENT_GAP) == 0.0


# --------------------------------------------------------------------------
# End-to-end probes on surrogates (ground truth we own)
# --------------------------------------------------------------------------

def test_in_capability_wet_engagement_helps():
    raw, wet, sr, _ = make_surrogate_pair(seed=101)   # wet = lowmid cut + compression
    amap = align_pair(raw, wet, sr)
    champ, acts = _champion_passthrough(raw)
    probe = probe_pair("surrogate-in", raw, wet, amap, champ, acts)
    champ_r = next(r for r in probe.results if r.name == "champion")
    forced = [r for r in probe.results if r.name != "champion"]
    best_lowmid = min(r.axis_distance.get("lowmid_250_500", 9) for r in forced)
    assert best_lowmid <= champ_r.axis_distance["lowmid_250_500"]
    assert probe.classification in (ENGAGEMENT_GAP, DATA_LIMITATION)
    assert probe.oracle_distance <= probe.champion_distance
    assert probe.active_processors                    # evidence names what ran


def test_out_of_capability_wet_not_engagement_gap():
    # wet = clean + heavy reverb (registry has no reverb add/remove) vs same raw.
    clean = make_performance(seed=131)
    raw = degrade_to_raw(clean, 131)
    d = int(0.08 * SR)
    reverb = clean.astype(np.float64).copy()
    for tap, g in ((d, 0.6), (2 * d, 0.4), (3 * d, 0.25)):
        reverb[tap:] += g * clean[:-tap]
    wet = (reverb / (np.max(np.abs(reverb)) + 1e-9) * 0.7).astype(np.float32)
    amap = align_pair(raw, wet, SR)
    champ, acts = _champion_passthrough(raw)
    probe = probe_pair("surrogate-out", raw, wet, amap, champ, acts)
    assert probe.classification != ENGAGEMENT_GAP     # existing chain can't fix reverb


def test_all_candidates_respect_safety():
    raw, wet, sr, _ = make_surrogate_pair(seed=141)
    amap = align_pair(raw, wet, sr)
    champ, acts = _champion_passthrough(raw)
    probe = probe_pair("surrogate-safe", raw, wet, amap, champ, acts)
    for r in probe.results:
        if r.name != "champion":
            assert r.safe, f"{r.name} breached ceiling/clipping"


def test_no_aligned_phrases_is_inconclusive_alignment():
    """Regression: an unalignable pair must NOT be attributed to a tuning gap."""
    raw, wet, sr, _ = make_surrogate_pair(seed=161)
    empty_map = AlignmentMap(0.0, 0.0, ())     # nothing aligned
    champ, acts = _champion_passthrough(raw)
    probe = probe_pair("s", raw, wet, empty_map, champ, acts)
    assert probe.classification == INCONCLUSIVE_ALIGNMENT
    assert probe.valid is False
    assert probe.improvement_pct == 0.0
    assert probe.active_processors == ()
    assert probe.confidence == 0.0


def test_probe_reports_every_candidate():
    raw, wet, sr, _ = make_surrogate_pair(seed=151)
    amap = align_pair(raw, wet, sr)
    champ, acts = _champion_passthrough(raw)
    probe = probe_pair("s", raw, wet, amap, champ, acts)
    names = {r.name for r in probe.results}
    assert names == {"champion", *(candidate_name(c, DEFAULT_STRENGTH) for c in CANDIDATES)}
    assert probe.n_measured_phrases > 0
    assert probe.n_candidates_searched == len(CANDIDATES)


def test_sweep_searches_the_existing_parameter_space():
    """A missing_processor verdict is only defensible after searching strengths."""
    raw, wet, sr, _ = make_surrogate_pair(seed=171)
    amap = align_pair(raw, wet, sr)
    champ, acts = _champion_passthrough(raw)
    sweep = (0.2, 1.0)
    probe = probe_pair("s", raw, wet, amap, champ, acts, sweep=sweep)
    assert probe.n_candidates_searched == len(CANDIDATES) * len(sweep)
    assert probe.best_candidate.split("@")[1] in ("0.2", "1.0")
    # searching more of the space can never be worse than the single default point
    point = probe_pair("s", raw, wet, amap, champ, acts)
    assert probe.oracle_distance <= point.oracle_distance + 1e-9


def test_range_binding_detects_an_optimum_outside_the_safe_range():
    """Still improving at max strength => the registry's cap is what limits us."""
    sweep = (0.2, 0.6, 1.0)

    def res(name, dist):
        return CandidateResult(name, 0.5, 0.0, True,
                               {"lowmid_250_500": dist}, 20, ("PeakFilter",))

    falling = [res(candidate_name("forced_lowmid", s), d)
               for s, d in zip(sweep, (0.5, 0.3, 0.2))]
    assert range_binding(falling, "forced_lowmid", sweep)[0] is True

    flattened = [res(candidate_name("forced_lowmid", s), d)
                 for s, d in zip(sweep, (0.5, 0.3, 0.3))]
    binding, slope = range_binding(flattened, "forced_lowmid", sweep)
    assert binding is False and slope == 0.0

    rising = [res(candidate_name("forced_lowmid", s), d)
              for s, d in zip(sweep, (0.2, 0.4, 0.6))]
    assert range_binding(rising, "forced_lowmid", sweep)[0] is False


def test_range_binding_is_unknowable_without_a_sweep():
    assert range_binding([], "forced_lowmid", ()) == (None, 0.0)
    assert range_binding([], "forced_lowmid", (0.7,)) == (None, 0.0)


def test_probe_without_sweep_reports_range_binding_unknown():
    raw, wet, sr, _ = make_surrogate_pair(seed=181)
    amap = align_pair(raw, wet, sr)
    champ, acts = _champion_passthrough(raw)
    assert probe_pair("s", raw, wet, amap, champ, acts).range_binding is None


def test_aggregate_range_binding_counts_only_swept_pairs():
    a = _probe("P-01", ENGAGEMENT_GAP, 40.0)
    b = _probe("P-02", MISSING_PROCESSOR, 0.0)
    a = OracleProbe(**{**a.__dict__, "range_binding": True})
    b = OracleProbe(**{**b.__dict__, "range_binding": False})
    unswept = _probe("P-03", DATA_LIMITATION, 5.0)          # range_binding None
    agg = aggregate([a, b, unswept])
    assert agg.n_range_binding == 1
    assert agg.range_binding_rate == pytest.approx(0.5)     # 1 of 2 measurable


def test_sweep_strength_changes_treatment_magnitude():
    gentle = build_plan("forced_lowmid", 0.2)
    hard = build_plan("forced_lowmid", 1.0)
    g = next(a for a in gentle.actions if a.objective_id == "obj.muddiness")
    h = next(a for a in hard.actions if a.objective_id == "obj.muddiness")
    assert abs(h.parameters["gain_db"]) > abs(g.parameters["gain_db"])


# --------------------------------------------------------------------------
# Aggregation — inconclusive pairs must never influence the numbers
# --------------------------------------------------------------------------

def _probe(pid, classification, improvement, champ_acts=0, procs=("PeakFilter",)):
    return OracleProbe(
        pair_id=pid, champion_actions=champ_acts, results=(),
        classification=classification, n_measured_phrases=20,
        champion_distance=10.0, oracle_distance=10.0 - improvement / 10,
        improvement_pct=improvement, best_candidate="forced_lowmid",
        active_processors=procs if classification != INCONCLUSIVE_ALIGNMENT else (),
        confidence=0.5, reason="test",
    )


def test_aggregate_excludes_inconclusive_pairs():
    probes = [
        _probe("P-01", ENGAGEMENT_GAP, 40.0),
        _probe("P-02", MISSING_PROCESSOR, 0.0, champ_acts=2),
        _probe("P-03", INCONCLUSIVE_ALIGNMENT, 999.0),   # poison if not excluded
        _probe("P-04", DATA_LIMITATION, 5.0),
    ]
    agg = aggregate(probes)
    assert agg.n_total == 4 and agg.n_valid == 3 and agg.n_excluded == 1
    assert agg.mean_improvement_pct == pytest.approx(15.0)
    assert agg.median_improvement_pct == pytest.approx(5.0)
    assert agg.classification_counts[INCONCLUSIVE_ALIGNMENT] == 1
    # 2 of the 3 valid pairs had a champion that applied zero actions
    assert agg.abstention_rate == pytest.approx(2 / 3, abs=1e-3)
    assert agg.engagement_rate == pytest.approx(1 / 3, abs=1e-3)
    assert agg.processor_activation_counts["PeakFilter"] == 3


def test_aggregate_reports_confidence_interval():
    agg = aggregate([_probe(f"P-{i}", ENGAGEMENT_GAP, 10.0 + i) for i in range(8)])
    lo, hi = agg.ci95_mean_improvement_pct
    assert lo < agg.mean_improvement_pct < hi


def test_aggregate_of_all_inconclusive_is_empty_not_a_claim():
    agg = aggregate([_probe("P-01", INCONCLUSIVE_ALIGNMENT, 0.0)])
    assert agg.n_valid == 0
    assert agg.mean_improvement_pct == 0.0
    assert np.isnan(agg.ci95_mean_improvement_pct[0])
