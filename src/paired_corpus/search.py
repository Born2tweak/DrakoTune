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

**N-018 correction.** Searching the registry's ranges alone is not enough. Given
only "is this safe to render?", the search won by highpassing a rap vocal at
330 Hz and compressing at 20:1 — inside every safe range, destructive as audio,
and it beat the objective by 62%. The default space is therefore *admissible*:
registry-safe AND within plausible-vocal-treatment bounds taken from the
repository's approved references, with an over-compression guard and a
preservation floor raised from 5 dB to 12 dB. `LEGACY_TEMPLATES` retains the
registry-only space solely to reproduce the superseded runs.

Any future objective change must be adversarially tested the same way: construct
a deliberately destructive candidate and require it to lose
(`tests/test_oracle_search.py::test_the_chain_that_won_under_the_old_objective_is_now_rejected`).

Diagnostic only. Nothing here authors a plan, tunes a threshold, or promotes
anything; it measures what the existing registry can and cannot reach.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

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
#
# N-018: at 5 dB this floor was the BINDING constraint — winning chains sat at
# 5.4-6.6 dB, i.e. the search spent every dB of destruction it was allowed. 12 dB
# is the declared floor for admissible searches; the 5 dB value is retained only
# to reproduce the superseded runs.
SI_SDR_FLOOR_DB = 12.0
SI_SDR_FLOOR_LEGACY_DB = 5.0
# Over-compression guard. `underground_vocal_engineering_reference.md` puts the
# over-compressed range at 6-10 dB crest and the sweet spot at 10-14 dB, so a
# candidate may not crush crest below 8 dB, nor remove more than 6 dB of the
# raw's crest.
CREST_FLOOR_DB = 8.0
MAX_CREST_LOSS_DB = 6.0
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
    """One processor position in a chain, with the params the search may move.

    `bounds` narrows a parameter below the registry's safe range. The registry's
    range answers "is this safe to render?"; it does NOT answer "is this a
    plausible vocal treatment?". N-018: given only the registry's ranges the
    search won by highpassing a rap vocal at 330 Hz and compressing at 20:1 —
    safe to render, destructive as audio, and it beat the objective. Admissible
    bounds come from the repository's own approved references
    (`docs/research/underground_vocal_engineering_reference.md`,
    `docs/research/vocal_chain_research.md`), never from fitting this corpus.
    """
    processor: str
    params: dict[str, float]
    search: tuple[str, ...]
    bounds: dict[str, tuple[float, float]] = field(default_factory=dict)

    def range_for(self, key: str) -> tuple[float, float]:
        """Effective search range: the narrower of admissible and registry-safe."""
        lo, hi = PROCESSORS[self.processor].safe_ranges[key]
        if key in self.bounds:
            blo, bhi = self.bounds[key]
            lo, hi = max(lo, blo), min(hi, bhi)
        return lo, hi


@dataclass(frozen=True)
class Chain:
    name: str
    slots: tuple[Slot, ...]

    @property
    def n_search_params(self) -> int:
        return sum(len(s.search) for s in self.slots)


# Admissible bounds, each traceable to a repository research reference. These are
# PRIORS, declared up front, never fitted to the paired corpus.
#   HP 60-120 Hz            - reference: 20-80 Hz is rumble to remove; a vocal
#                             highpass belongs below the chest register.
#   low-mid 200-800 Hz      - reference: 250-500 Hz "mud zone", 400-700 Hz boxiness.
#   low-mid gain +/-6 dB    - reference: mud cut -2..-4 dB is the professional norm;
#                             +/-6 leaves headroom on both sides without absurdity.
#   presence 2-6 kHz        - reference: 2-4 kHz presence, 3.5-6 kHz harshness.
#   air shelf 8-14 kHz,     - reference: shelf at 10 kHz, "+1.5-2.5 dB max";
#     +/-3 dB                 +/-3 dB is one step of headroom beyond the stated max.
#   gate -60..-35 dB        - a vocal gate sits well below the performance floor.
#   compressor 1.5-4.0:1,   - reference: "Compression 3:1-4:1, 15ms attack";
#     threshold -30..-12      attack sweet spot 10-20 ms.
ADMISSIBLE: dict[str, dict[str, tuple[float, float]]] = {
    "hp": {"cutoff_frequency_hz": (60.0, 120.0)},
    "lowmid": {"cutoff_frequency_hz": (200.0, 800.0), "gain_db": (-6.0, 6.0),
               "q": (0.5, 2.0)},
    "mid": {"cutoff_frequency_hz": (2000.0, 6000.0), "gain_db": (-6.0, 6.0),
            "q": (1.0, 4.0)},
    "air": {"cutoff_frequency_hz": (8000.0, 14000.0), "gain_db": (-3.0, 3.0)},
    "gate": {"threshold_db": (-60.0, -35.0), "release_ms": (100.0, 400.0)},
    "comp": {"threshold_db": (-30.0, -12.0), "ratio": (1.5, 4.0)},
}


