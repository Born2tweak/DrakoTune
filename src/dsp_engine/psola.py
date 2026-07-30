"""Time-varying pitch shifting by TD-PSOLA (DT-100, requirement R2).

The DT-98 spike (F-17) established why this exists. `PitchShift` applies **one**
interval to a whole buffer, and approximating a per-frame correction curve by
slicing, shifting and concatenating measures **SI-SDR −23.7 to −33.7 dB** against
a single-call shift — the output is dominated by boundary artifacts, because
block concatenation destroys phase continuity at every seam.

TD-PSOLA avoids seams by construction. It cuts the signal into grains centred on
*pitch marks* — one per glottal period — and overlap-adds them at new positions
spaced by the target period. Nothing is cut mid-period, so there is no
discontinuity to hear.

A second property matters for vocals: because each grain keeps its own waveform
and is only *re-spaced*, the spectral envelope stays where it was. Formants do
not move with the pitch, which is exactly the "chipmunk" artifact a resampling
shifter produces and the reason DT-100 needs this rather than the primitive.

Deterministic, numpy-only, and validated by shifting known tones and measuring
the result with the R1 estimator (`tests/test_psola.py`).

This module shifts pitch. It decides nothing: what to shift toward is the
correction curve's job, and that stage is still unbuilt.
"""

from __future__ import annotations

import numpy as np

from src.dsp_engine.pitch import F0Track, estimate_f0

# A grain spans two periods so that Hann-windowed neighbours sum to unity when
# they are spaced one period apart.
GRAIN_PERIODS = 2.0
# Refinement window for snapping a mark onto the local waveform peak, as a
# fraction of the period. Wider than this and a mark can jump to the neighbouring
# period, which reads as a pitch-doubling glitch.
_SNAP_FRACTION = 0.25
# Unvoiced regions have no period to be synchronous with. They are carried
# through on a fixed grain so the signal stays continuous instead of gating.
_UNVOICED_GRAIN_MS = 20.0

# Validated shift range, established by measurement rather than assumed.
#
# A grain spans GRAIN_PERIODS analysis periods and synthesis positions advance by
# period/ratio, so grains stop overlapping once ratio <= 1/GRAIN_PERIODS = 0.5.
# At exactly that point the method fails cleanly and badly: measured on a
# four-harmonic 220 Hz tone, a requested -1200 cents returned the ORIGINAL pitch
# (+1200 cents error), because each isolated grain still contains two periods of
# the input. Every other point measured from -900 to +1200 cents lands within
# +/-0.4 cents.
#
# Correction works in cents, not octaves, so clamping here costs nothing real —
# and transposition by an octave is what `PitchShift` is already for.
MIN_RATIO = 0.55        # ~ -1030 cents
MAX_RATIO = 4.0         # +2400 cents; the upper side overlaps more, not less


def _period_at(track: F0Track, time_s: float, sample_rate: int,
               fallback: float) -> tuple[float, bool]:
    """(period in samples, voiced) at a time, from the estimated contour."""
    if track.times_s.size == 0:
        return fallback, False
    index = int(np.argmin(np.abs(track.times_s - time_s)))
    f0 = track.f0_hz[index]
    if not np.isfinite(f0) or f0 <= 0:
        return fallback, False
    return float(sample_rate) / float(f0), True


def _snap_to_peak(audio: np.ndarray, centre: int, period: float) -> int:
    """Move a mark onto the nearest local peak, always of the SAME polarity.

    Snapping on |audio| looks reasonable and is wrong: a waveform with a strong
    negative lobe offers two candidates per period, so consecutive marks alternate
    between the positive and negative excursion. That places grains half a period
    apart in phase and makes the output periodic at *twice* the period — a clean
    octave-down error that no amount of grain re-spacing can undo. Measured on a
    four-harmonic 220 Hz tone it produced mark spacings alternating 160/241
    samples against an expected 200, and an output exactly 1200 cents low.

    Locking to the signed maximum keeps every grain aligned to the same part of
    the cycle.
    """
    span = max(int(period * _SNAP_FRACTION), 1)
    lo, hi = max(centre - span, 0), min(centre + span + 1, audio.size)
    if hi <= lo:
        return centre
    return lo + int(np.argmax(audio[lo:hi]))


