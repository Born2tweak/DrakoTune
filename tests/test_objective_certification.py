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
