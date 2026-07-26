"""Bounded oracle parameter search (DT-55E Track C).

The first oracle swept the *planner's* strength mapping, which is a far narrower
space than the processor registry actually permits: the planner's muddiness
treatment caps at a -4.0 dB PeakFilter, while `PROCESSORS["PeakFilter"]` declares
a safe range of -12..+12 dB. A `missing_processor` verdict drawn from the narrow
space says nothing about the registry's real capability.

This module does what DT-55E specifies: deterministic coordinate descent over the
**registry's own safe ranges** (`clamp_params` enforced), with hard safety
penalties, across chain templates of increasing capability. Comparing what each
template achieves is a capability ablation — it identifies *which* capability
closes a gap, instead of only reporting that the narrow chain did not.

Diagnostic only. Nothing here authors a plan, tunes a threshold, or promotes
anything; it measures what the existing registry can and cannot reach.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from src.dsp_engine import execute_plan
from src.dsp_engine.processors import PROCESSORS, clamp_params
from src.evaluation.reference_metrics import si_sdr
from src.paired_corpus.alignment import AlignmentMap
from src.paired_corpus.deltas import phrase_features
from src.shared_types import ProcessingAction, ProcessingPlan

SR = 44100
CEILING = 0.977
# Preservation floor: a candidate that matches the wet spectrum by destroying the
# performance is not a solution. Measured against the RAW input.
SI_SDR_FLOOR_DB = 5.0
PENALTY = 1e6

AXES = ("lowmid_250_500", "harsh_2500_5000", "sib_5500_12000", "crest_db",
        "tilt_db_per_oct")
AXIS_SCALE = {"lowmid_250_500": 10.0, "harsh_2500_5000": 10.0,
              "sib_5500_12000": 10.0, "crest_db": 1.0, "tilt_db_per_oct": 1.0}


# ---------------------------------------------------------------------------
# Chain templates — capability ablation ladder
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Slot:
    """One processor position in a chain, with the params the search may move."""
    processor: str
    params: dict[str, float]
    search: tuple[str, ...]


@dataclass(frozen=True)
class Chain:
    name: str
    slots: tuple[Slot, ...]

    @property
    def n_search_params(self) -> int:
        return sum(len(s.search) for s in self.slots)


def _hp() -> Slot:
    return Slot("HighpassFilter", {"cutoff_frequency_hz": 90.0}, ("cutoff_frequency_hz",))


def _lowmid() -> Slot:
    # Bidirectional by construction: the registry allows -12..+12 dB, so the
    # search can ADD low-mid body as readily as cut it (F-6 asked for this).
    return Slot("PeakFilter", {"cutoff_frequency_hz": 300.0, "gain_db": 0.0, "q": 0.8},
                ("cutoff_frequency_hz", "gain_db", "q"))


def _mid() -> Slot:
    return Slot("PeakFilter", {"cutoff_frequency_hz": 3500.0, "gain_db": 0.0, "q": 1.4},
                ("cutoff_frequency_hz", "gain_db", "q"))


def _air() -> Slot:
    return Slot("HighShelfFilter", {"cutoff_frequency_hz": 8000.0, "gain_db": 0.0, "q": 0.7},
                ("cutoff_frequency_hz", "gain_db"))


def _gate() -> Slot:
    # C-1: the planner's NoiseGate spec is strength-invariant (fixed -42 dB), so
    # denoising had only ever been tested at one threshold. Here it is searched.
    return Slot("NoiseGate", {"threshold_db": -42.0, "attack_ms": 1.0, "release_ms": 250.0},
                ("threshold_db", "release_ms"))


def _comp() -> Slot:
    return Slot("Compressor",
                {"threshold_db": -18.0, "ratio": 2.5, "attack_ms": 15.0, "release_ms": 75.0},
                ("threshold_db", "ratio"))


TEMPLATES: tuple[Chain, ...] = (
    Chain("t1_hp_lowmid", (_hp(), _lowmid())),
    Chain("t2_tonal", (_hp(), _lowmid(), _mid())),
    Chain("t3_tonal_air", (_hp(), _lowmid(), _mid(), _air())),
    Chain("t4_tonal_air_gate", (_hp(), _lowmid(), _mid(), _air(), _gate())),
    Chain("t5_full", (_hp(), _lowmid(), _mid(), _air(), _gate(), _comp())),
)
TEMPLATES_BY_NAME = {c.name: c for c in TEMPLATES}


def chain_to_plan(chain: Chain) -> ProcessingPlan:
    actions = tuple(
        ProcessingAction(
            id=f"search.{i}.{slot.processor}", processor=slot.processor,
            parameters=clamp_params(slot.processor, slot.params)[0], strength=1.0,
            reason=f"bounded oracle search ({chain.name})",
            objective_id=f"search.{i}", reversible=True,
        )
        for i, slot in enumerate(chain.slots)
    )
    return ProcessingPlan(
        id=f"search-{chain.name}", preset_profile="clean", objectives=(),
        actions=actions, skipped_processors=(), policy_version="oracle-search-1",
    )


def reorder(chain: Chain, order: tuple[int, ...], label: str = "") -> Chain:
    """Chain with slots permuted — the executor honours plan order exactly."""
    suffix = label or "order" + "".join(map(str, order))
    return Chain(f"{chain.name}|{suffix}", tuple(chain.slots[i] for i in order))


# Predeclared orderings for `t5_full`, whose slots are
#   0 highpass · 1 low-mid bell · 2 mid bell · 3 air shelf · 4 gate · 5 compressor.
# `research_chain` is the order documented in docs/research/vocal_chain_research.md
# (subtractive EQ before compression, additive EQ after it); the rest are the
# plausible alternatives. Which one wins is measured, never assumed.
ORDERINGS: dict[str, tuple[int, ...]] = {
    "as_specified": (0, 1, 2, 3, 4, 5),
    "research_chain": (4, 0, 1, 2, 5, 3),
    "eq_after_comp": (0, 4, 5, 1, 2, 3),
    "gate_last": (0, 1, 2, 5, 3, 4),
}


def ordering_variants(chain: Chain) -> tuple[Chain, ...]:
    """Every predeclared ordering of a 6-slot chain."""
    if len(chain.slots) != len(next(iter(ORDERINGS.values()))):
        raise ValueError("ORDERINGS are defined for the 6-slot full chain only")
    return tuple(reorder(chain, order, label) for label, order in ORDERINGS.items())


# ---------------------------------------------------------------------------
# Objective
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WetTarget:
    """Wet phrase features, computed ONCE per pair and reused by every candidate."""
    spans: tuple[tuple[float, float], ...]        # raw-side (start_s, end_s)
    features: tuple[dict, ...]

    @property
    def n_phrases(self) -> int:
        return len(self.spans)


def _slice(x: np.ndarray, a: float, b: float) -> np.ndarray:
    i, j = max(int(a * SR), 0), min(int(b * SR), len(x))
    return x[i:j] if j > i else np.zeros(1, dtype=x.dtype)


def build_target(wet: np.ndarray, amap: AlignmentMap,
                 max_phrases: int = 30) -> WetTarget:
    """Deterministically subsample aligned phrases and precompute wet features.

    Subsampling is evenly spaced (not random) so a rerun measures the same
    phrases; it bounds search cost without biasing toward one part of a take.
    """
    usable = [p for p in amap.aligned()
              if (p.raw_end_s - p.raw_start_s) >= 0.1 and (p.wet_end_s - p.wet_start_s) >= 0.1]
    if len(usable) > max_phrases:
        idx = np.linspace(0, len(usable) - 1, max_phrases).round().astype(int)
        usable = [usable[i] for i in dict.fromkeys(idx.tolist())]
    spans, feats = [], []
    for p in usable:
        wseg = _slice(wet, p.wet_start_s, p.wet_end_s)
        if len(wseg) < SR // 10:
            continue
        spans.append((p.raw_start_s, p.raw_end_s))
        feats.append(phrase_features(wseg, SR))
    return WetTarget(tuple(spans), tuple(feats))


def composite_distance(candidate: np.ndarray, target: WetTarget) -> float:
    """Mean scaled |wet - candidate| over the target phrases. inf if unmeasurable."""
    if not target.spans:
        return float("inf")
    totals: list[float] = []
    for (a, b), fw in zip(target.spans, target.features):
        cseg = _slice(candidate, a, b)
        if len(cseg) < SR // 10:
            continue
        fc = phrase_features(cseg, SR)
        totals.append(sum(abs(fw[ax] - fc[ax]) * AXIS_SCALE[ax] for ax in AXES))
    return round(float(np.mean(totals)), 5) if totals else float("inf")


@dataclass(frozen=True)
class Evaluation:
    distance: float
    penalized: float
    peak: float
    clipping_ratio: float
    si_sdr_db: float
    safe: bool


# SI-SDR over a whole take costs about as much as the render itself. During the
# search it is estimated on one fixed, centred window; the reported result is
# always recomputed over the full signal. The window is deterministic, so the
# search is still reproducible.
SI_SDR_WINDOW_S = 30.0


def _preservation_db(raw: np.ndarray, audio: np.ndarray, full: bool) -> float:
    n = min(len(audio), len(raw))
    if not full and n > int(SI_SDR_WINDOW_S * SR):
        width = int(SI_SDR_WINDOW_S * SR)
        start = (n - width) // 2
        sl = slice(start, start + width)
        return float(si_sdr(raw[sl], audio[sl]))
    return float(si_sdr(raw[:n], audio[:n]))


def evaluate(raw: np.ndarray, chain: Chain, target: WetTarget,
             full_si_sdr: bool = False) -> Evaluation:
    """Render a chain and score it. Unsafe candidates are penalized, not hidden."""
    out, _ = execute_plan(raw, SR, chain_to_plan(chain))
    audio = (out[:, 0] if out.ndim == 2 else out).astype(np.float32)
    peak = float(np.max(np.abs(audio)) + 1e-12)
    clip = float(np.mean(np.abs(audio) >= 0.999))
    sdr = _preservation_db(raw, audio, full_si_sdr)
    distance = composite_distance(audio, target)
    safe = peak <= CEILING + 1e-3 and clip == 0.0 and sdr >= SI_SDR_FLOOR_DB
    penalized = distance if safe else (
        distance + PENALTY if np.isfinite(distance) else float("inf"))
    return Evaluation(distance, penalized, round(peak, 4), round(clip, 6),
                      round(sdr, 3), safe)


# ---------------------------------------------------------------------------
# Deterministic coordinate descent
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SearchResult:
    chain_name: str
    best_chain: Chain
    best_distance: float
    start_distance: float
    evaluations: int
    passes: int
    converged: bool
    si_sdr_db: float
    peak: float
    at_bound: tuple[str, ...]      # params resting on a registry safe-range edge


def _axis_values(lo: float, hi: float, current: float, span: float,
                 n: int) -> list[float]:
    """Candidate values around `current`, clipped to [lo, hi], endpoints included."""
    half = (hi - lo) * span / 2.0
    vals = np.linspace(current - half, current + half, n)
    vals = np.clip(vals, lo, hi)
    return sorted({round(float(v), 4) for v in vals} | {lo, hi})


def coordinate_descent(raw: np.ndarray, chain: Chain, target: WetTarget,
                       passes: int = 3, points: int = 5,
                       max_evaluations: int = 400) -> SearchResult:
    """Deterministic coordinate descent inside the registry's safe ranges.

    One coordinate at a time, contracting the search span each pass. No RNG, so
    a rerun on the same inputs produces the same chain — a requirement for this
    to count as evidence.
    """
    best = chain
    base = evaluate(raw, chain, target)
    best_score, start = base.penalized, base.distance
    evals, converged = 1, False
    coords = [(i, key) for i, slot in enumerate(chain.slots) for key in slot.search]

    for p in range(passes):
        improved = False
        span = 1.0 / (2 ** p)                       # 100% -> 50% -> 25% of range
        for slot_i, key in coords:
            if evals >= max_evaluations:
                break
            lo, hi = PROCESSORS[best.slots[slot_i].processor].safe_ranges[key]
            current = best.slots[slot_i].params[key]
            for value in _axis_values(lo, hi, current, span, points):
                if value == current or evals >= max_evaluations:
                    continue
                slots = list(best.slots)
                params = dict(slots[slot_i].params)
                params[key] = value
                slots[slot_i] = replace(slots[slot_i], params=params)
                cand = Chain(best.name, tuple(slots))
                score = evaluate(raw, cand, target).penalized
                evals += 1
                if score < best_score - 1e-9:
                    best, best_score, improved = cand, score, True
                    current = value
        if not improved:
            converged = True
            break

    final = evaluate(raw, best, target, full_si_sdr=True)
    at_bound = []
    for slot_i, key in coords:
        lo, hi = PROCESSORS[best.slots[slot_i].processor].safe_ranges[key]
        value = best.slots[slot_i].params[key]
        if abs(value - lo) < 1e-6 or abs(value - hi) < 1e-6:
            at_bound.append(f"{best.slots[slot_i].processor}.{key}")
    return SearchResult(
        chain_name=chain.name, best_chain=best, best_distance=final.distance,
        start_distance=start, evaluations=evals, passes=min(p + 1, passes),
        converged=converged, si_sdr_db=final.si_sdr_db, peak=final.peak,
        at_bound=tuple(at_bound),
    )


def ablate(raw: np.ndarray, target: WetTarget,
           templates: tuple[Chain, ...] = TEMPLATES,
           **kw) -> tuple[SearchResult, ...]:
    """Search every capability template. The distance each one REACHES is the
    evidence for which capability a pair actually needs."""
    return tuple(coordinate_descent(raw, c, target, **kw) for c in templates)
