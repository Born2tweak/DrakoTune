"""Descriptive measurements of the file the user actually receives (DT-97 corrective).

Why this exists: F-12 recorded that the export stage now lands renders at a
consistent peak. A reviewer then read that as "consistent loudness", which it is
not. Peak is one number about one sample; it says nothing about how loud the
result seems, how much dynamic range survived, or whether a widened chain
survives a mono fold-down.

So this module reports what is actually measurable about a delivered file, and
nothing more:

  * sample_peak_dbfs / true_peak_dbfs - the second is measured on a 4x
    oversampled signal, because inter-sample peaks routinely exceed the sample
    peak an encoder never sees.
  * integrated_lufs - BS.1770 gated, via the existing M18 analyzer. `None` when
    the file is too short or too quiet to measure, never faked.
  * crest_factor_db - peak-to-RMS. The distance between "peaks at -1 dBFS" and
    "sounds loud".
  * clipped_samples - full-scale runs, which the ceiling should make impossible.
  * stereo_correlation / mono_folddown_delta_db - only for stereo output, and
    the pair that matters before DT-98 doubling ships.

DELIBERATELY ABSENT: any score, grade, pass/fail, or aggregate. This project has
spent N-016..N-022 establishing that it does not possess a certified perceptual
objective (`objective_certification.PERCEPTUAL_ALIGNMENT` is UNTESTABLE while
DEF-003 stands). Combining these numbers into a quality verdict would recreate
exactly the failure those findings documented. They are descriptive telemetry:
useful for spotting that something went wrong, never evidence that something
went right.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import soundfile as sf

from src.diagnostics.loudness import _integrated_lufs

# Oversampling factor for the true-peak estimate. BS.1770-4 Annex 2 specifies 4x
# for material at 44.1/48 kHz, which is everything the pipeline emits.
TRUE_PEAK_OVERSAMPLE = 4

# A sample within this of full scale counts as clipped. Not exactly 1.0: PCM_16
# quantisation lands the ceiling a hair below unity.
CLIP_THRESHOLD = 0.9995

DELIVERY_METRICS_VERSION = "1.0.0"


@dataclass(frozen=True)
class DeliveryMeasurement:
    """What a delivered file measures. Descriptive only - see module docstring."""

    channels: int
    duration_seconds: float
    sample_peak_dbfs: float
    true_peak_dbfs: float
    integrated_lufs: float | None
    crest_factor_db: float
    clipped_samples: int
    stereo_correlation: float | None
    mono_folddown_delta_db: float | None

    def to_dict(self) -> dict:
        def r(v: float | None) -> float | None:
            return None if v is None else round(float(v), 2)

        return {
            "version": DELIVERY_METRICS_VERSION,
            "channels": self.channels,
            "duration_seconds": r(self.duration_seconds),
            "sample_peak_dbfs": r(self.sample_peak_dbfs),
            "true_peak_dbfs": r(self.true_peak_dbfs),
            "integrated_lufs": r(self.integrated_lufs),
            "crest_factor_db": r(self.crest_factor_db),
            "clipped_samples": self.clipped_samples,
            "stereo_correlation": r(self.stereo_correlation),
            "mono_folddown_delta_db": r(self.mono_folddown_delta_db),
        }


def _dbfs(linear: float) -> float:
    return 20.0 * math.log10(linear) if linear > 0 else -120.0


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x.astype(np.float64) ** 2))) if x.size else 0.0


def _oversample(column: np.ndarray, factor: int) -> np.ndarray:
    """Band-limited interpolation by `factor`, numpy only.

    Zero-padding the spectrum is exact sinc interpolation, which is what a
    true-peak meter needs. scipy would be the obvious tool, but it is a
    dev-only dependency here (`pyproject.toml` optional-dependencies.dev) and
    runtime code must not reach into it - that is the two-clean-env SBOM parity
    gate CI enforces.
    """
    n = column.shape[0]
    if n < 2:
        return column
    spectrum = np.fft.rfft(column)
    target = n * factor
    padded = np.zeros(target // 2 + 1, dtype=complex)
    padded[: spectrum.shape[0]] = spectrum
    return np.fft.irfft(padded, n=target) * factor


def _true_peak(audio: np.ndarray) -> float:
    """Peak of the 4x oversampled signal, per channel, taking the maximum."""
    if audio.size == 0:
        return 0.0
    work = audio.reshape(-1, 1) if audio.ndim == 1 else audio
    peaks = []
    for ch in range(work.shape[1]):
        up = _oversample(work[:, ch].astype(np.float64), TRUE_PEAK_OVERSAMPLE)
        peaks.append(float(np.max(np.abs(up))) if up.size else 0.0)
    return max(peaks) if peaks else 0.0


def _stereo_pair(audio: np.ndarray) -> tuple[float | None, float | None]:
    """(correlation, mono fold-down delta dB) for stereo; (None, None) for mono.

    The delta is the level change from summing to mono. A strongly negative
    value means the stereo image is built from content that cancels itself -
    the failure mode that matters once DT-98 doubling exists.
    """
    if audio.ndim != 2 or audio.shape[1] < 2:
        return None, None
    left = audio[:, 0].astype(np.float64)
    right = audio[:, 1].astype(np.float64)

    if np.std(left) < 1e-12 or np.std(right) < 1e-12:
        correlation = None  # a silent or DC channel has no defined correlation
    else:
        correlation = float(np.corrcoef(left, right)[0, 1])

    stereo_level = _rms(np.stack([left, right]))
    mono_level = _rms((left + right) / 2.0)
    if stereo_level <= 0:
        # Silent program: there is nothing to fold down. Genuinely unmeasurable.
        return correlation, None
    # A mono_level of zero is TOTAL cancellation - the worst result this metric
    # exists to catch. Reporting it as unmeasurable would let the most severe
    # case look like missing data (the N-016 failure: absence of evidence
    # presented as evidence of absence). `_dbfs` floors at -120 dB.
    return correlation, _dbfs(mono_level / stereo_level)


def measure_array(audio: np.ndarray, sample_rate: int) -> DeliveryMeasurement:
    """Measure an in-memory signal. `audio` is (n,) mono or (n, channels)."""
    work = audio.reshape(-1, 1) if audio.ndim == 1 else audio
    channels = int(work.shape[1])
    frames = int(work.shape[0])

    sample_peak = float(np.max(np.abs(work))) if work.size else 0.0
    rms = _rms(work)
    peak_db = _dbfs(sample_peak)
    correlation, folddown = _stereo_pair(work)

    # LUFS is measured on the mono sum, matching how the M18 analyzer treats
    # multichannel input elsewhere in the pipeline.
    mono = work.mean(axis=1).astype(np.float32)

    return DeliveryMeasurement(
        channels=channels,
        duration_seconds=frames / float(sample_rate) if sample_rate else 0.0,
        sample_peak_dbfs=peak_db,
        true_peak_dbfs=_dbfs(_true_peak(work)),
        integrated_lufs=_integrated_lufs(mono, int(sample_rate)),
        crest_factor_db=peak_db - _dbfs(rms),
        clipped_samples=int(np.count_nonzero(np.abs(work) >= CLIP_THRESHOLD)),
        stereo_correlation=correlation,
        mono_folddown_delta_db=folddown,
    )


def measure_delivery(path: str) -> DeliveryMeasurement:
    """Measure a written audio file."""
    audio, sample_rate = sf.read(path, dtype="float32", always_2d=True)
    return measure_array(audio, int(sample_rate))
