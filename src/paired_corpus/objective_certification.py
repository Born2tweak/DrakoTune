"""Fail-closed certification battery for candidate objectives (DT-77 C-4).

`objective_audit` answers one question — can a destructive candidate beat an
honest one? That is necessary and nowhere near sufficient. This module states the
full set of properties an objective must hold before any result measured with it
may be reported, and checks them mechanically.

Three design commitments, each of them a lesson this project paid for:

1. **Fail closed.** A property that cannot be evaluated is not a pass. `UNTESTABLE`
   blocks certification exactly as `FAIL` does. The N-016 error — absence of
   evidence used as evidence — is otherwise trivially re-entered here.

2. **Structural soundness is not perceptual validity.** `PERCEPTUAL_ALIGNMENT` is
   permanently `UNTESTABLE` while DEF-003 stands: no listening data exists, so no
   metric in this repository can be shown to track what a listener hears. That is
   why `certified_for_production` is currently unreachable BY CONSTRUCTION, and it
   should stay unreachable until listening evidence exists rather than being
   quietly redefined. `structurally_sound` is the weaker verdict this battery can
   actually deliver.

3. **Pathologies are generated, not listed.** A curated catalogue only contains the
   exploits someone already imagined — which is how N-018 survived a review that
   already had adversarial tests in it.

Diagnostic only. Nothing here authors a plan, tunes a threshold, or promotes
anything.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum

import numpy as np

from src.paired_corpus.objective_audit import (
    PATHOLOGIES,
    Objective,
    Pathology,
    generated_pathologies,
    render,
)


# A constraint answers "may this candidate be considered at all?" — separate from
# how good it is. Keeping the two apart is what stops a rejection from reading as
# a score.
Admissibility = Callable[[np.ndarray], bool]


class Verdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    # Not "unknown, assume fine". Blocks certification exactly like FAIL.
    UNTESTABLE = "untestable"


@dataclass(frozen=True)
class PropertyResult:
    name: str
    verdict: Verdict
    detail: str
    measurements: dict


@dataclass(frozen=True)
class CertificationReport:
    properties: tuple[PropertyResult, ...]

    def _by(self, verdict: Verdict) -> tuple[str, ...]:
        return tuple(p.name for p in self.properties if p.verdict is verdict)

    @property
    def failed(self) -> tuple[str, ...]:
        return self._by(Verdict.FAIL)

    @property
    def untestable(self) -> tuple[str, ...]:
        return self._by(Verdict.UNTESTABLE)

    @property
    def structurally_sound(self) -> bool:
        """Every property that CAN be checked mechanically holds.

        This is the strongest verdict available without listening data. It means
        the objective is not obviously broken — not that it measures quality.
        """
        return not self.failed

    @property
    def certified_for_production(self) -> bool:
        """Fail-closed: every property, including the ones nothing can test yet."""
        return not self.failed and not self.untestable

    def as_dict(self) -> dict:
        return {
            "structurally_sound": self.structurally_sound,
            "certified_for_production": self.certified_for_production,
            "failed": list(self.failed),
            "untestable": list(self.untestable),
            "properties": [
                {"name": p.name, "verdict": p.verdict.value, "detail": p.detail,
                 "measurements": p.measurements}
                for p in self.properties
            ],
        }


# ---------------------------------------------------------------------------
# Individual properties
# ---------------------------------------------------------------------------

def _finite(x: float) -> bool:
    return bool(np.isfinite(x))


def check_determinism(objective: Objective, candidate: np.ndarray) -> PropertyResult:
    """The same input must score the same. Without this nothing else is evidence."""
    scores = [float(objective(candidate.copy())) for _ in range(3)]
    same = max(scores) - min(scores) == 0.0
    return PropertyResult(
        "DETERMINISM", Verdict.PASS if same else Verdict.FAIL,
        "repeat scoring of one candidate is bit-identical" if same else
        f"repeat scoring drifted by {max(scores) - min(scores):.3e}",
        {"scores": scores})


def check_identity_optimum(objective: Objective, wet: np.ndarray,
                           raw: np.ndarray) -> PropertyResult:
    """The target itself must be the best-scoring candidate.

    An objective whose optimum is not the thing it is measuring distance TO cannot
    have its minimum interpreted as "closest to the reference".
    """
    s_wet, s_raw = float(objective(wet)), float(objective(raw))
    ok = _finite(s_wet) and _finite(s_raw) and s_wet < s_raw
    return PropertyResult(
        "IDENTITY_OPTIMUM", Verdict.PASS if ok else Verdict.FAIL,
        f"target scores {s_wet:.4f} vs untreated raw {s_raw:.4f}",
        {"wet": s_wet, "raw": s_raw})


def check_monotonicity(objective: Objective, raw: np.ndarray, wet: np.ndarray,
                       steps: int = 6) -> PropertyResult:
    """Interpolating raw→target must not make the score worse.

    Tested on a straight crossfade, which is the one path along which "closer to
    the reference" has an unambiguous meaning. A non-monotone objective can reward
    a candidate for moving AWAY from the target, which is how a search ends up
    somewhere no one asked it to go.
    """
    n = min(len(raw), len(wet))
    alphas = np.linspace(0.0, 1.0, steps)
    scores = [float(objective(((1 - a) * raw[:n] + a * wet[:n]).astype(np.float32)))
              for a in alphas]
    inversions = [(round(float(alphas[i]), 3), scores[i], scores[i + 1])
                  for i in range(len(scores) - 1) if scores[i + 1] > scores[i] + 1e-9]
    ok = not inversions and all(_finite(s) for s in scores)
    return PropertyResult(
        "MONOTONICITY", Verdict.PASS if ok else Verdict.FAIL,
        "score decreases along the raw→target crossfade" if ok else
        f"{len(inversions)} inversion(s) along the crossfade",
        {"alphas": [round(float(a), 3) for a in alphas], "scores": scores,
         "inversions": inversions})


def check_level_invariance(objective: Objective, candidate: np.ndarray,
                           gains_db: Sequence[float] = (-6.0, 6.0),
                           tolerance: float = 1e-3) -> PropertyResult:
    """A pure level change must not move the score.

    Loudness inflation is the cheapest exploit of any level-sensitive metric, and
    the registry permits +12 dB of clean gain. An objective that fails this can be
    improved by turning it up.
    """
    base = float(objective(candidate))
    moved = {}
    for g in gains_db:
        scaled = np.clip(candidate * (10 ** (g / 20.0)), -1.0, 1.0).astype(np.float32)
        moved[f"{g:+.0f}dB"] = float(objective(scaled))
    worst = max(abs(v - base) for v in moved.values()) if moved else float("inf")
    ok = _finite(base) and worst <= tolerance
    return PropertyResult(
        "LEVEL_INVARIANCE", Verdict.PASS if ok else Verdict.FAIL,
        f"largest score change under a pure gain change: {worst:.3e}",
        {"base": base, "scaled": moved, "tolerance": tolerance})


def check_non_degenerate(objective: Objective, raw: np.ndarray,
                         honest: np.ndarray) -> PropertyResult:
    """Silence and noise must not beat an honest treatment.

    A metric that prefers silence has found that the cheapest way to resemble a
    reference is to stop being a signal.
    """
    rng = np.random.default_rng(0)
    degenerates = {
        "silence": np.zeros_like(raw),
        "white_noise": (rng.standard_normal(len(raw)) * 0.05).astype(np.float32),
    }
    s_honest = float(objective(honest))
    scores = {k: float(objective(v)) for k, v in degenerates.items()}
    beating = [k for k, v in scores.items() if _finite(v) and v < s_honest]
    return PropertyResult(
        "NON_DEGENERATE", Verdict.PASS if not beating else Verdict.FAIL,
        "silence and noise both score worse than the honest candidate" if not beating
        else f"degenerate candidate(s) beat the honest one: {beating}",
        {"honest": s_honest, **scores})


def check_honest_reference_validity(objective: Objective, raw: np.ndarray,
                                    honest: np.ndarray) -> PropertyResult:
    """The honest reference must at least beat doing nothing under this objective.

    Every gaming verdict is relative to the honest candidate, so a reference that
    scores WORSE than the untreated raw makes "a pathology beat the honest one"
    uninterpretable: near-no-op candidates then "win" without exploiting anything.

    Measured, not assumed: the fixed reference chain used here beats no-op under
    `composite_v1` and `mfcc_l1` and loses to it under `logmel_l1` and
    `mrstft_log`, because the surrogate's raw carries a room comb no registry
    processor can undo and the full-spectrum metrics are dominated by it. So a
    single reference cannot rank objectives against each other, and the verdict is
    UNTESTABLE rather than FAIL — the objective has not been shown to be bad, it
    has not been shown to be anything.
    """
    s_honest, s_noop = float(objective(honest)), float(objective(raw))
    ok = _finite(s_honest) and _finite(s_noop) and s_honest < s_noop
    return PropertyResult(
        "HONEST_REFERENCE_VALID", Verdict.PASS if ok else Verdict.UNTESTABLE,
        f"honest {s_honest:.4f} vs untreated {s_noop:.4f}" + ("" if ok else
        " — the reference loses to doing nothing, so gaming verdicts under this "
        "objective carry no information"),
        {"honest": s_honest, "noop": s_noop})


def check_gaming_resistance(objective: Objective, raw: np.ndarray, honest: np.ndarray,
                            pathologies: Sequence[Pathology],
                            admissible: Admissibility | None) -> PropertyResult:
    """No destructive candidate that the constraint ADMITS may outscore the honest one.

    Scored on the distance, with the constraint applied as a filter rather than as
    a penalty added to it. Folding the constraint into the number was itself a
    harness artifact when first written here: it rejected the honest candidate and
    the reference, after which every unpenalized candidate "won" and the objective
    looked gameable 37 ways. A constraint excludes candidates; it does not make the
    survivors better.
    """
    s_honest = float(objective(honest))
    if not (_finite(s_honest) and s_honest < float(objective(raw))):
        return PropertyResult(
            "GAMING_RESISTANCE", Verdict.UNTESTABLE,
            "not evaluated: the honest reference does not beat doing nothing under "
            "this objective, so 'a pathology outscores it' would say nothing about "
            "gaming (see HONEST_REFERENCE_VALID)",
            {"honest": s_honest, "noop": float(objective(raw))})
    beaten: list[tuple[str, float]] = []
    excluded = 0
    for path in pathologies:
        audio = render(raw, path.chain)
        if admissible is not None and not admissible(audio):
            excluded += 1
            continue
        score = float(objective(audio))
        if _finite(score) and score < s_honest:
            beaten.append((path.name, round(score, 5)))
    n_scored = len(pathologies) - excluded
    return PropertyResult(
        "GAMING_RESISTANCE", Verdict.PASS if not beaten else Verdict.FAIL,
        f"{n_scored} admitted destructive candidates all lose to the honest one "
        f"({excluded} excluded by the constraint)" if not beaten else
        f"{len(beaten)} of {n_scored} admitted destructive candidates outscore it",
        {"honest": s_honest, "n_pathologies": len(pathologies),
         "n_excluded_by_constraint": excluded, "n_scored": n_scored,
         "beaten_by": beaten[:20]})


def check_constraint_admits_honest(honest: np.ndarray,
                                   admissible: Admissibility | None) -> PropertyResult:
    """The preservation constraint must not reject a defensible treatment.

    N-019: the 12 dB SI-SDR floor rejects a -4 dB low-mid cut with gentle
    compression. A constraint that excludes honest work biases every measurement
    taken under it downward, so the number it produces is a lower bound.
    """
    if admissible is None:
        return PropertyResult(
            "CONSTRAINT_ADMITS_HONEST", Verdict.UNTESTABLE,
            "no admissibility constraint supplied; an objective used without one "
            "inherits none of the protection a bounded search provides", {})
    ok = bool(admissible(honest))
    return PropertyResult(
        "CONSTRAINT_ADMITS_HONEST", Verdict.PASS if ok else Verdict.FAIL,
        "the constraint admits the honest candidate" if ok else
        "the constraint REJECTS the honest candidate, so every result measured "
        "under it is a lower bound rather than an estimate (N-019)", {"admitted": ok})


def check_perceptual_alignment() -> PropertyResult:
    """Permanently UNTESTABLE while DEF-003 stands — and that is the finding.

    No listening data exists in this repository, so no metric here has ever been
    shown to correlate with what a listener hears. Any battery that reported this
    as a pass would be manufacturing the exact assurance the project lacks.
    """
    return PropertyResult(
        "PERCEPTUAL_ALIGNMENT", Verdict.UNTESTABLE,
        "no listening data exists (DEF-003); correlation with perceived quality "
        "cannot be measured, so it must not be assumed. Q-016 is the open question.",
        {"blocked_by": "DEF-003", "open_question": "Q-016"})


# ---------------------------------------------------------------------------
# Battery
# ---------------------------------------------------------------------------

def certify(objective: Objective, raw: np.ndarray, wet: np.ndarray,
            honest: np.ndarray,
            pathologies: Sequence[Pathology] | None = None,
            admissible: Admissibility | None = None) -> CertificationReport:
    """Run every property against one objective on one pair.

    `objective` is the DISTANCE alone and `admissible` the constraint, kept apart
    on purpose: the distance's properties (identity, monotonicity, invariance) are
    meaningless once a penalty is folded in, and the constraint's job is to exclude
    candidates rather than to reorder the survivors.

    A verdict belongs to (objective, pair): a metric can be sound on a gentle
    surrogate and gameable on real material, so a report is never a global claim
    about the objective.
    """
    catalogue = tuple(pathologies) if pathologies is not None else (
        PATHOLOGIES + generated_pathologies())
    return CertificationReport((
        check_determinism(objective, honest),
        check_identity_optimum(objective, wet, raw),
        check_monotonicity(objective, raw, wet),
        check_level_invariance(objective, honest),
        check_non_degenerate(objective, raw, honest),
        check_honest_reference_validity(objective, raw, honest),
        check_gaming_resistance(objective, raw, honest, catalogue, admissible),
        check_constraint_admits_honest(honest, admissible),
        check_perceptual_alignment(),
    ))
