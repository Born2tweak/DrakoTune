"""Adversarial audit for candidate objectives (DT-77 Track C-4 precondition).

Three times in the DT-55E thread a conclusion turned out to be an artifact of the
harness rather than a fact about the system, and N-018 turned that into a rule:

    Never treat whatever the harness optimises as a proxy for quality until a
    deliberately destructive candidate has been constructed and *required to lose*.

A rule that lives only in a document gets applied to the objective someone
remembers to test. This module makes it executable: given an objective, it renders
a fixed catalogue of **pathologies** — treatments that are safe to render, easy for
a spectral metric to like, and unacceptable to any listener — plus an **honest**
candidate, and reports which pathologies the objective prefers.

An objective that ranks any pathology above the honest candidate is *gameable*: no
capability, calibration or quality conclusion may be drawn from it. That is a
property of the objective alone, so it can be audited before a corpus is ever run.

This audits ONLY the ordering an objective imposes. It is not a perceptual model
and passing it does not make an objective perceptually valid — it makes it not
obviously invalid, which is the precondition Q-016 is open about, not an answer
to it.

Diagnostic only: nothing here authors a plan, tunes a threshold, or promotes
anything.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

from src.paired_corpus.search import SR, Chain, Slot, chain_to_plan
from src.dsp_engine import execute_plan

# An objective scores a rendered candidate; LOWER IS BETTER (a distance). Anything
# with the opposite polarity must be negated by the caller, which keeps the
# convention explicit rather than inferred.
Objective = Callable[[np.ndarray], float]


@dataclass(frozen=True)
class Pathology:
    """A treatment that is safe to render and destructive to listen to.

    `rationale` records WHY a spectral objective might like it, so a failure names
    the mechanism instead of only the verdict.
    """
    name: str
    chain: Chain
    rationale: str


def _slot(processor: str, **params: float) -> Slot:
    return Slot(processor, dict(params), ())


# The catalogue is deliberately drawn from what has already fooled this project.
# Each entry cites the run or test that produced it; new entries should too.
PATHOLOGIES: tuple[Pathology, ...] = (
    Pathology(
        "body_removal",
        Chain("body_removal", (_slot("HighpassFilter", cutoff_frequency_hz=330.0),)),
        "N-018: removes the whole chest/body region of a rap vocal; a cheap way to "
        "move every low-band ratio and the spectral tilt at once",
    ),
    Pathology(
        "crush",
        Chain("crush", (_slot("Compressor", threshold_db=-10.5, ratio=20.0,
                              attack_ms=15.0, release_ms=75.0),)),
        "N-018: ratio pinned at the registry maximum; buys `crest_db` directly",
    ),
    Pathology(
        "gate_chop",
        Chain("gate_chop", (_slot("NoiseGate", threshold_db=-15.75, attack_ms=1.0,
                                  release_ms=250.0),)),
        "N-018: gates above the performance floor, chopping word tails and breaths, "
        "while removing exactly the low-level content a noise-floor axis penalises",
    ),
    Pathology(
        "tilt_hack",
        Chain("tilt_hack", (_slot("HighShelfFilter", cutoff_frequency_hz=8000.0,
                                  gain_db=12.0, q=0.7),)),
        "buys `tilt_db_per_oct` with a shelf far beyond any documented air setting",
    ),
    Pathology(
        "wrong_direction_boost",
        Chain("wrong_direction_boost", (_slot("PeakFilter", cutoff_frequency_hz=300.0,
                                              gain_db=9.0, q=0.8),)),
        "N-018 CI reproduction: a +9 dB boost where the truth was an -8 dB cut, "
        "which still scored 47% under the discredited objective",
    ),
    Pathology(
        "everything_at_once",
        Chain("everything_at_once", (
            _slot("HighpassFilter", cutoff_frequency_hz=330.0),
            _slot("Compressor", threshold_db=-10.5, ratio=20.0, attack_ms=15.0,
                  release_ms=75.0),
        )),
        "the two cheapest axes bought together — the actual N-018 winning shape",
    ),
)


def honest_recovery_chain() -> Chain:
    """A competent, objective-INDEPENDENT answer for a surrogate pair.

    The honest reference must not be produced by optimising the objective under
    audit — that is circular, and an objective can pass by having a bad optimum
    that its own search reproduces. `surrogates.TRUTH` states the transformation
    the wet applied (a -4 dB low-mid cut at 250-500 Hz plus gentle compression),
    so its recovery is written out here directly: this is what an engineer who
    already knew the answer would do, chosen without consulting any score.
    """
    return Chain("honest_recovery", (
        _slot("PeakFilter", cutoff_frequency_hz=350.0, gain_db=-4.0, q=0.8),
        _slot("Compressor", threshold_db=-18.0, ratio=2.5, attack_ms=15.0,
              release_ms=75.0),
    ))


def render(raw: np.ndarray, chain: Chain) -> np.ndarray:
    out, _ = execute_plan(raw, SR, chain_to_plan(chain))
    return (out[:, 0] if out.ndim == 2 else out).astype(np.float32)


@dataclass(frozen=True)
class PathologyScore:
    name: str
    score: float
    beats_honest: bool
    rationale: str


@dataclass(frozen=True)
class AuditReport:
    """Ordering audit of one objective. `gameable` is the verdict that matters."""
    honest_score: float
    pathologies: tuple[PathologyScore, ...]
    # Score of the untouched raw. Not a pass/fail axis — some treatment is
    # supposed to help — but a pathology that also beats doing nothing tells you
    # the objective actively rewards the damage rather than merely tolerating it.
    noop_score: float = float("nan")

    @property
    def rewarded_over_noop(self) -> tuple[str, ...]:
        if not np.isfinite(self.noop_score):
            return ()
        return tuple(p.name for p in self.pathologies
                     if np.isfinite(p.score) and p.score < self.noop_score)

    @property
    def gameable(self) -> bool:
        return any(p.beats_honest for p in self.pathologies)

    @property
    def beaten_by(self) -> tuple[str, ...]:
        return tuple(p.name for p in self.pathologies if p.beats_honest)

    def as_dict(self) -> dict:
        return {
            "gameable": self.gameable,
            "beaten_by": list(self.beaten_by),
            "honest_score": self.honest_score,
            "noop_score": self.noop_score,
            "rewarded_over_noop": list(self.rewarded_over_noop),
            "pathologies": [
                {"name": p.name, "score": p.score, "beats_honest": p.beats_honest,
                 "rationale": p.rationale}
                for p in self.pathologies
            ],
        }


def audit_objective(objective: Objective, raw: np.ndarray, honest: np.ndarray,
                    pathologies: Sequence[Pathology] = PATHOLOGIES) -> AuditReport:
    """Score `honest` and every pathology under `objective` (lower is better).

    `honest` is the candidate a competent engineer would defend — for a surrogate
    pair whose transformation is known, the recovery of that transformation. The
    audit asks one question: does the objective rank any destructive candidate
    above it?

    A non-finite pathology score counts as NOT beating the honest candidate: an
    objective that cannot measure a candidate has not endorsed it.
    """
    honest_score = float(objective(honest))
    noop_score = float(objective(raw))
    scores = []
    for path in pathologies:
        score = float(objective(render(raw, path.chain)))
        beats = bool(np.isfinite(score) and score < honest_score)
        scores.append(PathologyScore(path.name, score, beats, path.rationale))
    return AuditReport(honest_score, tuple(scores), noop_score)
