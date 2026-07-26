"""DT-55E Track C — bounded oracle search, validated on ground-truth surrogates.

The load-bearing claims this file must defend:
  1. the search never leaves the registry's declared safe ranges;
  2. it is deterministic, so a rerun is the same evidence;
  3. it can RECOVER a known in-capability transformation (otherwise a
     `missing_processor` verdict drawn from it means nothing);
  4. it refuses to buy spectral closeness with destruction (SI-SDR floor);
  5. the capability ablation actually separates templates.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.dsp_engine.processors import PROCESSORS
from src.paired_corpus import align_pair, make_surrogate_pair
from src.paired_corpus.search import (
    SI_SDR_FLOOR_DB,
    SR,
    TEMPLATES,
    TEMPLATES_BY_NAME,
    Chain,
    Slot,
    ablate,
    build_target,
    chain_to_plan,
    composite_distance,
    coordinate_descent,
    evaluate,
    reorder,
)
from src.paired_corpus.surrogates import make_performance


def _pair(seed=101):
    raw, wet, sr, _ = make_surrogate_pair(seed=seed)
    assert sr == SR
    return raw, wet, align_pair(raw, wet, sr)


# ---------------------------------------------------------------------------
# Safety and bounds
# ---------------------------------------------------------------------------

def test_every_template_stays_inside_registry_safe_ranges():
    for chain in TEMPLATES:
        for action in chain_to_plan(chain).actions:
            ranges = PROCESSORS[action.processor].safe_ranges
            for key, value in action.parameters.items():
                if key in ranges:
                    lo, hi = ranges[key]
                    assert lo <= value <= hi, f"{chain.name}/{action.processor}.{key}"


def test_search_result_never_leaves_safe_ranges():
    raw, wet, amap = _pair()
    target = build_target(wet, amap)
    result = coordinate_descent(raw, TEMPLATES[1], target, passes=2, points=4)
    for slot in result.best_chain.slots:
        ranges = PROCESSORS[slot.processor].safe_ranges
        for key, value in slot.params.items():
            if key in ranges:
                lo, hi = ranges[key]
                assert lo <= value <= hi, f"{slot.processor}.{key}={value}"


def test_registry_permits_more_than_the_planner_spec_uses():
    """The premise of Track C: the narrow sweep was not the registry's limit."""
    lo, hi = PROCESSORS["PeakFilter"].safe_ranges["gain_db"]
    assert lo <= -12.0 and hi >= 12.0        # planner's muddiness caps at -4.0 dB
    assert lo < 0 < hi                        # boosting is available, not only cutting


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_search_is_deterministic():
    raw, wet, amap = _pair()
    target = build_target(wet, amap)
    a = coordinate_descent(raw, TEMPLATES[0], target, passes=2, points=4)
    b = coordinate_descent(raw, TEMPLATES[0], target, passes=2, points=4)
    assert a.best_distance == b.best_distance
    assert [s.params for s in a.best_chain.slots] == [s.params for s in b.best_chain.slots]


def test_build_target_subsampling_is_deterministic_and_capped():
    raw, wet, amap = _pair(seed=105)
    t1 = build_target(wet, amap, max_phrases=3)
    t2 = build_target(wet, amap, max_phrases=3)
    assert t1.spans == t2.spans
    assert t1.n_phrases <= 3


# ---------------------------------------------------------------------------
# Capability: can it recover something we know is reachable?
# ---------------------------------------------------------------------------

def test_search_recovers_a_known_in_capability_transformation():
    """Wet = raw through a PeakFilter the registry owns. The search must undo
    most of the distance; if it cannot, no `missing_processor` verdict from this
    search means anything."""
    from src.dsp_engine import execute_plan
    clean = make_performance(seed=211)
    raw = clean.astype(np.float32)
    known = Chain("known", (Slot("PeakFilter",
                                 {"cutoff_frequency_hz": 300.0, "gain_db": -8.0, "q": 0.8},
                                 ()),))
    out, _ = execute_plan(raw, SR, chain_to_plan(known))
    wet = (out[:, 0] if out.ndim == 2 else out).astype(np.float32)
    amap = align_pair(raw, wet, SR)
    target = build_target(wet, amap)
    result = coordinate_descent(raw, TEMPLATES[0], target, passes=3, points=5)
    assert result.best_distance < result.start_distance * 0.5, (
        f"search recovered only {result.start_distance} -> {result.best_distance}")


def test_descent_never_returns_worse_than_its_starting_point():
    raw, wet, amap = _pair(seed=113)
    target = build_target(wet, amap)
    for chain in (TEMPLATES[0], TEMPLATES[2]):
        r = coordinate_descent(raw, chain, target, passes=2, points=4)
        assert r.best_distance <= r.start_distance + 1e-9


def test_at_bound_reports_parameters_resting_on_a_registry_edge():
    raw, wet, amap = _pair(seed=117)
    target = build_target(wet, amap)
    r = coordinate_descent(raw, TEMPLATES[0], target, passes=2, points=4)
    for name in r.at_bound:
        proc, key = name.split(".")
        slot = next(s for s in r.best_chain.slots if s.processor == proc)
        lo, hi = PROCESSORS[proc].safe_ranges[key]
        assert slot.params[key] in (lo, hi)


# ---------------------------------------------------------------------------
# The preservation floor must actually bind
# ---------------------------------------------------------------------------

