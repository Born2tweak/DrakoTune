"""Forced-engagement oracle probe (DT-55E, diagnostic only).

Answers the plan's question: is the champion->wet gap caused by the engine not
engaging, by a capability the registry does not have, or by the corpus being
unable to answer? Method: build candidate chains from the planner's OWN
treatments (`_ISSUE_SPECS`) — forcing engagement the champion currently gates
out — run them through the real executor (-0.2 dBFS ceiling enforced), and
measure per-axis distance to the aligned wet target.

Diagnostic only: no threshold is tuned, nothing is promoted, no claim is made.

Classification taxonomy (every pair lands in exactly ONE bucket):

  INCONCLUSIVE_ALIGNMENT  the pair cannot be measured — too few aligned phrases,
                          or a non-finite distance. MUST be excluded from every
                          aggregate; it is absence of evidence, not evidence.
  ENGAGEMENT_GAP          forcing the existing chain to engage closes >= 10% of
                          the composite distance -> the champion was under-engaging.
  MISSING_PROCESSOR       even the full forced chain moves <= 2% -> the registry
                          lacks the capability the professional chain applied.
  DATA_LIMITATION         movement lands in the 2-10% band: real but below what
                          this lossy, single-artist corpus can attribute.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from src.decision.planner import _ISSUE_SPECS, ProcessingAction, ProcessingPlan
from src.dsp_engine import execute_plan
from src.paired_corpus.alignment import AlignmentMap
from src.paired_corpus.deltas import phrase_features

SR = 44100
CEILING = 0.977

# Classification thresholds (predeclared; not tuned against results).
MIN_MEASURED_PHRASES = 3      # below this the pair cannot support a conclusion
ENGAGEMENT_IMPROVEMENT = 0.10  # >=10% composite reduction -> engagement gap
NULL_IMPROVEMENT = 0.02       # <=2% -> the existing chain cannot move this axis set

ENGAGEMENT_GAP = "engagement_gap"
MISSING_PROCESSOR = "missing_processor"
DATA_LIMITATION = "data_limitation"
INCONCLUSIVE_ALIGNMENT = "inconclusive_alignment"
CLASSIFICATIONS = (ENGAGEMENT_GAP, MISSING_PROCESSOR, DATA_LIMITATION,
                   INCONCLUSIVE_ALIGNMENT)

# Predeclared candidate chains, built from the planner's own issue specs at a
# fixed moderate strength. Order follows the specs' declared order.
CANDIDATES: dict[str, tuple[str, ...]] = {
    "forced_lowmid": ("rumble", "muddiness"),
    "forced_lowmid_denoise": ("rumble", "muddiness", "noise_floor"),
    "forced_full": ("rumble", "muddiness", "noise_floor", "harshness"),
}
AXES = ("lowmid_250_500", "harsh_2500_5000", "sib_5500_12000", "crest_db",
        "tilt_db_per_oct")


def build_plan(name: str, strength: float = 0.7) -> ProcessingPlan:
    specs = [(_ISSUE_SPECS[issue], issue) for issue in CANDIDATES[name]]
    specs.sort(key=lambda t: t[0].order)
    actions = tuple(
        ProcessingAction(
            id=f"oracle.{issue}", processor=spec.processor,
            parameters=spec.build(strength), strength=strength,
            reason=f"forced-engagement oracle probe ({name})",
            objective_id=f"obj.{issue}", reversible=True,
        )
        for spec, issue in specs
    )
    return ProcessingPlan(
        id=f"oracle-{name}", preset_profile="clean", objectives=(),
        actions=actions, skipped_processors=(), policy_version="oracle-1",
    )


def candidate_processors(name: str) -> tuple[str, ...]:
    """Processor names activated by a candidate chain (evidence, not a claim)."""
    if name == "champion":
        return ()
    return tuple(a.processor for a in build_plan(name).actions)


def _render(raw: np.ndarray, plan: ProcessingPlan) -> np.ndarray:
    out, _ = execute_plan(raw, SR, plan)
    return (out[:, 0] if out.ndim == 2 else out).astype(np.float32)


def _slice(x: np.ndarray, a: float, b: float) -> np.ndarray:
    i, j = max(int(a * SR), 0), min(int(b * SR), len(x))
    return x[i:j] if j > i else np.zeros(1, dtype=x.dtype)


def _axis_distance(cand: np.ndarray, wet: np.ndarray,
                   amap: AlignmentMap) -> tuple[dict, int]:
    """(mean |wet - candidate| per axis, n_measured_phrases). Lower = closer.

    Only phrases that survive slicing on BOTH sides are measured, so the count
    returned is the true evidence base — not the alignment map's optimistic total.
    """
    acc: dict[str, list[float]] = {a: [] for a in AXES}
    measured = 0
    for p in amap.aligned():
        cseg = _slice(cand, p.raw_start_s, p.raw_end_s)
        wseg = _slice(wet, p.wet_start_s, p.wet_end_s)
        if len(cseg) < SR // 10 or len(wseg) < SR // 10:
            continue
        measured += 1
        fc, fw = phrase_features(cseg, SR), phrase_features(wseg, SR)
        for a in AXES:
            acc[a].append(abs(fw[a] - fc[a]))
    return {a: round(float(np.mean(v)), 5) for a, v in acc.items() if v}, measured


@dataclass(frozen=True)
class CandidateResult:
    name: str
    peak: float
    clipping_ratio: float
    safe: bool
    axis_distance: dict
    n_measured_phrases: int = 0
    processors: tuple[str, ...] = ()


@dataclass(frozen=True)
class OracleProbe:
    pair_id: str
    champion_actions: int
    results: tuple[CandidateResult, ...]
    classification: str
    n_measured_phrases: int = 0
    champion_distance: float = float("inf")
    oracle_distance: float = float("inf")
    improvement_pct: float = 0.0
    best_candidate: str = ""
    active_processors: tuple[str, ...] = ()
    confidence: float = 0.0
    reason: str = ""

    @property
    def valid(self) -> bool:
        """Only valid probes may enter aggregate metrics."""
        return self.classification != INCONCLUSIVE_ALIGNMENT


def _composite(d: dict) -> float:
    """Scale band ratios (x10) to be comparable with dB axes; lower = closer."""
    if not d:
        return float("inf")
    scale = {"lowmid_250_500": 10, "harsh_2500_5000": 10, "sib_5500_12000": 10,
             "crest_db": 1, "tilt_db_per_oct": 1}
    return round(sum(d.get(a, 0) * s for a, s in scale.items()), 4)


def _confidence(improvement: float, n_phrases: int, classification: str) -> float:
    """Heuristic evidence-quality score in [0,1] — NOT a probability.

    Two multiplicative factors: how much evidence (measured phrases, saturating
    at 20) and how far the measurement sits from the nearest decision boundary
    (saturating at one full threshold width). A pair right on a boundary with a
    handful of phrases scores near zero; a large, unambiguous result scores near one.
    """
    if classification == INCONCLUSIVE_ALIGNMENT:
        return 0.0
    evidence = min(n_phrases / 20.0, 1.0)
    if improvement >= ENGAGEMENT_IMPROVEMENT:
        margin = improvement - ENGAGEMENT_IMPROVEMENT
    elif improvement <= NULL_IMPROVEMENT:
        margin = NULL_IMPROVEMENT - improvement
    else:                                  # inside the ambiguous middle band
        margin = min(improvement - NULL_IMPROVEMENT,
                     ENGAGEMENT_IMPROVEMENT - improvement)
    decisiveness = min(margin / ENGAGEMENT_IMPROVEMENT, 1.0)
    return round(evidence * decisiveness, 4)


def _classify(champ_d: float, best_d: float, n_phrases: int) -> tuple[str, str]:
    if n_phrases < MIN_MEASURED_PHRASES:
        return (INCONCLUSIVE_ALIGNMENT,
                f"only {n_phrases} measurable aligned phrases "
                f"(< {MIN_MEASURED_PHRASES}); nothing to measure")
    if not np.isfinite(champ_d) or not np.isfinite(best_d):
        return INCONCLUSIVE_ALIGNMENT, "non-finite distance (no comparable phrases)"
    if champ_d <= 0:
        return INCONCLUSIVE_ALIGNMENT, "champion distance is zero; ratio undefined"
    improvement = (champ_d - best_d) / champ_d
    if improvement >= ENGAGEMENT_IMPROVEMENT:
        return (ENGAGEMENT_GAP,
                f"forced engagement closed {improvement:.1%} of the composite distance")
    if improvement <= NULL_IMPROVEMENT:
        return (MISSING_PROCESSOR,
                f"full forced chain moved only {improvement:.1%}; existing registry "
                "cannot reach the wet target")
    return (DATA_LIMITATION,
            f"movement of {improvement:.1%} is below the attribution threshold for "
            "this lossy single-artist corpus")


def probe_pair(pair_id: str, raw: np.ndarray, wet: np.ndarray,
               amap: AlignmentMap, champion: np.ndarray, champion_actions: int,
               ) -> OracleProbe:
    results: list[CandidateResult] = []
    # Champion is the baseline candidate (often passthrough).
    for name, audio in [("champion", champion)] + [
        (n, _render(raw, build_plan(n))) for n in CANDIDATES
    ]:
        peak = float(np.max(np.abs(audio)) + 1e-12)
        clip = float(np.mean(np.abs(audio) >= 0.999))
        dist, measured = _axis_distance(audio, wet, amap)
        results.append(CandidateResult(
            name, round(peak, 4), round(clip, 6),
            peak <= CEILING + 1e-3 and clip == 0.0,
            dist, measured, candidate_processors(name),
        ))

    champ = next((r for r in results if r.name == "champion"), None)
    forced = [r for r in results if r.name != "champion" and r.safe]
    n_measured = champ.n_measured_phrases if champ else 0
    if champ is None or not forced:
        return OracleProbe(
            pair_id, champion_actions, tuple(results), INCONCLUSIVE_ALIGNMENT,
            n_measured, reason="no safe forced candidate to compare against",
        )
    champ_d = _composite(champ.axis_distance)
    best = min(forced, key=lambda r: _composite(r.axis_distance))
    best_d = _composite(best.axis_distance)
    classification, reason = _classify(champ_d, best_d, n_measured)
    improvement = (
        (champ_d - best_d) / champ_d
        if np.isfinite(champ_d) and np.isfinite(best_d) and champ_d > 0
        else 0.0
    )
    if classification == INCONCLUSIVE_ALIGNMENT:
        improvement = 0.0
    return OracleProbe(
        pair_id=pair_id, champion_actions=champion_actions, results=tuple(results),
        classification=classification, n_measured_phrases=n_measured,
        champion_distance=champ_d, oracle_distance=best_d,
        improvement_pct=round(improvement * 100.0, 3),
        best_candidate=best.name if classification != INCONCLUSIVE_ALIGNMENT else "",
        active_processors=best.processors if classification != INCONCLUSIVE_ALIGNMENT else (),
        confidence=_confidence(improvement, n_measured, classification),
        reason=reason,
    )


# --------------------------------------------------------------------------
# Aggregation (valid pairs only)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class OracleAggregate:
    n_total: int
    n_valid: int
    n_excluded: int
    median_improvement_pct: float
    mean_improvement_pct: float
    ci95_mean_improvement_pct: tuple[float, float]
    abstention_rate: float
    engagement_rate: float
    classification_counts: dict = field(default_factory=dict)
    processor_activation_counts: dict = field(default_factory=dict)


def _bootstrap_ci(values: list[float], iters: int = 5000,
                  seed: int = 20260725) -> tuple[float, float]:
    """Percentile bootstrap 95% CI of the mean. Small n -> deliberately wide."""
    if len(values) < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype=float)
    means = arr[rng.integers(0, len(arr), size=(iters, len(arr)))].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return (round(float(lo), 3), round(float(hi), 3))


def aggregate(probes: list[OracleProbe]) -> OracleAggregate:
    """Aggregate over VALID probes only; inconclusive pairs are excluded."""
    valid = [p for p in probes if p.valid]
    improvements = [p.improvement_pct for p in valid]
    counts: dict[str, int] = {c: 0 for c in CLASSIFICATIONS}
    for p in probes:
        counts[p.classification] = counts.get(p.classification, 0) + 1
    procs: dict[str, int] = {}
    for p in valid:
        for proc in p.active_processors:
            procs[proc] = procs.get(proc, 0) + 1
    abstain = sum(1 for p in valid if p.champion_actions == 0)
    return OracleAggregate(
        n_total=len(probes), n_valid=len(valid), n_excluded=len(probes) - len(valid),
        median_improvement_pct=round(float(np.median(improvements)), 3) if improvements else 0.0,
        mean_improvement_pct=round(float(np.mean(improvements)), 3) if improvements else 0.0,
        ci95_mean_improvement_pct=_bootstrap_ci(improvements),
        abstention_rate=round(abstain / len(valid), 4) if valid else 0.0,
        engagement_rate=round(1 - abstain / len(valid), 4) if valid else 0.0,
        classification_counts=counts,
        processor_activation_counts=dict(sorted(procs.items(), key=lambda kv: -kv[1])),
    )
