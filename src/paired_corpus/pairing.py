"""Pair verification from signal evidence (DT-55B).

Filenames are hints only; a pair is confirmed by envelope correlation, duration
agreement, and phrase-count agreement. Real-corpus runs additionally require a
human confirmation flag before a pair is used for delta profiling.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.paired_corpus.alignment import global_offset_s, segment_phrases

CORR_EXACT = 0.60
CORR_PARTIAL = 0.35
DUR_TOL = 0.08          # |dur_raw - dur_wet| / max <= 8% (after edge silence trim)
PHRASE_AGREE = 0.5      # phrase-count ratio must be within [0.5, 2.0]


def _trim(x: np.ndarray, sr: int, gate_db: float = -50.0) -> np.ndarray:
    env = np.abs(x)
    peak = np.max(env) if len(env) else 0.0
    if peak <= 0:
        return x
    idx = np.where(env > peak * 10 ** (gate_db / 20))[0]
    return x[idx[0]: idx[-1] + 1] if len(idx) else x


@dataclass(frozen=True)
class PairEvidence:
    duration_ratio: float
    envelope_corr: float
    global_offset_s: float
    raw_phrases: int
    wet_phrases: int
    verdict: str    # verified_exact_pair | partially_matchable | incorrect_pair | unusable


def classify_pair(raw: np.ndarray, wet: np.ndarray, sr: int) -> PairEvidence:
    raw_t, wet_t = _trim(raw, sr), _trim(wet, sr)
    if len(raw_t) < sr or len(wet_t) < sr:
        return PairEvidence(0.0, 0.0, 0.0, 0, 0, "unusable")
    dur_r, dur_w = len(raw_t) / sr, len(wet_t) / sr
    dur_ratio = abs(dur_r - dur_w) / max(dur_r, dur_w)
    offset, corr = global_offset_s(raw_t, wet_t, sr)
    n_raw = len(segment_phrases(raw_t, sr))
    n_wet = len(segment_phrases(wet_t, sr))
    phrase_ok = (
        n_raw > 0 and n_wet > 0
        and PHRASE_AGREE <= (n_wet / n_raw) <= 1.0 / PHRASE_AGREE
    )
    # Envelope correlation is the primary evidence. Phrase-count agreement is a
    # soft corroborator only: reverb tails merge wet phrases on real material, so
    # a strong correlation (>= 0.75) overrides phrase-count disagreement.
    if corr >= CORR_EXACT and dur_ratio <= DUR_TOL and (phrase_ok or corr >= 0.75):
        verdict = "verified_exact_pair"
    elif corr >= CORR_PARTIAL:
        verdict = "partially_matchable"
    else:
        verdict = "incorrect_pair"
    return PairEvidence(round(dur_ratio, 4), round(corr, 4), round(offset, 4),
                        n_raw, n_wet, verdict)
