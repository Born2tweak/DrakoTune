"""Explicit mono/stereo buffer contracts for the V3 graph (DT-94).

Before this module the engine was mono end-to-end by accident rather than by
contract: `src/dsp/preprocess.py` normalizes inputs to mono WAV, and the
executor's array-processor path collapsed any 2-D buffer to channel 0 and
reshaped to `(-1, 1)`. Anything that widened the signal would therefore have
been silently discarded before export — so width, doubling, panned sends and
stereo delay are impossible to build correctly until channel handling is
explicit.

The contract, enforced by `normalize()`:

  * Every buffer crossing a node boundary is float32, 2-D, shaped
    `(n_samples, n_channels)`, with `n_channels` in {1, 2}.
  * A node declares what it can accept and what it emits via `ChannelMode`.
  * Widening is explicit. A mono graph stays mono unless some node declares
    `MONO_TO_STEREO`; nothing widens as a side effect.

Mono compatibility matters here for a real reason: a doubled/widened vocal that
sounds good in stereo can partially cancel when a club system, phone speaker or
streaming encoder sums it to mono. `mono_compatibility()` reports the numbers
that detect that (inter-channel correlation and the level change under summing)
so the safety suite can fail on it rather than shipping a vocal that vanishes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

MONO = 1
STEREO = 2


class ChannelMode(Enum):
    """What a node accepts and emits.

    ANY             - handles whatever it is given, channel count unchanged
                      (pedalboard filters/dynamics; they process per channel).
    PER_CHANNEL     - a mono-only kernel; the executor maps it over each channel
                      independently and preserves the channel count.
    MONO_TO_STEREO  - deliberately widens: accepts mono (or a summed copy) and
                      emits two channels. The only way a graph gains width.
    STEREO_TO_MONO  - deliberately narrows (e.g. a mono-sum utility).
    """

    ANY = "any"
    PER_CHANNEL = "per_channel"
    MONO_TO_STEREO = "mono_to_stereo"
    STEREO_TO_MONO = "stereo_to_mono"


def normalize(audio: np.ndarray) -> np.ndarray:
    """Coerce any accepted input to the canonical `(n_samples, n_channels)` float32.

    Accepts 1-D mono, `(n, c)`, or a transposed `(c, n)` buffer from pedalboard.
    Raises on >2 channels rather than silently discarding them.
    """
    a = np.asarray(audio, dtype=np.float32)
    if a.ndim == 1:
        return a.reshape(-1, 1)
    if a.ndim != 2:
        raise ValueError(f"audio must be 1-D or 2-D, got {a.ndim}-D")
    n_rows, n_cols = a.shape
    # pedalboard hands back (channels, samples); ours is (samples, channels).
    # Disambiguate only when it is unambiguous: few rows, many columns.
    if n_rows <= STEREO < n_cols:
        a = a.T
        n_rows, n_cols = a.shape
    if n_cols > STEREO:
        raise ValueError(f"unsupported channel count: {n_cols} (mono or stereo only)")
    return np.ascontiguousarray(a, dtype=np.float32)


def channel_count(audio: np.ndarray) -> int:
    return int(normalize(audio).shape[1])


def is_mono(audio: np.ndarray) -> bool:
    return channel_count(audio) == MONO


def to_mono(audio: np.ndarray) -> np.ndarray:
    """Sum to a single channel. Averages so a correlated stereo pair keeps its level."""
    a = normalize(audio)
    if a.shape[1] == MONO:
        return a
    return a.mean(axis=1, keepdims=True).astype(np.float32)


def to_stereo(audio: np.ndarray) -> np.ndarray:
    """Duplicate mono to two channels. A no-op on already-stereo input."""
    a = normalize(audio)
    if a.shape[1] == STEREO:
        return a
    return np.repeat(a, STEREO, axis=1).astype(np.float32)


def match_channels(audio: np.ndarray, n_channels: int) -> np.ndarray:
    """Coerce to exactly `n_channels`, widening or summing as needed."""
    if n_channels not in (MONO, STEREO):
        raise ValueError(f"n_channels must be 1 or 2, got {n_channels}")
    return to_mono(audio) if n_channels == MONO else to_stereo(audio)


def align_for_mix(*buffers: np.ndarray) -> list[np.ndarray]:
    """Bring buffers to a common channel count and length so they can be summed.

    Channel count is the max across inputs (a widened branch widens the mix);
    length is the max, zero-padded, so a delay/reverb tail is never truncated by
    a shorter dry branch.
    """
    norm = [normalize(b) for b in buffers]
    if not norm:
        return []
    width = max(b.shape[1] for b in norm)
    length = max(b.shape[0] for b in norm)
    out: list[np.ndarray] = []
    for b in norm:
        b = match_channels(b, width)
        if b.shape[0] < length:
            b = np.pad(b, ((0, length - b.shape[0]), (0, 0)))
        out.append(b.astype(np.float32))
    return out


def pan(audio: np.ndarray, position: float) -> np.ndarray:
    """Constant-power pan to stereo. `position` -1.0 = hard left, +1.0 = hard right.

    Constant power (not linear) so a panned double keeps perceived loudness as it
    moves off centre; linear panning dips ~3 dB in the middle.
    """
    p = float(np.clip(position, -1.0, 1.0))
    mono = to_mono(audio)[:, 0]
    angle = (p + 1.0) * 0.25 * np.pi  # 0 -> hard left, pi/2 -> hard right
    left = float(np.cos(angle))
    right = float(np.sin(angle))
    return np.stack([mono * left, mono * right], axis=1).astype(np.float32)


@dataclass(frozen=True)
class MonoCompatibility:
    """Evidence that a widened signal survives being summed to mono."""

    correlation: float          # +1 identical channels, 0 uncorrelated, -1 inverted
    mono_sum_delta_db: float    # level change from stereo RMS to mono-sum RMS
    channels: int

    @property
    def collapses(self) -> bool:
        """True when summing to mono destroys a meaningful amount of signal.

        -3 dB is the honest threshold: two uncorrelated channels averaged lose
        ~3 dB, which is expected. Beyond that the channels are actively
        cancelling, which is the failure this check exists to catch.
        """
        return self.mono_sum_delta_db < -3.0 or self.correlation < 0.0

    def to_dict(self) -> dict:
        return {
            "correlation": round(self.correlation, 6),
            "mono_sum_delta_db": round(self.mono_sum_delta_db, 3),
            "channels": self.channels,
            "collapses": self.collapses,
        }


def _rms(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(a, dtype=np.float64)))) if a.size else 0.0


def mono_compatibility(audio: np.ndarray) -> MonoCompatibility:
    """Measure how a buffer behaves when summed to mono.

    Mono input is trivially compatible (correlation 1.0, no level change).
    """
    a = normalize(audio)
    if a.shape[1] == MONO:
        return MonoCompatibility(correlation=1.0, mono_sum_delta_db=0.0, channels=MONO)

    left, right = a[:, 0].astype(np.float64), a[:, 1].astype(np.float64)
    if _rms(left) <= 0.0 or _rms(right) <= 0.0:
        correlation = 0.0
    else:
        correlation = float(np.corrcoef(left, right)[0, 1])
        if not np.isfinite(correlation):
            correlation = 0.0

    stereo_rms = _rms(a)
    mono_rms = _rms(to_mono(a))
    if stereo_rms <= 0.0:
        delta_db = 0.0
    elif mono_rms <= 0.0:
        delta_db = -120.0
    else:
        delta_db = 20.0 * float(np.log10(mono_rms / stereo_rms))

    return MonoCompatibility(
        correlation=correlation, mono_sum_delta_db=delta_db, channels=STEREO
    )