def test_destructive_candidate_is_rejected_by_the_si_sdr_floor():
    raw, wet, amap = _pair(seed=123)
    target = build_target(wet, amap)
    destructive = Chain("destructive", (
        Slot("NoiseGate", {"threshold_db": -10.0, "attack_ms": 0.1, "release_ms": 10.0}, ()),
        Slot("PeakFilter", {"cutoff_frequency_hz": 300.0, "gain_db": -12.0, "q": 8.0}, ()),
    ))
    ev = evaluate(raw, destructive, target)
    assert ev.si_sdr_db < SI_SDR_FLOOR_DB
    assert ev.safe is False
    assert ev.penalized > ev.distance      # penalized, not silently accepted


def test_unsafe_candidates_cannot_win_the_search():
    raw, wet, amap = _pair(seed=127)
    target = build_target(wet, amap)
    r = coordinate_descent(raw, TEMPLATES[3], target, passes=2, points=4)
    final = evaluate(raw, r.best_chain, target, full_si_sdr=True)
    assert final.safe, f"search returned an unsafe chain: {final}"


# ---------------------------------------------------------------------------
# Ablation and ordering
# ---------------------------------------------------------------------------

def test_ablation_returns_one_result_per_template():
    raw, wet, amap = _pair(seed=131)
    target = build_target(wet, amap)
    results = ablate(raw, target, templates=TEMPLATES[:3], passes=1, points=3)
    assert [r.chain_name for r in results] == [c.name for c in TEMPLATES[:3]]


def test_richer_template_is_never_worse_than_its_prefix_at_equal_budget():
    """t2 contains t1's slots, so with the extra slot neutral it must at least tie."""
    raw, wet, amap = _pair(seed=137)
    target = build_target(wet, amap)
    r1, r2 = ablate(raw, target, templates=(TEMPLATES[0], TEMPLATES[1]),
                    passes=2, points=4)
    assert r2.best_distance <= r1.best_distance * 1.05    # tolerance: greedy descent


def test_reorder_permutes_slots_and_keeps_them_valid():
    chain = reorder(TEMPLATES[1], (2, 0, 1))
    assert [s.processor for s in chain.slots] == ["PeakFilter", "HighpassFilter", "PeakFilter"]
    assert len(chain_to_plan(chain).actions) == 3


def test_composite_distance_is_inf_without_measurable_phrases():
    from src.paired_corpus.search import WetTarget
    assert composite_distance(np.zeros(SR, dtype=np.float32), WetTarget((), ())) == float("inf")


def test_templates_form_an_increasing_capability_ladder():
    names = [c.name for c in TEMPLATES]
    assert names == sorted(names)                       # t1..t5 ordering is stable
    counts = [c.n_search_params for c in TEMPLATES]
    assert counts == sorted(counts), "each template must add capability, not remove it"
    assert TEMPLATES_BY_NAME["t5_full"].n_search_params > TEMPLATES_BY_NAME["t1_hp_lowmid"].n_search_params


@pytest.mark.parametrize("name", [c.name for c in TEMPLATES])
def test_every_template_renders_safely_at_its_neutral_start(name):
    raw, wet, amap = _pair(seed=141)
    target = build_target(wet, amap)
    ev = evaluate(raw, TEMPLATES_BY_NAME[name], target, full_si_sdr=True)
    assert ev.peak <= 0.978 and ev.clipping_ratio == 0.0


# ---------------------------------------------------------------------------
# Processor ordering — measured, not assumed
# ---------------------------------------------------------------------------

def test_ordering_variants_cover_every_predeclared_order():
    from src.paired_corpus.search import ORDERINGS, ordering_variants
    variants = ordering_variants(TEMPLATES_BY_NAME["t5_full"])
    assert len(variants) == len(ORDERINGS)
    for chain, label in zip(variants, ORDERINGS):
        assert chain.name.endswith(f"|{label}")
        assert len(chain.slots) == 6
        assert sorted(s.processor for s in chain.slots) == sorted(
            s.processor for s in TEMPLATES_BY_NAME["t5_full"].slots)


def test_research_chain_matches_the_documented_professional_order():
    """docs/research/vocal_chain_research.md: subtractive EQ before compression,
    additive EQ after it."""
    from src.paired_corpus.search import ORDERINGS, reorder
    chain = reorder(TEMPLATES_BY_NAME["t5_full"], ORDERINGS["research_chain"])
    procs = [s.processor for s in chain.slots]
    assert procs.index("Compressor") > procs.index("PeakFilter")
    assert procs.index("HighShelfFilter") > procs.index("Compressor")
    assert procs.index("NoiseGate") == 0


def test_ordering_changes_the_rendered_result():
    """If order were inert, comparing orderings would be meaningless."""
    from src.paired_corpus.search import ORDERINGS, reorder
    raw, wet, amap = _pair(seed=151)
    target = build_target(wet, amap)
    loaded = Chain("loaded", tuple(
        Slot(s.processor, {**s.params, **({"gain_db": -6.0} if s.processor == "PeakFilter"
                                          else {})}, ())
        for s in TEMPLATES_BY_NAME["t5_full"].slots))
    a = evaluate(raw, loaded, target).distance
    b = evaluate(raw, reorder(loaded, ORDERINGS["eq_after_comp"]), target).distance
    assert a != b, "processor order had no measurable effect — check the executor"


def test_ordering_variants_reject_wrong_slot_count():
    with pytest.raises(ValueError):
        from src.paired_corpus.search import ordering_variants
        ordering_variants(TEMPLATES_BY_NAME["t1_hp_lowmid"])
