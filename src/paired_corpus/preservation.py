"""Candidate preservation constraint measured on the PERFORMANCE (N-021 follow-up).

The constraint in use floors SI-SDR against the raw. N-021 showed that is not a
mis-tuned threshold but a mis-pointed one: the better a treatment corrects the raw,
the further it sits from the raw, so the exact inverse of a known degradation —
92 dB from the target — is rejected on every seed. No threshold value repairs a
constraint of that shape.

This module is a **candidate replacement**, offered to Q-016 with its evidence.
Nothing here is wired into the search: swapping the admissibility rule changes every
measured result, which is a decision, not a refactor.

What it measures, and what was rejected after measuring it:

- **`voiced_retention` — kept.** The fraction of the raw's voiced frames that
  survive in the candidate within 12 dB. Gating a performance removes word tails and
  breaths, and this is what sees it: on the noisy surrogates it reads 0.75-0.79 for
  a gate set above the performance floor and 1.000 for the exact inverse and for
  honest chains. Cheap (frame RMS only), so it can run inside a search.

- **pitch-contour correlation — REJECTED after measurement.** The obvious
  formulation, and it does not work: a 20:1 compressor scores a correlation of
  **1.000** (compression genuinely does not move pitch, so pitch can never catch the
  worst dynamics pathology), while the exact inverse scores 0.897 and honest chains
  score mid-pack — the tonal change that makes an answer CORRECT is what disturbs
  the tracker most. Including it would rebuild the same anti-correlation N-021
  found. It is recorded here so the idea is not re-proposed as new.

- **tonal destruction is deliberately NOT constrained here.** A +12 dB shelf or a
  330 Hz highpass leaves timing and dynamics intact; catching them is the
  objective's job, and on ground truth the objective does catch them (no pathology
  beats the exact inverse). A constraint that also judged tone would be a second,
  unvalidated objective wearing a guard's clothes.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SR = 44100
HOP = 512
# A frame counts as performance if it is within this much of the take's loudest
# frame. Wide enough to include quiet entrances and tails, narrow enough to exclude
# the noise floor a treatment is allowed to remove.
VOICED_RANGE_DB = 40.0
# How far a retained frame may drop before it counts as removed. 12 dB is well
# beyond any level change ordinary mixing applies to a single frame, and well inside
# what gating does to a word tail.
RETENTION_DROP_DB = 12.0
RETENTION_FLOOR = 0.95
CEILING = 0.977
# Carried over unchanged from the current contract: these guards are not what
# N-021 found wrong, and dropping them while replacing the floor would confound
# the comparison. Neither they nor retention catch extreme compression -- measured,
# not assumed -- so that remains the objective's job.
CREST_FLOOR_DB = 8.0
MAX_CREST_LOSS_DB = 6.0


def _frame_db(x: np.ndarray, hop: int = HOP) -> np.ndarray:
    n = max(len(x) // hop, 1)
    frames = np.array([x[i * hop:(i + 1) * hop] for i in range(n)], dtype=object)
    rms = np.array([float(np.sqrt(np.mean(np.square(f.astype(np.float64))) + 1e-20))
                    for f in frames])
    return 20.0 * np.log10(rms + 1e-12)


def _crest_db(x: np.ndarray) -> float:
    if x.size == 0:
        return 0.0
    rms = float(np.sqrt(np.mean(np.square(x.astype(np.float64))) + 1e-20))
    peak = float(np.max(np.abs(x)) + 1e-20)
    return 20.0 * float(np.log10(peak / rms))


@dataclass(frozen=True)
class Preservation:
    voiced_retention: float
    peak: float
    clipping_ratio: float
    crest_db: float
    crest_loss_db: float
    admitted: bool
    rejected_for: tuple[str, ...]


def performance_preservation(raw: np.ndarray, candidate: np.ndarray,
                             retention_floor: float = RETENTION_FLOOR) -> Preservation:
    """Does the candidate keep the performance the raw contains?

    Measured against the raw's *content* — which frames carry performance — rather
    than against the raw's waveform, so a correct tonal or dynamic treatment is not
    penalised for being far from its input.
    """
    e_raw, e_cand = _frame_db(raw), _frame_db(candidate)
    n = min(len(e_raw), len(e_cand))
    e_raw, e_cand = e_raw[:n], e_cand[:n]
    voiced = e_raw > (np.max(e_raw) - VOICED_RANGE_DB) if n else np.zeros(0, bool)
    retention = (float(np.mean(e_cand[voiced] > e_raw[voiced] - RETENTION_DROP_DB))
                 if voiced.any() else float("nan"))
    peak = float(np.max(np.abs(candidate)) + 1e-12) if candidate.size else 0.0
    clip = float(np.mean(np.abs(candidate) >= 0.999)) if candidate.size else 0.0

    crest = _crest_db(candidate)
    crest_loss = _crest_db(raw) - crest

    rejected: list[str] = []
    if not np.isfinite(retention) or retention < retention_floor:
        rejected.append("voiced_retention")
    if peak > CEILING + 1e-3:
        rejected.append("ceiling")
    if clip > 0.0:
        rejected.append("clipping")
    if crest < CREST_FLOOR_DB:
        rejected.append("crest_floor")
    if crest_loss > MAX_CREST_LOSS_DB:
        rejected.append("crest_loss")
    return Preservation(round(retention, 4) if np.isfinite(retention) else retention,
                        round(peak, 4), round(clip, 6), round(crest, 3),
                        round(crest_loss, 3), not rejected, tuple(rejected))


def admits(raw: np.ndarray, candidate: np.ndarray) -> bool:
    """Admissibility predicate in the shape the certification battery expects."""
    return performance_preservation(raw, candidate).admitted
