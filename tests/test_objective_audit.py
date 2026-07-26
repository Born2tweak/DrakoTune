"""Adversarial audit of candidate objectives (DT-77 C-4 precondition).

N-018's rule — an objective may not be believed until a deliberately destructive
candidate has been constructed and required to lose — is enforced here as code
rather than as advice.

What the audit found when first run (N-019) is asserted below rather than
narrated: the post-N-018 *guards* are not what stops the destructive candidates.
Three of the six are admitted by every guard, and an honest treatment is rejected
by one. What actually excludes them is the admissible parameter space. These tests
pin that down so the protection cannot quietly be attributed to the wrong
mechanism, and so a future change to either one is forced to restate the claim.
"""
from __future__ import annotations

import numpy as np

from src.dsp_engine import execute_plan
from src.paired_corpus import align_pair, make_surrogate_pair
from src.paired_corpus.objective_audit import (
    PATHOLOGIES,
    audit_objective,
    honest_recovery_chain,
    render,
)
from src.paired_corpus.search import (
    ADMISSIBLE,
    SI_SDR_FLOOR_DB,
    SR,
    Chain,
    Slot,
    build_target,
    chain_to_plan,
    composite_distance,
    evaluate,
)
from src.paired_corpus.surrogates import make_performance


def _surrogate(seed=101):
    raw, wet, sr, _ = make_surrogate_pair(seed=seed)
    return raw, wet, build_target(wet, align_pair(raw, wet, sr))


def _cut_pair(seed=211, true_hz=300.0, true_gain=-8.0):
    """The N-018 CI reproduction: wet is a KNOWN low-mid cut, so the correct
    direction of treatment is not a matter of opinion."""
    raw = make_performance(seed=seed).astype(np.float32)
    known = Chain("known", (Slot("PeakFilter", {"cutoff_frequency_hz": true_hz,
                                                "gain_db": true_gain, "q": 0.8}, ()),))
    out, _ = execute_plan(raw, SR, chain_to_plan(known))
    wet = (out[:, 0] if out.ndim == 2 else out).astype(np.float32)
    return raw, wet, build_target(wet, align_pair(raw, wet, SR))


def test_pathologies_are_all_renderable_and_documented():
    raw, _, _ = _surrogate()
    for path in PATHOLOGIES:
        out = render(raw, path.chain)
        assert np.all(np.isfinite(out)), f"{path.name} did not render"
        assert path.rationale, f"{path.name} has no recorded mechanism"


def test_every_pathology_lies_outside_the_admissible_space():
    """The catalogue must consist of candidates the *bounds* exclude — otherwise
    the search could author one and the corpus results would be unsafe."""
    assert PATHOLOGIES[1].chain.slots[0].params["ratio"] > ADMISSIBLE["comp"]["ratio"][1]
    assert PATHOLOGIES[2].chain.slots[0].params["threshold_db"] > \
        ADMISSIBLE["gate"]["threshold_db"][1]
    assert PATHOLOGIES[3].chain.slots[0].params["gain_db"] > ADMISSIBLE["air"]["gain_db"][1]
    for name in ("body_removal", "everything_at_once"):
        path = next(p for p in PATHOLOGIES if p.name == name)
        hp = next(s for s in path.chain.slots if s.processor == "HighpassFilter")
        assert hp.params["cutoff_frequency_hz"] > ADMISSIBLE["hp"]["cutoff_frequency_hz"][1]
    boost = next(p for p in PATHOLOGIES if p.name == "wrong_direction_boost")
    assert boost.chain.slots[0].params["gain_db"] > ADMISSIBLE["lowmid"]["gain_db"][1]


def test_the_guards_alone_do_not_exclude_destruction():
    """N-019. SI-SDR is scale-invariant and correlation-based, so a 20:1 compressor,
    a gate set above the performance floor and a +12 dB shelf all SCORE WELL on it
    (16-43 dB) while being unacceptable audio. The crest guard does not catch them
    either. The admissible bounds are the only thing that excludes them.

    If a future change makes the guards catch these, this test fails — and the
    claim in the docs about which mechanism protects the search must be rewritten,
    not silently upgraded."""
    raw, _, target = _cut_pair()
    admitted = [p.name for p in PATHOLOGIES
                if evaluate(raw, p.chain, target, full_si_sdr=True).safe]
    assert set(admitted) == {"crush", "gate_chop", "tilt_hack"}, (
        f"the set of guard-admitted pathologies changed: {admitted}")


def test_the_preservation_floor_also_rejects_an_honest_treatment():
    """N-019, the same finding from the other side: a -4 dB low-mid cut plus 2.5:1
    compression — squarely inside documented professional practice — measures about
    11 dB SI-SDR and is rejected by the 12 dB floor.

    So the floor is both under-inclusive (above) and over-inclusive (here). Any gap
    closure measured under it is a FLOOR on what an admissible chain can do, not a
    ceiling, and the number must be reported that way."""
    raw, _, target = _cut_pair()
    honest = evaluate(raw, honest_recovery_chain(), target, full_si_sdr=True)
    assert honest.crest_db > 8.0 and honest.peak < 0.98, "the honest chain is not gentle"
    assert honest.si_sdr_db < SI_SDR_FLOOR_DB
    assert honest.rejected_for == ("si_sdr",)


def test_audit_reports_baselines_so_a_verdict_is_never_a_bare_boolean():
    """An audit verdict belongs to (objective, pair). The surrogate wets here are
    gentle, so a pathology that wins on real material can lose on them; the report
    carries its own baselines to keep a pass from being over-read."""
    raw, _, target = _surrogate()
    honest = render(raw, honest_recovery_chain())
    report = audit_objective(lambda c: composite_distance(c, target), raw, honest)
    d = report.as_dict()
    assert set(d) >= {"gameable", "beaten_by", "honest_score", "noop_score",
                      "rewarded_over_noop", "pathologies"}
    assert np.isfinite(d["noop_score"]) and np.isfinite(d["honest_score"])
    assert len(d["pathologies"]) == len(PATHOLOGIES)
    # Measured: on synthetic surrogates the bare distance is NOT won by any of the
    # six, which is why a synthetic pass cannot certify an objective.
    assert report.gameable is False


def test_unmeasurable_candidate_is_not_treated_as_an_endorsement():
    raw, _, target = _surrogate()
    honest = render(raw, honest_recovery_chain())
    report = audit_objective(lambda c: float("-inf") if len(c) else 0.0, raw, honest)
    assert report.gameable is False
