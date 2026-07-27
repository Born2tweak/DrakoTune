"""Candidate preservation constraint measured on the performance (N-021 follow-up).

The constraint in use floors SI-SDR against the raw, which N-021 showed is
anti-correlated with correctness. These tests pin what the replacement does and —
just as important — what it does not do, so its limits are inherited deliberately
rather than discovered later.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.paired_corpus import align_pair, make_surrogate_pair
from src.paired_corpus.objective_audit import PATHOLOGIES, honest_recovery_chain, render
from src.paired_corpus.objective_certification import certify
from src.paired_corpus.objectives import CANDIDATES
from src.paired_corpus.preservation import admits, performance_preservation
from src.paired_corpus.search import (
    SR,
    Chain,
    Slot,
    build_target,
    composite_distance,
    evaluate_audio,
)
from src.paired_corpus.surrogates import make_invertible_pair

SEEDS = (101, 103, 107, 211)


def _inverse_pair(seed):
    raw, wet, _, truth = make_invertible_pair(seed=seed)
    inverse = render(raw, Chain("inv", tuple(Slot(p, dict(q), ())
                                             for p, q in truth["inverse"])))
    return raw, wet, inverse


@pytest.mark.parametrize("seed", SEEDS)
def test_admits_the_answer_the_current_floor_rejects(seed):
    """The whole point. The exact inverse is 92 dB from the target and the SI-SDR
    floor rejects it on every seed; a constraint measured on the performance admits
    it."""
    raw, wet, inverse = _inverse_pair(seed)
    ft = build_target(wet, align_pair(raw, wet, SR))
    assert evaluate_audio(raw, inverse, ft, full_si_sdr=True).safe is False
    result = performance_preservation(raw, inverse)
    assert result.admitted is True
    assert result.voiced_retention == 1.0


def test_admits_an_honest_treatment_on_noisy_material():
    raw, wet, sr, _ = make_surrogate_pair(seed=101)
    honest = render(raw, honest_recovery_chain())
    ft = build_target(wet, align_pair(raw, wet, SR))
    assert evaluate_audio(raw, honest, ft, full_si_sdr=True).safe is False
    assert admits(raw, honest) is True


def test_rejects_gating_that_removes_the_performance():
    """What the SI-SDR floor let through: a gate above the performance floor scores
    43 dB on SI-SDR because it does not decorrelate anything — it just removes word
    tails and breaths."""
    raw, wet, sr, _ = make_surrogate_pair(seed=101)
    ft = build_target(wet, align_pair(raw, wet, SR))
    gate = next(p for p in PATHOLOGIES if p.name == "gate_chop")
    audio = render(raw, gate.chain)
    assert evaluate_audio(raw, audio, ft, full_si_sdr=True).safe is True
    result = performance_preservation(raw, audio)
    assert result.admitted is False
    assert "voiced_retention" in result.rejected_for
    assert result.voiced_retention < 0.9


def test_does_not_catch_extreme_compression_and_says_so():
    """A limitation carried deliberately: neither retention nor the crest guards stop
    a 20:1 compressor, so rejecting it stays the objective's job. Measured, so that
    the docstring's claim cannot quietly become false."""
    raw, wet, sr, _ = make_surrogate_pair(seed=101)
    crush = next(p for p in PATHOLOGIES if p.name == "crush")
    assert performance_preservation(raw, render(raw, crush.chain)).admitted is True


def test_tonal_destruction_is_left_to_the_objective():
    raw, wet, sr, _ = make_surrogate_pair(seed=101)
    for name in ("body_removal", "tilt_hack", "wrong_direction_boost"):
        path = next(p for p in PATHOLOGIES if p.name == name)
        assert performance_preservation(raw, render(raw, path.chain)).admitted is True
    # ...and the objective does reject them against a provably optimal reference.
    raw, wet, inverse = _inverse_pair(101)
    ft = build_target(wet, align_pair(raw, wet, SR))
    best = composite_distance(inverse, ft)
    for name in ("body_removal", "tilt_hack", "wrong_direction_boost"):
        path = next(p for p in PATHOLOGIES if p.name == name)
        assert composite_distance(render(raw, path.chain), ft) > best


def test_is_deterministic():
    raw, wet, sr, _ = make_surrogate_pair(seed=103)
    honest = render(raw, honest_recovery_chain())
    a = performance_preservation(raw, honest)
    b = performance_preservation(raw, honest)
    assert a == b


@pytest.mark.parametrize("seed", (101, 211))
def test_every_candidate_objective_becomes_structurally_sound(seed):
    """With the constraint replaced, all four candidate objectives pass every
    property the battery can check on ground truth — the first configuration in this
    thread that does. `certified_for_production` stays False: PERCEPTUAL_ALIGNMENT is
    untestable while DEF-003 stands, and that is not a formality to be waived."""
    raw, wet, inverse = _inverse_pair(seed)
    amap = align_pair(raw, wet, SR)
    ft = build_target(wet, amap)
    for cand in CANDIDATES:
        report = certify(cand.build(wet, amap, ft), raw, wet, inverse,
                         admissible=lambda c: admits(raw, c))
        assert report.structurally_sound is True, f"{cand.name}: {report.failed}"
        assert report.certified_for_production is False
        assert "PERCEPTUAL_ALIGNMENT" in report.untestable