def _hp(admissible: bool = True) -> Slot:
    return Slot("HighpassFilter", {"cutoff_frequency_hz": 90.0}, ("cutoff_frequency_hz",),
                ADMISSIBLE["hp"] if admissible else {})


def _lowmid(admissible: bool = True) -> Slot:
    # Bidirectional by construction: PeakFilter cuts and boosts, so the search can
    # ADD low-mid body as readily as remove it.
    return Slot("PeakFilter", {"cutoff_frequency_hz": 300.0, "gain_db": 0.0, "q": 0.8},
                ("cutoff_frequency_hz", "gain_db", "q"),
                ADMISSIBLE["lowmid"] if admissible else {})


def _mid(admissible: bool = True) -> Slot:
    return Slot("PeakFilter", {"cutoff_frequency_hz": 3500.0, "gain_db": 0.0, "q": 1.4},
                ("cutoff_frequency_hz", "gain_db", "q"),
                ADMISSIBLE["mid"] if admissible else {})


def _air(admissible: bool = True) -> Slot:
    return Slot("HighShelfFilter", {"cutoff_frequency_hz": 8000.0, "gain_db": 0.0, "q": 0.7},
                ("cutoff_frequency_hz", "gain_db"),
                ADMISSIBLE["air"] if admissible else {})


def _gate(admissible: bool = True) -> Slot:
    # C-1: the planner's NoiseGate spec is strength-invariant (fixed -42 dB), so
    # denoising had only ever been tested at one threshold. Here it is searched.
    return Slot("NoiseGate", {"threshold_db": -42.0, "attack_ms": 1.0, "release_ms": 250.0},
                ("threshold_db", "release_ms"),
                ADMISSIBLE["gate"] if admissible else {})


def _comp(admissible: bool = True) -> Slot:
    return Slot("Compressor",
                {"threshold_db": -18.0, "ratio": 2.5, "attack_ms": 15.0, "release_ms": 75.0},
                ("threshold_db", "ratio"),
                ADMISSIBLE["comp"] if admissible else {})


def _ladder(admissible: bool) -> tuple[Chain, ...]:
    return (
        Chain("t1_hp_lowmid", (_hp(admissible), _lowmid(admissible))),
        Chain("t2_tonal", (_hp(admissible), _lowmid(admissible), _mid(admissible))),
        Chain("t3_tonal_air", (_hp(admissible), _lowmid(admissible), _mid(admissible),
                               _air(admissible))),
        Chain("t4_tonal_air_gate", (_hp(admissible), _lowmid(admissible), _mid(admissible),
                                    _air(admissible), _gate(admissible))),
        Chain("t5_full", (_hp(admissible), _lowmid(admissible), _mid(admissible),
                          _air(admissible), _gate(admissible), _comp(admissible))),
    )


# Default search space: admissible bounds + the N-018 preservation guards.
TEMPLATES: tuple[Chain, ...] = _ladder(admissible=True)
TEMPLATES_BY_NAME = {c.name: c for c in TEMPLATES}
# Registry-bounded only. Retained solely to reproduce the superseded N-017 runs;
# N-018 showed this space is won by destructive chains. Do not report results
# from it as capability or quality evidence.
LEGACY_TEMPLATES: tuple[Chain, ...] = _ladder(admissible=False)
LEGACY_TEMPLATES_BY_NAME = {c.name: c for c in LEGACY_TEMPLATES}


def contract(templates: tuple[Chain, ...] = TEMPLATES) -> dict:
    """The space and guards a run actually enforced, as data.

    N-018 landed because a report *described* a contract the code no longer ran
    (registry-only space, 5 dB floor) while the code enforced another. Reports are
    evidence; a report that misstates its own method is worse than no report. Every
    generated artifact therefore takes its method text from here, and
    `tests/test_oracle_search.py` asserts the two cannot drift apart.
    """
    admissible = any(slot.bounds for c in templates for slot in c.slots)
    return {
        "space": "admissible" if admissible else "registry_safe_only",
        "space_note": (
            "registry `safe_ranges` INTERSECTED with plausible-vocal bounds cited "
            "from docs/research/ (never fitted to the corpus)"
            if admissible else
            "registry `safe_ranges` only — the N-018-discredited space, retained "
            "solely to reproduce superseded runs; not capability or quality evidence"
        ),
        "si_sdr_floor_db": SI_SDR_FLOOR_DB,
        "crest_floor_db": CREST_FLOOR_DB,
        "max_crest_loss_db": MAX_CREST_LOSS_DB,
        "ceiling_dbfs": round(20.0 * float(np.log10(CEILING)), 2),
        "clipping_allowed": False,
        "templates": [c.name for c in templates],
        "objective": (
            "mean scaled |wet − candidate| over aligned phrases on "
            f"{', '.join(AXES)} — a spectral/dynamics distance to a lossy wet "
            "reference, NOT perceptual quality (Q-016 open)"
        ),
    }


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
    crest_db: float = 0.0
    crest_loss_db: float = 0.0
    rejected_for: tuple[str, ...] = ()


