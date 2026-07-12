"""Frame-level dynamic de-esser (M30).

Evidence basis (reports/evaluations/informal_listening_notes.md, 2026-07-11):
the static sibilance PeakFilter left the sibilance diagnosis firing on 3/3
user-tested processed files, with residual peaks localized to 5-8 kHz transient
frames — while the overall matched-loudness brightness ("space of air") was the
part listeners liked. Therefore: attenuate the sibilant *frames* only, never
the static balance.

Design/artifact guards:
- Only bins inside the sibilance band are touched; everything else is passed
  through bit-transparently (original phase, unity gain).
- Reduction per frame is proportional to how far the frame's band fraction
  exceeds the threshold, hard-capped at max_reduction_db (lisp guard: an "s"
  is tamed, never deleted).
- Gain is smoothed with instant attack and a multi-frame release to avoid
  zipper/flutter artifacts.
- Deterministic: same input, same params -> same output.
"""

import numpy as np

DEESSER_VERSION = "1.0.0"

FRAME_LENGTH = 2048
HOP_LENGTH = 512

# Release smoothing: how much of the previous frame's reduction is retained
# once the detector releases (per hop of ~11.6 ms; 0.6 -> ~90% release in
# ~5 frames / ~60 ms).
RELEASE_RETAIN = 0.6


def de_ess(
    audio: np.ndarray,
    sample_rate: int,
    band_lo_hz: float = 5000.0,
    band_hi_hz: float = 9000.0,
    frame_threshold: float = 0.18,
    max_reduction_db: float = 8.0,
) -> np.ndarray:
    """Attenuate sibilant frames' band energy. Returns float32, same length.

    frame_threshold matches the diagnosis metric: per-frame E(band)/E(full).
    """
    import librosa  # local import keeps module import cheap for the registry

    mono = audio.astype(np.float32)
    if mono.ndim == 2:
        mono = mono[:, 0]
    n = len(mono)
    if n < FRAME_LENGTH:
        return mono.copy()

    stft = librosa.stft(mono, n_fft=FRAME_LENGTH, hop_length=HOP_LENGTH)
    freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=FRAME_LENGTH)
    band = (freqs >= band_lo_hz) & (freqs <= band_hi_hz)
    if not np.any(band):
        return mono.copy()

    power = np.abs(stft) ** 2
    frame_full = power.sum(axis=0) + 1e-20
    fraction = power[band].sum(axis=0) / frame_full

    # Raw per-frame reduction: dB excess over threshold, capped.
    with np.errstate(divide="ignore"):
        excess_db = 10.0 * np.log10(np.maximum(fraction / frame_threshold, 1e-12))
    reduction_db = np.clip(excess_db, 0.0, max_reduction_db)

    # Instant attack, smoothed release.
    smoothed = np.empty_like(reduction_db)
    prev = 0.0
    for i, r in enumerate(reduction_db):
        prev = r if r >= prev else prev * RELEASE_RETAIN
        smoothed[i] = prev

    gains = (10.0 ** (-smoothed / 20.0)).astype(stft.dtype)
    stft[band, :] *= gains[np.newaxis, :]

    out = librosa.istft(stft, hop_length=HOP_LENGTH, length=n)
    return out.astype(np.float32)
