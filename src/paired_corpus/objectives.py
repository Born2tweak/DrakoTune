"""Candidate objectives for the oracle target (DT-77 C-4, Q-016).

The objective in use is a 5-axis feature distance — three band-energy ratios, crest
and spectral tilt — chosen because it is interpretable, not because it was shown to
track anything a listener hears. N-018 showed a 5-number summary is cheap to
satisfy by destruction; N-019 showed the guards protecting it are not what stops
that. So the target itself has to be reconsidered, and candidates have to be
comparable on evidence rather than on preference.

This module defines the candidates and nothing else. Selection is Q-016, a human
gate: **nothing here is promoted, and none of these is a perceptual model.** Every
candidate is a *signal* distance with a perceptual motivation, which is a weaker
thing and must keep being called one — no candidate in this module has been shown
to correlate with a listening judgement, because no listening data exists
(DEF-003).

Each candidate compares a rendered candidate against the WET AUDIO of aligned
phrases, so they are all full-reference-against-a-professional-rendering. Each is
made level-invariant by per-phrase RMS normalisation, which closes the loudness
inflation exploit by construction rather than by a guard: the registry permits
+12 dB of clean gain, and a metric that can be improved by turning it up will be.

No new dependency: everything here uses numpy/librosa, both already required.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from src.paired_corpus.alignment import AlignmentMap
from src.paired_corpus.search import SR, WetTarget, composite_distance

_EPS = 1e-10


@dataclass(frozen=True)
class PhraseAudioTarget:
    """Aligned phrase spans (raw-side) plus the WET AUDIO for each.

    `WetTarget` precomputes five scalars; a candidate objective that looks at the
    spectrum needs the audio itself, so the two targets exist side by side rather
    than one being widened into the other.
    """
    spans: tuple[tuple[float, float], ...]
    wet_segments: tuple[np.ndarray, ...]

    @property
    def n_phrases(self) -> int:
        return len(self.spans)


def _slice(x: np.ndarray, a: float, b: float) -> np.ndarray:
    i, j = max(int(a * SR), 0), min(int(b * SR), len(x))
    return x[i:j] if j > i else np.zeros(1, dtype=x.dtype)


def build_audio_target(wet: np.ndarray, amap: AlignmentMap,
                       max_phrases: int = 30) -> PhraseAudioTarget:
    """Same deterministic, evenly spaced phrase subsampling `build_target` uses."""
    usable = [p for p in amap.aligned()
              if (p.raw_end_s - p.raw_start_s) >= 0.1 and (p.wet_end_s - p.wet_start_s) >= 0.1]
    if len(usable) > max_phrases:
        idx = np.linspace(0, len(usable) - 1, max_phrases).round().astype(int)
        usable = [usable[i] for i in dict.fromkeys(idx.tolist())]
    spans, segs = [], []
    for p in usable:
        wseg = _slice(wet, p.wet_start_s, p.wet_end_s)
        if len(wseg) < SR // 10:
            continue
        spans.append((p.raw_start_s, p.raw_end_s))
        segs.append(_normalize(wseg))
    return PhraseAudioTarget(tuple(spans), tuple(segs))


def _normalize(x: np.ndarray) -> np.ndarray:
    """Unit-RMS. Level invariance by construction, not by a guard bolted on later."""
    rms = float(np.sqrt(np.mean(np.square(x.astype(np.float64))) + _EPS))
    return (x.astype(np.float64) / (rms + _EPS)).astype(np.float32)


def _pairwise(candidate: np.ndarray, target: PhraseAudioTarget,
              distance: Callable[[np.ndarray, np.ndarray], float]) -> float:
    """Mean per-phrase distance; inf when nothing is measurable (never 0)."""
    totals: list[float] = []
    for (a, b), wseg in zip(target.spans, target.wet_segments):
        cseg = _slice(candidate, a, b)
        if len(cseg) < SR // 10:
            continue
        n = min(len(cseg), len(wseg))
        value = distance(_normalize(cseg[:n]), wseg[:n])
        if np.isfinite(value):
            totals.append(float(value))
    return round(float(np.mean(totals)), 6) if totals else float("inf")


# ---------------------------------------------------------------------------
# Candidate distances
# ---------------------------------------------------------------------------

def _log_mel(x: np.ndarray, n_mels: int = 64) -> np.ndarray:
    import librosa
    mel = librosa.feature.melspectrogram(y=x.astype(np.float32), sr=SR, n_fft=2048,
                                         hop_length=512, n_mels=n_mels, power=2.0)
    return np.log(mel + _EPS)


def _logmel_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Mean |Δ log-mel|. A frequency-resolved difference, so removing a whole
    region costs proportionally instead of moving one of five summary numbers."""
    ma, mb = _log_mel(a), _log_mel(b)
    n = min(ma.shape[1], mb.shape[1])
    return float(np.mean(np.abs(ma[:, :n] - mb[:, :n])))