def _crest_db(x: np.ndarray) -> float:
    if x.size == 0:
        return 0.0
    rms = float(np.sqrt(np.mean(np.square(x.astype(np.float64))) + 1e-20))
    peak = float(np.max(np.abs(x)) + 1e-20)
    return 20.0 * float(np.log10(peak / rms))


# SI-SDR over a whole take costs about as much as the render itself (measured:
# ~86%), so the search estimates it on windows and the reported result recomputes
# it over the full signal.
#
# **A single centred window was not a safe estimate.** On the 2026-07-26 corpus run
# two winners passed the search's centred-window estimate and then reported 7.3 dB
# and 4.9 dB full-signal — under a floor declared at 12 dB. A guard measured on a
# proxy that disagrees with the reported metric is not a guard. The estimate is now
# the MINIMUM over several evenly spaced windows, which tracks the worst-behaved
# part of a take instead of whatever the middle happens to contain, and
# `coordinate_descent` additionally re-checks its winner on the full signal and
# fails closed.
SI_SDR_WINDOW_S = 30.0
SI_SDR_WINDOWS = 5


def _preservation_db(raw: np.ndarray, audio: np.ndarray, full: bool) -> float:
    """Worst-case SI-SDR estimate (dB). `full` measures the whole signal exactly."""
    n = min(len(audio), len(raw))
    width = int(SI_SDR_WINDOW_S * SR)
    if full or n <= width:
        return float(si_sdr(raw[:n], audio[:n]))
    # Deterministic, evenly spaced, non-overlapping-where-possible windows.
    starts = np.linspace(0, n - width, SI_SDR_WINDOWS).round().astype(int)
    return min(float(si_sdr(raw[s:s + width], audio[s:s + width]))
               for s in dict.fromkeys(starts.tolist()))


def evaluate(raw: np.ndarray, chain: Chain, target: WetTarget,
             full_si_sdr: bool = False,
             si_sdr_floor_db: float = SI_SDR_FLOOR_DB) -> Evaluation:
    """Render a chain and score it. Inadmissible candidates are penalized, and the
    reason is reported rather than silently folded into a number."""
    out, _ = execute_plan(raw, SR, chain_to_plan(chain))
    audio = (out[:, 0] if out.ndim == 2 else out).astype(np.float32)
    return evaluate_audio(raw, audio, target, full_si_sdr, si_sdr_floor_db)


def evaluate_audio(raw: np.ndarray, audio: np.ndarray, target: WetTarget,
                   full_si_sdr: bool = False,
                   si_sdr_floor_db: float = SI_SDR_FLOOR_DB) -> Evaluation:
    """Score already-rendered audio — the guarded objective, as a function of audio.

    Split out from `evaluate` so the certification battery can put the SAME scoring
    the search uses under audit, including candidates no chain in the search space
    can author. An objective that is only reachable through the search cannot be
    audited independently of it.
    """
    peak = float(np.max(np.abs(audio)) + 1e-12)
    clip = float(np.mean(np.abs(audio) >= 0.999))
    sdr = _preservation_db(raw, audio, full_si_sdr)
    crest = _crest_db(audio)
    crest_loss = _crest_db(raw) - crest
    distance = composite_distance(audio, target)

    rejected: list[str] = []
    if peak > CEILING + 1e-3:
        rejected.append("ceiling")
    if clip > 0.0:
        rejected.append("clipping")
    if sdr < si_sdr_floor_db:
        rejected.append("si_sdr")
    if crest < CREST_FLOOR_DB:
        rejected.append("crest_floor")
    if crest_loss > MAX_CREST_LOSS_DB:
        rejected.append("crest_loss")
    safe = not rejected
    penalized = distance if safe else (
        distance + PENALTY if np.isfinite(distance) else float("inf"))
    return Evaluation(distance, penalized, round(peak, 4), round(clip, 6),
                      round(sdr, 3), safe, round(crest, 3), round(crest_loss, 3),
                      tuple(rejected))


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
    at_bound: tuple[str, ...]      # params resting on an effective search edge
    # Full-signal re-check of the winner. The search scores candidates on a
    # windowed SI-SDR estimate; if the exact measurement disagrees, the winner is
    # NOT admissible and must not be reported as one (fail closed).
    final_admissible: bool = True
    final_rejected_for: tuple[str, ...] = ()


