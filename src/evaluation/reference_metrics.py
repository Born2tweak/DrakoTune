"""Reference-based fidelity metrics (M23).

Used only when a clean reference exists (synthetic degradation pairs,
SingVERSE-style paired data). Both metrics are standard, loudness-aware
formulations; neither makes any perceptual-quality claim on its own
(ADR 0004 §3 — metric roles are fixed).
"""

import math

import numpy as np

REFERENCE_METRICS_VERSION = "1.0.0"

_EPS = 1e-10


def _align(reference: np.ndarray, estimate: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = min(len(reference), len(estimate))
    return reference[:n].astype(np.float64), estimate[:n].astype(np.float64)


def si_sdr(reference: np.ndarray, estimate: np.ndarray) -> float:
    """Scale-invariant signal-to-distortion ratio in dB (Le Roux et al. 2019).

    Invariant to overall gain of `estimate`; higher is closer to the reference.
    """
    ref, est = _align(reference, estimate)
    ref = ref - np.mean(ref)
    est = est - np.mean(est)
    ref_energy = np.sum(ref ** 2)
    if ref_energy < _EPS:
        return float("nan")
    projection = (np.dot(est, ref) / ref_energy) * ref
    noise = est - projection
    ratio = np.sum(projection ** 2) / max(np.sum(noise ** 2), _EPS)
    return float(10.0 * math.log10(max(ratio, _EPS)))


def segmental_snr(
    reference: np.ndarray,
    estimate: np.ndarray,
    sample_rate: int,
    frame_s: float = 0.03,
    floor_db: float = -10.0,
    ceil_db: float = 35.0,
) -> float:
    """Mean frame-level SNR in dB, clamped per frame (classic segSNR).

    Frames where the reference is essentially silent are excluded.
    """
    ref, est = _align(reference, estimate)
    frame = max(int(sample_rate * frame_s), 1)
    snrs: list[float] = []
    for start in range(0, len(ref) - frame + 1, frame):
        r = ref[start:start + frame]
        e = est[start:start + frame]
        signal = np.sum(r ** 2)
        if signal < _EPS * frame:  # silent reference frame: SNR undefined
            continue
        noise = np.sum((r - e) ** 2)
        snr = 10.0 * math.log10(max(signal, _EPS) / max(noise, _EPS))
        snrs.append(min(max(snr, floor_db), ceil_db))
    return float(np.mean(snrs)) if snrs else float("nan")