def _mfcc_distance(a: np.ndarray, b: np.ndarray, n_mfcc: int = 13) -> float:
    """Timbral distance, c0 dropped (level) — the shape of the spectrum only."""
    import librosa
    ca = librosa.feature.mfcc(y=a.astype(np.float32), sr=SR, n_mfcc=n_mfcc)[1:]
    cb = librosa.feature.mfcc(y=b.astype(np.float32), sr=SR, n_mfcc=n_mfcc)[1:]
    n = min(ca.shape[1], cb.shape[1])
    return float(np.mean(np.abs(ca[:, :n] - cb[:, :n])))


def _mrstft_distance(a: np.ndarray, b: np.ndarray,
                     ffts: tuple[int, ...] = (512, 2048, 8192)) -> float:
    """Multi-resolution log-magnitude STFT distance.

    Several time/frequency resolutions at once, so a candidate cannot satisfy the
    metric at one scale while wrecking another — the failure mode a single
    resolution invites.
    """
    total = 0.0
    for n_fft in ffts:
        hop = n_fft // 4
        if len(a) < n_fft or len(b) < n_fft:
            continue
        sa = np.abs(np.fft.rfft(_frames(a, n_fft, hop), axis=-1))
        sb = np.abs(np.fft.rfft(_frames(b, n_fft, hop), axis=-1))
        n = min(sa.shape[0], sb.shape[0])
        if n == 0:
            continue
        total += float(np.mean(np.abs(np.log(sa[:n] + _EPS) - np.log(sb[:n] + _EPS))))
    return total / max(len(ffts), 1)


def _frames(x: np.ndarray, n_fft: int, hop: int) -> np.ndarray:
    n = 1 + max((len(x) - n_fft) // hop, 0)
    idx = np.arange(n_fft)[None, :] + hop * np.arange(n)[:, None]
    idx = np.clip(idx, 0, len(x) - 1)
    return x[idx] * np.hanning(n_fft)[None, :]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Candidate:
    name: str
    rationale: str
    # Built from (wet, alignment map) so every candidate sees the same phrases.
    build: Callable[[np.ndarray, AlignmentMap, WetTarget], Callable[[np.ndarray], float]]


def _build_composite(wet, amap, feature_target):
    return lambda c: composite_distance(c, feature_target)


def _build_from_audio(distance):
    def build(wet, amap, feature_target):
        target = build_audio_target(wet, amap)
        return lambda c: _pairwise(c, target, distance)
    return build


CANDIDATES: tuple[Candidate, ...] = (
    Candidate(
        "composite_v1",
        "the objective currently in use: 3 band-energy ratios, crest, spectral "
        "tilt. Interpretable, and small enough that N-018 bought two of its five "
        "axes by destruction. Baseline, not a recommendation.",
        _build_composite),
    Candidate(
        "logmel_l1",
        "mean |Δ log-mel| over aligned phrases: frequency-resolved, so deleting a "
        "band costs in proportion to the band instead of moving one summary number",
        _build_from_audio(_logmel_distance)),
    Candidate(
        "mfcc_l1",
        "cepstral (timbre-shape) distance with c0 dropped; insensitive to level "
        "and to fine harmonic structure, sensitive to spectral envelope",
        _build_from_audio(_mfcc_distance)),
    Candidate(
        "mrstft_log",
        "multi-resolution log-magnitude STFT distance; a candidate cannot satisfy "
        "one time/frequency resolution while wrecking another",
        _build_from_audio(_mrstft_distance)),
)

CANDIDATES_BY_NAME = {c.name: c for c in CANDIDATES}