def _axis_values(lo: float, hi: float, current: float, span: float,
                 n: int) -> list[float]:
    """Candidate values around `current`, clipped to [lo, hi], endpoints included."""
    half = (hi - lo) * span / 2.0
    vals = np.linspace(current - half, current + half, n)
    vals = np.clip(vals, lo, hi)
    return sorted({round(float(v), 4) for v in vals} | {lo, hi})


def coordinate_descent(raw: np.ndarray, chain: Chain, target: WetTarget,
                       passes: int = 3, points: int = 5,
                       max_evaluations: int = 400,
                       si_sdr_floor_db: float = SI_SDR_FLOOR_DB) -> SearchResult:
    """Deterministic coordinate descent inside the registry's safe ranges.

    One coordinate at a time, contracting the search span each pass. No RNG, so
    a rerun on the same inputs produces the same chain — a requirement for this
    to count as evidence.
    """
    best = chain
    base = evaluate(raw, chain, target, si_sdr_floor_db=si_sdr_floor_db)
    best_score, start = base.penalized, base.distance
    evals, converged = 1, False
    coords = [(i, key) for i, slot in enumerate(chain.slots) for key in slot.search]

    for p in range(passes):
        improved = False
        span = 1.0 / (2 ** p)                       # 100% -> 50% -> 25% of range
        for slot_i, key in coords:
            if evals >= max_evaluations:
                break
            lo, hi = best.slots[slot_i].range_for(key)
            current = min(max(best.slots[slot_i].params[key], lo), hi)
            for value in _axis_values(lo, hi, current, span, points):
                if value == current or evals >= max_evaluations:
                    continue
                slots = list(best.slots)
                params = dict(slots[slot_i].params)
                params[key] = value
                slots[slot_i] = replace(slots[slot_i], params=params)
                cand = Chain(best.name, tuple(slots))
                score = evaluate(raw, cand, target,
                                 si_sdr_floor_db=si_sdr_floor_db).penalized
                evals += 1
                if score < best_score - 1e-9:
                    best, best_score, improved = cand, score, True
                    current = value
        if not improved:
            converged = True
            break

    final = evaluate(raw, best, target, full_si_sdr=True,
                     si_sdr_floor_db=si_sdr_floor_db)
    at_bound = []
    for slot_i, key in coords:
        lo, hi = best.slots[slot_i].range_for(key)
        value = best.slots[slot_i].params[key]
        if abs(value - lo) < 1e-6 or abs(value - hi) < 1e-6:
            at_bound.append(f"{best.slots[slot_i].processor}.{key}")
    return SearchResult(
        chain_name=chain.name, best_chain=best, best_distance=final.distance,
        start_distance=start, evaluations=evals, passes=min(p + 1, passes),
        converged=converged, si_sdr_db=final.si_sdr_db, peak=final.peak,
        at_bound=tuple(at_bound),
        final_admissible=final.safe, final_rejected_for=final.rejected_for,
    )


def _warm_start(chain: Chain, previous: Chain | None) -> Chain:
    """Seed a template with the previous (prefix) template's solution.

    Each template in the ladder extends the one before it, so without this a
    richer template can finish WORSE than its own prefix: greedy coordinate
    descent is path-dependent, and adding a coordinate changes the path. That
    would make "the smallest template that suffices" meaningless. Warm-starting
    makes the ladder monotone by construction — the richer template begins from
    the poorer one's answer with the extra slot neutral, so it can only improve.
    """
    if previous is None:
        return chain
    slots = list(chain.slots)
    for i, prev_slot in enumerate(previous.slots):
        if i < len(slots) and slots[i].processor == prev_slot.processor:
            slots[i] = replace(slots[i], params=dict(prev_slot.params))
    return Chain(chain.name, tuple(slots))


def ablate(raw: np.ndarray, target: WetTarget,
           templates: tuple[Chain, ...] = TEMPLATES,
           **kw) -> tuple[SearchResult, ...]:
    """Search every capability template, warm-started along the ladder.

    The distance each template REACHES is the evidence for which capability a
    pair actually needs — which only holds if the ladder is monotone, hence the
    warm start.
    """
    results: list[SearchResult] = []
    previous: Chain | None = None
    for chain in templates:
        result = coordinate_descent(raw, _warm_start(chain, previous), target, **kw)
        results.append(result)
        previous = result.best_chain
    return tuple(results)
