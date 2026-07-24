"""Global + phrase-level alignment for raw/wet pairs (DT-55B).

numpy-only signal alignment: RMS envelopes at a fixed frame rate, FFT
cross-correlation for the global offset, energy-gated phrase segmentation, and
per-phrase local refinement. Originals are never modified; callers pass float32
mono arrays (analysis copies).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ENV_HZ = 50               # envelope frame rate
PHRASE_MIN_S = 0.35
PHRASE_GAP_S = 0.15       # gaps shorter than this merge phrases
GATE_DB = -40.0           # relative to peak envelope
LOCAL_SEARCH_S = 0.15     # per-phrase refinement window
LOCAL_CORR_MIN = 0.5      # below -> unmatched
EDIT_DUR_TOL = 0.2        # >20% phrase-duration mismatch -> edited


def envelope(x: np.ndarray, sr: int, env_hz: int = ENV_HZ) -> np.ndarray:
    """RMS envelope at env_hz frames/second."""
    hop = max(int(sr / env_hz), 1)
    n = len(x) // hop
    if n == 0:
        return np.zeros(1, dtype=np.float64)
    frames = x[: n * hop].astype(np.float64).reshape(n, hop)
    return np.sqrt(np.mean(frames**2, axis=1) + 1e-20)


def _norm(e: np.ndarray) -> np.ndarray:
    e = e - np.mean(e)
    s = np.std(e)
    return e / s if s > 1e-12 else e


def global_offset_s(raw: np.ndarray, wet: np.ndarray, sr: int,
                    max_offset_s: float = 30.0) -> tuple[float, float]:
    """(offset_seconds, peak_correlation): shift applied to WET to match RAW.

    Positive offset means the wet performance starts LATER than the raw.
    Correlation is normalized cross-correlation of standardized envelopes.
    """
    ea, eb = _norm(envelope(raw, sr)), _norm(envelope(wet, sr))
    n = len(ea) + len(eb)
    corr = np.fft.irfft(np.fft.rfft(ea, n) * np.conj(np.fft.rfft(eb, n)), n)
    lags = np.arange(n)
    lags[lags > n // 2] -= n                      # wrap to signed lags
    max_lag = int(max_offset_s * ENV_HZ)
    mask = np.abs(lags) <= max_lag
    idx = np.argmax(corr[mask])
    lag = lags[mask][idx]
    denom = np.sqrt(np.sum(ea**2) * np.sum(eb**2)) + 1e-20
    peak = float(corr[mask][idx] / denom)
    return float(lag / ENV_HZ), peak


def segment_phrases(x: np.ndarray, sr: int) -> list[tuple[float, float]]:
    """Energy-gated phrase segments (start_s, end_s), merged across short gaps.

    The gate is adaptive: the louder of (peak-relative GATE_DB) and 3x the 10th-
    percentile envelope, so a noise/room floor sitting just above the fixed gate
    cannot merge every phrase into one segment.
    """
    env = envelope(x, sr)
    peak = np.max(env)
    if peak <= 0:
        return []
    thresh = max(peak * (10 ** (GATE_DB / 20)), float(np.percentile(env, 10)) * 3.0)
    active = env > thresh
    segments: list[tuple[float, float]] = []
    start = None
    for i, on in enumerate(active):
        if on and start is None:
            start = i
        elif not on and start is not None:
            segments.append((start / ENV_HZ, i / ENV_HZ))
            start = None
    if start is not None:
        segments.append((start / ENV_HZ, len(active) / ENV_HZ))
    # merge gaps < PHRASE_GAP_S, drop segments < PHRASE_MIN_S
    merged: list[tuple[float, float]] = []
    for seg in segments:
        if merged and seg[0] - merged[-1][1] < PHRASE_GAP_S:
            merged[-1] = (merged[-1][0], seg[1])
        else:
            merged.append(seg)
    return [s for s in merged if s[1] - s[0] >= PHRASE_MIN_S]


@dataclass(frozen=True)
class PhraseMatch:
    raw_start_s: float
    raw_end_s: float
    wet_start_s: float
    wet_end_s: float
    local_corr: float
    verdict: str          # "aligned" | "unmatched" | "edited"


@dataclass(frozen=True)
class AlignmentMap:
    global_offset_s: float
    global_corr: float
    phrases: tuple[PhraseMatch, ...]

    def aligned(self) -> tuple[PhraseMatch, ...]:
        return tuple(p for p in self.phrases if p.verdict == "aligned")


def _slice(x: np.ndarray, sr: int, start_s: float, end_s: float) -> np.ndarray:
    a, b = max(int(start_s * sr), 0), min(int(end_s * sr), len(x))
    return x[a:b] if b > a else np.zeros(1, dtype=x.dtype)


def align_pair(raw: np.ndarray, wet: np.ndarray, sr: int) -> AlignmentMap:
    """Global offset + per-phrase local refinement with aligned/edited/unmatched verdicts."""
    offset, gcorr = global_offset_s(raw, wet, sr)
    matches: list[PhraseMatch] = []
    for start_s, end_s in segment_phrases(raw, sr):
        dur = end_s - start_s
        target = start_s + offset
        best_corr, best_shift = -1.0, 0.0
        raw_env = _norm(envelope(_slice(raw, sr, start_s, end_s), sr))
        for shift in np.arange(-LOCAL_SEARCH_S, LOCAL_SEARCH_S + 1e-9, 1.0 / ENV_HZ):
            wet_seg = _slice(wet, sr, target + shift, target + shift + dur)
            wet_env = _norm(envelope(wet_seg, sr))
            n = min(len(raw_env), len(wet_env))
            if n < 3:
                continue
            c = float(np.dot(raw_env[:n], wet_env[:n]) / n)
            if c > best_corr:
                best_corr, best_shift = c, float(shift)
        wet_start = target + best_shift
        wet_seg = _slice(wet, sr, wet_start, wet_start + dur)
        wet_dur = len(wet_seg) / sr
        if best_corr < LOCAL_CORR_MIN:
            verdict = "unmatched"
        elif abs(wet_dur - dur) / max(dur, 1e-9) > EDIT_DUR_TOL:
            verdict = "edited"
        else:
            verdict = "aligned"
        matches.append(PhraseMatch(start_s, end_s, wet_start, wet_start + dur,
                                   round(best_corr, 4), verdict))
    return AlignmentMap(round(offset, 4), round(gcorr, 4), tuple(matches))
