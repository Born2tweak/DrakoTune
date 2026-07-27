"""Fail-closed certification battery for candidate objectives (DT-77 C-4).

Two kinds of test here. The first kind checks the battery detects each defect it
claims to detect — a battery that cannot fail is decoration. The second records
what it says about the objective currently in use, so a change to either the
objective or the guards has to restate the verdict rather than inherit it.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.dsp_engine import execute_plan
from src.paired_corpus import align_pair, make_surrogate_pair
from src.paired_corpus.objective_audit import (
    PATHOLOGIES,
    generated_pathologies,
    honest_recovery_chain,
    render,
)
from src.paired_corpus.objective_certification import (
    Verdict,
    certify,
    check_determinism,
    check_level_invariance,
    check_monotonicity,
    check_honest_reference_validity,
    check_non_degenerate,
)
from src.paired_corpus.search import (
    SR,
    Chain,
    Slot,
    build_target,
    chain_to_plan,
    composite_distance,
    evaluate_audio,
)
from src.paired_corpus.surrogates import make_performance


@pytest.fixture(scope="module")
def pair():
    raw, wet, sr, _ = make_surrogate_pair(seed=101)
    target = build_target(wet, align_pair(raw, wet, sr))
    honest = render(raw, honest_recovery_chain())
    return raw, wet, target, honest


def _distance(target):
    return lambda c: composite_distance(c, target)


def _admissible(raw, target):
    return lambda c: evaluate_audio(raw, c, target, full_si_sdr=True).safe


# ---------------------------------------------------------------------------
# The battery must be able to fail
# ---------------------------------------------------------------------------

def test_non_deterministic_objective_fails(pair):
    _, _, _, honest = pair
    rng = np.random.default_rng(0)
    result = check_determinism(lambda c: float(rng.standard_normal()), honest)
    assert result.verdict is Verdict.FAIL


def test_level_sensitive_objective_fails(pair):
    """Loudness inflation is the cheapest exploit of a level-sensitive metric."""
    _, _, _, honest = pair
    loudness = lambda c: -float(np.sqrt(np.mean(np.square(c))))  # noqa: E731
    assert check_level_invariance(loudness, honest).verdict is Verdict.FAIL


def test_inverted_objective_fails_monotonicity(pair):
    raw, wet, target, _ = pair
    assert check_monotonicity(lambda c: -composite_distance(c, target),
                              raw, wet).verdict is Verdict.FAIL


def test_objective_that_prefers_silence_fails(pair):
    raw, _, _, honest = pair
    energy = lambda c: float(np.sum(np.square(c)))  # noqa: E731
    assert check_non_degenerate(energy, raw, honest).verdict is Verdict.FAIL


def test_current_distance_passes_the_properties_it_should(pair):
    raw, wet, target, honest = pair
    obj = _distance(target)
    assert check_determinism(obj, honest).verdict is Verdict.PASS
    assert check_monotonicity(obj, raw, wet).verdict is Verdict.PASS
    assert check_level_invariance(obj, honest).verdict is Verdict.PASS
    assert check_non_degenerate(obj, raw, honest).verdict is Verdict.PASS


# ---------------------------------------------------------------------------
# Fail-closed semantics
# ---------------------------------------------------------------------------

def test_untestable_blocks_certification_exactly_like_failure(pair):
    """N-016 in a new place: absence of evidence must not read as evidence."""
    raw, wet, target, honest = pair
    report = certify(_distance(target), raw, wet, honest, pathologies=(),
                     admissible=_admissible(raw, target))
    assert "PERCEPTUAL_ALIGNMENT" in report.untestable
    assert report.certified_for_production is False


def test_production_certification_is_unreachable_while_def_003_stands(pair):
    """Nothing in this repository can pass the battery, and that is the point: no
    metric here has ever been shown to track what a listener hears. If this test
    starts failing, listening data exists and the claim must be re-derived."""
    raw, wet, target, honest = pair
    report = certify(_distance(target), raw, wet, honest, pathologies=(),
                     admissible=_admissible(raw, target))
    perceptual = next(p for p in report.properties if p.name == "PERCEPTUAL_ALIGNMENT")
    assert perceptual.verdict is Verdict.UNTESTABLE
    assert perceptual.measurements["blocked_by"] == "DEF-003"


def test_missing_constraint_is_untestable_not_a_pass(pair):
    raw, wet, target, honest = pair
    report = certify(_distance(target), raw, wet, honest, pathologies=())
    assert "CONSTRAINT_ADMITS_HONEST" in report.untestable


# ---------------------------------------------------------------------------
# What the battery says about the objective actually in use (N-020)
# ---------------------------------------------------------------------------

def test_current_objective_is_not_structurally_sound(pair):
    """Recorded, not narrated. The constraint rejects the honest candidate on every
    pair tried, so no result measured under it is an estimate rather than a lower
    bound. Priority order: this must be fixed before any objective is promoted."""
    raw, wet, target, honest = pair
    report = certify(_distance(target), raw, wet, honest,
                     admissible=_admissible(raw, target))
    assert report.structurally_sound is False
    assert "CONSTRAINT_ADMITS_HONEST" in report.failed


def test_generated_catalogue_covers_the_whole_registry():
    """A curated list only holds the exploits someone already imagined — which is
    how N-018 survived a review that already had adversarial tests in it."""
    from src.dsp_engine.processors import PROCESSORS
    names = {p.name.split(".")[1] for p in generated_pathologies()}
    assert names == set(PROCESSORS), f"registry processors missing from the battery: {set(PROCESSORS) - names}"
    assert len(generated_pathologies()) > len(PATHOLOGIES)


def test_the_generated_catalogue_found_what_the_curated_one_missed(pair):
    """Sensitivity evidence, and the reason generation is not decoration: on this
    pair a registry `Limiter` at its threshold bound is ADMITTED by every guard and
    outscores the honest candidate, while no curated pathology does."""
    raw, wet, target, honest = pair
    obj, adm = _distance(target), _admissible(raw, target)
    s_honest = obj(honest)

    curated_winners = [p.name for p in PATHOLOGIES
                       if adm(render(raw, p.chain)) and obj(render(raw, p.chain)) < s_honest]
    assert curated_winners == []

    limiter = next(p for p in generated_pathologies()
                   if p.name == "extreme.Limiter.threshold_db.max")
    audio = render(raw, limiter.chain)
    assert adm(audio), "the guards admit this candidate"
    assert obj(audio) < s_honest, "and it outscores the honest treatment"


def test_constraint_failure_is_not_reported_as_gaming(pair):
    """The first version of this battery folded the constraint into the score, which
    rejected the honest candidate and the reference and then reported the objective
    as gameable 37 ways. A constraint excludes candidates; it does not reorder the
    survivors."""
    raw, wet, target, honest = pair
    report = certify(_distance(target), raw, wet, honest,
                     admissible=_admissible(raw, target))
    gaming = next(p for p in report.properties if p.name == "GAMING_RESISTANCE")
    assert gaming.measurements["n_excluded_by_constraint"] > 0
    assert gaming.measurements["n_scored"] < gaming.measurements["n_pathologies"]
    # Identity and monotonicity are properties of the DISTANCE and must be scored
    # on it, not on a penalized composite.
    assert next(p for p in report.properties
                if p.name == "IDENTITY_OPTIMUM").verdict is Verdict.PASS


# ---------------------------------------------------------------------------
# A gaming verdict is only meaningful relative to a valid reference (N-020)
# ---------------------------------------------------------------------------

def test_reference_that_loses_to_no_op_makes_gaming_untestable(pair):
    """The confound that invalidated the first cross-objective comparison: under a
    full-spectrum distance the fixed honest chain scores WORSE than untreated raw,
    after which near-no-op candidates "beat" it without exploiting anything.

    Fail-closed handling: UNTESTABLE, not FAIL. The objective has not been shown to
    be bad; it has not been shown to be anything."""
    from src.paired_corpus.objectives import CANDIDATES_BY_NAME
    raw, wet, target, honest = pair
    amap = align_pair(raw, wet, SR)

    # `mrstft_log` is the surviving case on the noisy/comb surrogate: its reference
    # still loses to no-op there. (`logmel_l1` no longer does, once log-magnitudes
    # are floored -- see LOG_FLOOR_DB.)
    mrstft = CANDIDATES_BY_NAME["mrstft_log"].build(wet, amap, target)
    assert mrstft(honest) > mrstft(raw), "reference no longer loses to no-op here"
    assert check_honest_reference_validity(mrstft, raw, honest).verdict is Verdict.UNTESTABLE

    report = certify(mrstft, raw, wet, honest, admissible=_admissible(raw, target))
    assert "GAMING_RESISTANCE" in report.untestable
    assert "GAMING_RESISTANCE" not in report.failed


def test_reference_that_beats_no_op_yields_a_real_gaming_verdict(pair):
    raw, wet, target, honest = pair
    obj = _distance(target)
    assert obj(honest) < obj(raw)
    assert check_honest_reference_validity(obj, raw, honest).verdict is Verdict.PASS
    report = certify(obj, raw, wet, honest, admissible=_admissible(raw, target))
    assert "GAMING_RESISTANCE" not in report.untestable


def test_no_candidate_objective_can_be_selected_on_current_evidence(pair):
    """N-020, recorded as a test so a future ranking has to earn it: two of the four
    candidates cannot even be audited with the reference available, and all four are
    rejected by the preservation constraint."""
    from src.paired_corpus.objectives import CANDIDATES
    raw, wet, target, honest = pair
    amap = align_pair(raw, wet, SR)
    adm = _admissible(raw, target)
    verdicts = {}
    for cand in CANDIDATES:
        report = certify(cand.build(wet, amap, target), raw, wet, honest, admissible=adm)
        verdicts[cand.name] = report
        assert report.structurally_sound is False
        assert "CONSTRAINT_ADMITS_HONEST" in report.failed
    untestable_gaming = [n for n, r in verdicts.items() if "GAMING_RESISTANCE" in r.untestable]
    assert set(untestable_gaming) == {"mrstft_log"}


# ---------------------------------------------------------------------------
# Invertible surrogate: a reference that is provably optimal (N-021)
# ---------------------------------------------------------------------------

def _invertible(seed=101):
    from src.paired_corpus.surrogates import make_invertible_pair
    raw, wet, _, truth = make_invertible_pair(seed=seed)
    inverse = render(raw, Chain("inv", tuple(Slot(p, dict(q), ())
                                             for p, q in truth["inverse"])))
    amap = align_pair(raw, wet, SR)
    return raw, wet, amap, build_target(wet, amap), inverse


def test_exact_inverse_recovers_the_target_under_every_candidate():
    """N-020's blocker cleared: on a pair whose degradation the registry can invert
    exactly, the honest answer is optimal for every candidate objective, so a
    gaming verdict no longer depends on how good the reference happened to be."""
    from src.paired_corpus.objectives import CANDIDATES
    raw, wet, amap, ft, inverse = _invertible()
    for cand in CANDIDATES:
        obj = cand.build(wet, amap, ft)
        assert obj(inverse) < obj(raw), f"{cand.name}: inverse loses to doing nothing"
        assert obj(inverse) <= obj(wet) + 0.05, f"{cand.name}: inverse is far from the target"


def test_no_pathology_beats_the_exact_inverse():
    """With a provably optimal reference, none of the 44 destructive candidates
    outscores it — so the earlier 80/145 'gaming' figure was the reference, exactly
    as N-020 concluded."""
    raw, wet, amap, ft, inverse = _invertible()
    report = certify(_distance(ft), raw, wet, inverse,
                     admissible=_admissible(raw, ft))
    gaming = next(p for p in report.properties if p.name == "GAMING_RESISTANCE")
    assert gaming.verdict is Verdict.PASS
    assert gaming.measurements["beaten_by"] == []


def test_the_preservation_floor_rejects_the_mathematically_correct_answer():
    """N-021, and it is not a tuning complaint. SI-SDR is measured against the RAW,
    so the better a treatment corrects the raw the further it is from it: the exact
    inverse sits 92 dB from the target and 11.5-11.9 dB from the raw, and the 12 dB
    floor rejects it on every seed. A constraint anti-correlated with correctness
    cannot be made right by moving the number."""
    from src.evaluation.reference_metrics import si_sdr
    for seed in (101, 103, 107, 211):
        raw, wet, amap, ft, inverse = _invertible(seed)
        ev = evaluate_audio(raw, inverse, ft, full_si_sdr=True)
        n = min(len(inverse), len(wet))
        assert si_sdr(wet[:n], inverse[:n]) > 60.0, "the inverse is not actually correct"
        assert ev.rejected_for == ("si_sdr",)
        assert ev.safe is False


def test_level_invariance_check_does_not_clip_the_candidate():
    """The check scaled candidates up into clipping and then reported every metric
    as level-sensitive — it was measuring its own distortion. Positive gain is now
    capped at the available headroom."""
    raw, wet, amap, ft, inverse = _invertible()
    result = check_level_invariance(_distance(ft), inverse)
    assert result.verdict is Verdict.PASS
    assert result.measurements["headroom_db"] < 6.0, "pick a candidate with little headroom"
