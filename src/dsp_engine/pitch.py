"""Continuous-valued f0 estimation (DT-100, requirement R1).

The DT-98 spike (F-17) established why this module has to exist. `librosa.pyin`
tracks a melody perfectly well but returns f0 on a **quantized candidate grid**:
10 cents at its default, which is coarser than the error pitch correction has to
resolve. Buying precision from a grid search does not work — a 2-cent grid costs
about 20x realtime, and a 1-cent grid raised `MemoryError` on a two-second
excerpt.

So precision here comes from **interpolation, not enumeration**. This is YIN
(de Cheveigné & Kawahara 2002) with parabolic interpolation of the difference
minimum, which makes the estimate continuous: two inputs three cents apart
produce two different numbers, which is the property a corrector needs and a grid
cannot provide.

Deterministic, dependency-free (numpy only), and measured against synthetic
signals whose true f0 is known exactly — see `tests/test_pitch.py`.

This module estimates. It does not correct anything, and nothing here may be
described as tuning: correction additionally needs R2 (a real time-varying
resynthesis stage), which does not exist yet.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# YIN's absolute threshold on the cumulative mean normalized difference. Below
# this the frame is considered periodic. 0.15 is the value the paper uses for
# speech; it is deliberately not tuned against any corpus here.
DEFAULT_THRESHOLD = 0.15
DEFAULT_FRAME_MS = 46.0     # long enough to hold two periods at fmin=65 Hz
DEFAULT_HOP_MS = 10.0


@dataclass(frozen=True)
class F0Track:
    """Per-frame f0 in Hz (NaN where unvoiced) with the times they belong to."""

    f0_hz: np.ndarray
    times_s: np.ndarray
    periodicity: np.ndarray      # 1 - CMND at the chosen lag; higher = more periodic
    sample_rate: int
    frame_ms: float
    hop_ms: float

    @property
    def voiced(self) -> np.ndarray:
        return np.isfinite(self.f0_hz)

    @property
    def voiced_fraction(self) -> float:
        return float(np.mean(self.voiced)) if self.f0_hz.size else 0.0

    def cents_from(self, reference_hz: float) -> np.ndarray:
        """Signed cents of each voiced frame relative to `reference_hz`."""
        voiced = self.f0_hz[self.voiced]
        if voiced.size == 0 or reference_hz <= 0:
            return np.zeros(0)
        return 1200.0 * np.log2(voiced / reference_hz)

    def to_dict(self) -> dict:
        return {
            "frames": int(self.f0_hz.size),
            "voiced_fraction": round(self.voiced_fraction, 4),
            "median_f0_hz": (round(float(np.nanmedian(self.f0_hz)), 3)
                             if np.any(self.voiced) else None),
            "sample_rate": self.sample_rate,
            "frame_ms": self.frame_ms,
            "hop_ms": self.hop_ms,
        }


def _difference(frame: np.ndarray, max_lag: int) -> np.ndarray:
    """YIN's squared-difference function d(tau), computed via autocorrelation.

    d(tau) = sum_j (x_j - x_{j+tau})^2, expanded to power terms plus the
    autocorrelation, so the whole curve costs one FFT instead of `max_lag`
    explicit shifts. That difference is what keeps this affordable where the
    grid search was not.
    """
    n = frame.size
    size = int(2 ** np.ceil(np.log2(2 * n)))
    spectrum = np.fft.rfft(frame, size)
    autocorr = np.fft.irfft(spectrum * np.conjugate(spectrum), size)[:max_lag + 1]

    cumulative = np.concatenate(([0.0], np.cumsum(frame ** 2)))
    total = cumulative[n]
    lags = np.arange(max_lag + 1)
    # Energy of the two windows actually being compared at lag tau:
    # x[0 : n-tau] against x[tau : n]. Getting these wrong biases the CMND
    # minimum and therefore every estimate — it showed up as a systematic
    # -11 cents at 220 Hz before this was corrected.
    left = cumulative[n - lags]                 # sum x[0 : n-tau]^2
    right = total - cumulative[lags]            # sum x[tau : n]^2
    return left + right - 2.0 * autocorr


def _cumulative_mean_normalized(diff: np.ndarray) -> np.ndarray:
    """CMND: d(tau) normalized by its running mean, so it is scale-free."""
    cmnd = np.ones_like(diff)
    running = np.cumsum(diff[1:])
    lags = np.arange(1, diff.size)
    nonzero = running > 0
    cmnd[1:][nonzero] = diff[1:][nonzero] * lags[nonzero] / running[nonzero]
    return cmnd


def _parabolic_refine(values: np.ndarray, index: int) -> float:
    """Sub-sample minimum by fitting a parabola through three points.

    This is where continuous precision comes from: the true minimum almost never
    lands exactly on an integer lag, and rounding it to one is precisely the
    quantization that made a grid-based estimator unusable for correction.
    """
    if index <= 0 or index >= values.size - 1:
        return float(index)
    a, b, c = values[index - 1], values[index], values[index + 1]
    denom = a - 2.0 * b + c
    if denom == 0.0:
        return float(index)
    return float(index) + 0.5 * (a - c) / denom


def _frame_f0(frame: np.ndarray, sample_rate: int, min_lag: int, max_lag: int,
              threshold: float) -> tuple[float, float]:
    """(f0_hz, periodicity) for one frame; f0 is NaN when the frame is unvoiced."""
    if frame.size < max_lag + 2 or not np.any(frame):
        return float("nan"), 0.0
    frame = frame - float(np.mean(frame))          # DC would bias the difference
    if not np.any(frame):
        return float("nan"), 0.0

    cmnd = _cumulative_mean_normalized(_difference(frame, max_lag))
    search = cmnd[min_lag:max_lag + 1]
    if search.size == 0:
        return float("nan"), 0.0

    # YIN takes the FIRST lag below the threshold, not the global minimum: the
    # global minimum is often an octave-down multiple of the true period.
    below = np.flatnonzero(search < threshold)
    if below.size:
        local = int(below[0])
        # Walk to the bottom of that dip so the parabola is fitted at a minimum.
        while (local + 1 < search.size) and search[local + 1] < search[local]:
            local += 1
    else:
        local = int(np.argmin(search))

    index = local + min_lag
    period = _parabolic_refine(cmnd, index)
    if period <= 0:
        return float("nan"), 0.0

    periodicity = float(np.clip(1.0 - cmnd[index], 0.0, 1.0))
    if not below.size:
        return float("nan"), periodicity          # measured, but not periodic enough
    return float(sample_rate) / period, periodicity


def estimate_f0(audio: np.ndarray, sample_rate: int, fmin: float = 65.0,
                fmax: float = 1000.0, frame_ms: float = DEFAULT_FRAME_MS,
                hop_ms: float = DEFAULT_HOP_MS,
                threshold: float = DEFAULT_THRESHOLD) -> F0Track:
    """Estimate a continuous-valued f0 contour.

    `fmin`/`fmax` bound the lag search only — unlike a candidate grid they do not
    quantize the result, so the returned f0 is not confined to any lattice.
    """
    if fmin <= 0 or fmax <= fmin:
        raise ValueError(f"require 0 < fmin < fmax, got {fmin}, {fmax}")
    x = np.asarray(audio, dtype=np.float64)
    if x.ndim == 2:
        x = x.mean(axis=1)
    x = x.reshape(-1)

    frame_len = max(int(sample_rate * frame_ms / 1000.0), 4)
    hop = max(int(sample_rate * hop_ms / 1000.0), 1)
    min_lag = max(int(np.floor(sample_rate / fmax)), 2)
    required_lag = int(np.ceil(sample_rate / fmin))
    # Silently narrowing the lag range would make low pitches simply undetectable
    # while still returning a confident-looking contour. Refuse instead.
    if required_lag > frame_len - 2:
        raise ValueError(
            f"frame of {frame_ms} ms ({frame_len} samples) cannot resolve {fmin} Hz "
            f"at {sample_rate} Hz; needs at least {required_lag + 2} samples")
    max_lag = required_lag
    if max_lag <= min_lag:
        raise ValueError(f"lag range empty for fmin={fmin}, fmax={fmax}")

    starts = range(0, max(len(x) - frame_len + 1, 1), hop)
    f0 = np.full(len(starts), np.nan)
    periodicity = np.zeros(len(starts))
    for i, start in enumerate(starts):
        frame = x[start:start + frame_len]
        if frame.size < frame_len:
            break
        f0[i], periodicity[i] = _frame_f0(frame, sample_rate, min_lag, max_lag, threshold)

    # A lag outside the requested range is not a valid answer.
    out_of_range = np.isfinite(f0) & ((f0 < fmin) | (f0 > fmax))
    f0[out_of_range] = np.nan

    times = (np.asarray(starts, dtype=np.float64) + frame_len / 2.0) / sample_rate
    return F0Track(f0, times, periodicity, int(sample_rate), frame_ms, hop_ms)