def pitch_marks(audio: np.ndarray, sample_rate: int,
                track: F0Track | None = None) -> tuple[np.ndarray, np.ndarray]:
    """(mark positions in samples, period at each mark).

    Marks advance by the *local* period, so they follow the contour rather than
    assuming a constant pitch.
    """
    audio = np.asarray(audio, dtype=np.float64).reshape(-1)
    if track is None:
        track = estimate_f0(audio, sample_rate)
    fallback = sample_rate * _UNVOICED_GRAIN_MS / 1000.0

    marks: list[int] = []
    periods: list[float] = []
    position = 0.0
    while position < audio.size:
        period, voiced = _period_at(track, position / sample_rate, sample_rate, fallback)
        index = int(round(position))
        if voiced:
            index = _snap_to_peak(audio, index, period)
        if index >= audio.size:
            break
        marks.append(index)
        periods.append(period)
        position = max(index + period, position + 1.0)
    return np.asarray(marks, dtype=int), np.asarray(periods, dtype=float)


def shift_pitch(audio: np.ndarray, sample_rate: int,
                ratio: np.ndarray | float,
                track: F0Track | None = None) -> np.ndarray:
    """Shift pitch by `ratio` (2.0 = an octave up) preserving duration.

    `ratio` may be a scalar or a per-sample array, which is what makes this a
    *correction* engine rather than a transposer: the curve can differ at every
    moment of the take.

    Duration is preserved by choosing which analysis grain to copy for each
    synthesis position, rather than by stretching the signal.
    """
    x = np.asarray(audio, dtype=np.float64)
    if x.ndim == 2:                      # per-channel, so stereo is not collapsed
        return np.stack(
            [shift_pitch(x[:, c], sample_rate, ratio, track) for c in range(x.shape[1])],
            axis=1).astype(np.float32)
    x = x.reshape(-1)
    if x.size == 0:
        return x.astype(np.float32)

    ratios = (np.full(x.size, float(ratio), dtype=np.float64)
              if np.isscalar(ratio) or np.ndim(ratio) == 0
              else np.asarray(ratio, dtype=np.float64).reshape(-1))
    if ratios.size != x.size:
        ratios = np.interp(np.linspace(0, 1, x.size),
                           np.linspace(0, 1, ratios.size), ratios)
    ratios = np.clip(ratios, MIN_RATIO, MAX_RATIO)

    marks, periods = pitch_marks(x, sample_rate, track)
    if marks.size < 2:
        return x.astype(np.float32)

    out = np.zeros(x.size, dtype=np.float64)
    norm = np.zeros(x.size, dtype=np.float64)

    # Walk synthesis positions forward at the TARGET period; for each, copy the
    # grain from the nearest analysis mark. Raising pitch shortens the synthesis
    # step, so grains repeat; lowering it lengthens the step, so some are skipped.
    position = float(marks[0])
    while position < x.size:
        nearest = int(np.argmin(np.abs(marks - position)))
        centre = int(marks[nearest])
        period = periods[nearest]
        half = int(round(period * GRAIN_PERIODS / 2.0))
        if half < 2:
            break

        lo, hi = centre - half, centre + half
        grain = x[max(lo, 0):min(hi, x.size)]
        if grain.size < 4:
            position += max(period / ratios[min(int(position), ratios.size - 1)], 1.0)
            continue
        window = np.hanning(grain.size)
        grain = grain * window

        target = int(round(position))
        start = target - (centre - max(lo, 0))
        a, b = max(start, 0), min(start + grain.size, out.size)
        if b > a:
            g0 = a - start
            out[a:b] += grain[g0:g0 + (b - a)]
            norm[a:b] += window[g0:g0 + (b - a)]

        local_ratio = ratios[min(max(target, 0), ratios.size - 1)]
        position += max(period / local_ratio, 1.0)

    # Hann grains at one-period spacing sum to ~1; divide by the actual envelope
    # so that repeated or skipped grains do not change level.
    active = norm > 1e-6
    out[active] /= norm[active]
    return out.astype(np.float32)


def cents_to_ratio(cents: np.ndarray | float) -> np.ndarray | float:
    """Convert a correction curve in cents to a frequency ratio."""
    return 2.0 ** (np.asarray(cents, dtype=np.float64) / 1200.0)
