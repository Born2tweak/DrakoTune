"""Substantive dynamics and tone processors (DT-96).

These are implementations, not registry aliases. Each one exists because a
pedalboard primitive cannot do the job:

  vocal_rider          - there is no level-automation plugin. Riding gain BEFORE
                         compression is what keeps every word audible without
                         asking one compressor to flatten the whole performance.
  dynamic_eq           - a static PeakFilter cuts a frequency always. A dynamic
                         band only acts while that region is actually excessive,
                         which is the difference between "controlled" and "dull".
  suppress_resonances  - finds the narrow peaks that ring in an untreated room
                         and reduces each one only while it is ringing.
  saturate             - Distortion is a raw nonlinearity. Tasteful saturation
                         needs oversampling (so added harmonics do not alias back
                         down as inharmonic grit), a drive curve, and a wet/dry
                         blend that keeps the dry transient intact.

All four are mono kernels shaped like `deesser.de_ess`, so the graph maps them
per channel and the registry clamps their parameters.

Frame sizes are chosen for voice: 2048-sample analysis at 44.1 kHz is ~46 ms,
long enough to resolve a low male fundamental (~80 Hz) and short enough to track
syllables.
"""

from __future__ import annotations

import numpy as np

FRAME_LENGTH = 2048
HOP_LENGTH = 512

# Gain smoothing floor. Any gain envelope changing faster than this modulates at
# audio rate and is heard as distortion rather than as level movement.
_MIN_SMOOTH_MS = 20.0


def _smooth_gain(gain: np.ndarray, sample_rate: int, ms: float) -> np.ndarray:
    """One-pole smoothing of a per-sample gain envelope, applied both ways.

    Filtering forward then backward keeps the envelope aligned with the signal;
    a single forward pass would lag and pull gain down after the loud moment
    instead of during it.
    """
    ms = max(ms, _MIN_SMOOTH_MS)
    window = max(1, int(sample_rate * ms / 1000.0))
    coeff = float(np.exp(-1.0 / window))
    out = np.asarray(gain, dtype=np.float32).copy()
    for i in range(1, out.size):
        out[i] = coeff * out[i - 1] + (1.0 - coeff) * out[i]
    for i in range(out.size - 2, -1, -1):
        out[i] = coeff * out[i + 1] + (1.0 - coeff) * out[i]
    return out


def _frame_rms(audio: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-frame RMS and the sample index at each frame centre."""
    if audio.size < FRAME_LENGTH:
        return np.array([_rms(audio)], dtype=np.float32), np.array([0], dtype=np.int64)
    starts = np.arange(0, audio.size - FRAME_LENGTH + 1, HOP_LENGTH)
    frames = np.lib.stride_tricks.sliding_window_view(audio, FRAME_LENGTH)[starts]
    rms = np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=1)).astype(np.float32)
    return rms, (starts + FRAME_LENGTH // 2).astype(np.int64)


def _rms(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(a, dtype=np.float64)))) if a.size else 0.0


def _interp_to_samples(values: np.ndarray, centres: np.ndarray, n: int) -> np.ndarray:
    if values.size == 0:
        return np.ones(n, dtype=np.float32)
    if values.size == 1:
        return np.full(n, float(values[0]), dtype=np.float32)
    return np.interp(np.arange(n), centres, values).astype(np.float32)


def vocal_rider(
    audio: np.ndarray,
    sample_rate: int,
    target_percentile: float = 70.0,
    max_boost_db: float = 6.0,
    max_cut_db: float = 6.0,
    smoothing_ms: float = 120.0,
    silence_floor_db: float = -45.0,
) -> np.ndarray:
    """Phrase-level gain automation: bring quiet words up, hold loud words back.

    Runs before compression. A compressor reacts to peaks in milliseconds; a
    rider moves over syllables and phrases, so the compressor is left with much
    less work and stops pumping.

    The target level is a percentile of the *voiced* frames rather than the mean:
    silence and breaths would drag a mean down and make the rider boost noise.
    Frames below `silence_floor_db` are held at unity for exactly that reason.
    """
    mono = np.asarray(audio, dtype=np.float32)
    if mono.ndim == 2:
        mono = mono[:, 0]
    if mono.size == 0:
        return mono.copy()

    rms, centres = _frame_rms(mono)
    floor_linear = 10.0 ** (silence_floor_db / 20.0)
    voiced = rms > floor_linear
    if not np.any(voiced):
        return mono.copy()

    target = float(np.percentile(rms[voiced], target_percentile))
    if target <= 0.0:
        return mono.copy()

    with np.errstate(divide="ignore", invalid="ignore"):
        gain_db = 20.0 * np.log10(np.where(rms > 0, target / np.maximum(rms, 1e-12), 1.0))
    gain_db = np.clip(gain_db, -abs(max_cut_db), abs(max_boost_db))
    gain_db[~voiced] = 0.0  # never ride silence or breath noise upward

    envelope = _interp_to_samples(gain_db, centres, mono.size)
    envelope = _smooth_gain(envelope, sample_rate, smoothing_ms)
    return (mono * (10.0 ** (envelope / 20.0))).astype(np.float32)


def _band_energy(stft_mag: np.ndarray, freqs: np.ndarray, lo: float, hi: float) -> np.ndarray:
    mask = (freqs >= lo) & (freqs <= hi)
    if not np.any(mask):
        return np.zeros(stft_mag.shape[1], dtype=np.float32)
    return np.sqrt(np.mean(np.square(stft_mag[mask]), axis=0)).astype(np.float32)


def dynamic_eq(
    audio: np.ndarray,
    sample_rate: int,
    band_lo_hz: float = 200.0,
    band_hi_hz: float = 500.0,
    threshold_ratio: float = 1.3,
    max_reduction_db: float = 6.0,
    smoothing_ms: float = 40.0,
) -> np.ndarray:
    """Reduce a band only while it is excessive relative to the whole signal.

    `threshold_ratio` is measured against the band's own median energy, so the
    processor adapts to the material instead of assuming an absolute level. A
    ratio of 1.3 means "act when this band is 30% above its usual share".

    Implemented in the STFT domain: attenuation is applied to the band's bins
    per frame and inverted back, which avoids the filter-coefficient instability
    a time-varying IIR would risk when the gain moves quickly.
    """
    import librosa

    mono = np.asarray(audio, dtype=np.float32)
    if mono.ndim == 2:
        mono = mono[:, 0]
    if mono.size < FRAME_LENGTH:
        return mono.copy()

    stft = librosa.stft(mono, n_fft=FRAME_LENGTH, hop_length=HOP_LENGTH)
    mag, phase = np.abs(stft), np.angle(stft)
    freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=FRAME_LENGTH)

    band = _band_energy(mag, freqs, band_lo_hz, band_hi_hz)
    voiced = band > 0
    if not np.any(voiced):
        return mono.copy()
    reference = float(np.median(band[voiced]))
    if reference <= 0.0:
        return mono.copy()

    excess = np.maximum(band / reference - threshold_ratio, 0.0)
    # Map excess to attenuation, saturating so a single loud frame cannot pull
    # the band down by more than the declared maximum.
    reduction_db = -max_reduction_db * (excess / (excess + 1.0))
    reduction_db = _smooth_gain(reduction_db.astype(np.float32), sample_rate // HOP_LENGTH,
                                smoothing_ms)

    gain = (10.0 ** (reduction_db / 20.0)).astype(np.float32)
    mask = (freqs >= band_lo_hz) & (freqs <= band_hi_hz)
    mag[mask] *= gain[None, :]

    out = librosa.istft(mag * np.exp(1j * phase), hop_length=HOP_LENGTH, length=mono.size)
    return out.astype(np.float32)


def suppress_resonances(
    audio: np.ndarray,
    sample_rate: int,
    search_lo_hz: float = 150.0,
    search_hi_hz: float = 6000.0,
    max_resonances: int = 3,
    prominence_ratio: float = 2.0,
    max_reduction_db: float = 6.0,
) -> np.ndarray:
    """Find narrow persistent peaks and reduce each one while it rings.

    An untreated room adds resonances: narrow frequencies that ring on and make a
    vocal sound boxy or honky. They differ per room and per voice, so a fixed EQ
    curve cannot address them — they have to be found in the material.

    A peak qualifies only if it is `prominence_ratio` above the local spectral
    neighbourhood in the *median* spectrum, i.e. persistent across the take. A
    peak present in only a few frames is a note, not a resonance, and reducing it
    would attack the performance.
    """
    import librosa

    mono = np.asarray(audio, dtype=np.float32)
    if mono.ndim == 2:
        mono = mono[:, 0]
    if mono.size < FRAME_LENGTH:
        return mono.copy()

    stft = librosa.stft(mono, n_fft=FRAME_LENGTH, hop_length=HOP_LENGTH)
    mag, phase = np.abs(stft), np.angle(stft)
    freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=FRAME_LENGTH)

    median_spectrum = np.median(mag, axis=1)
    in_range = (freqs >= search_lo_hz) & (freqs <= search_hi_hz)
    if not np.any(in_range) or float(np.max(median_spectrum)) <= 0.0:
        return mono.copy()

    # Local neighbourhood = a smoothed copy of the median spectrum. A resonance
    # stands above its own neighbourhood; broadband tilt does not.
    kernel = max(3, int(len(freqs) * 0.02) | 1)
    smoothed = np.convolve(median_spectrum, np.ones(kernel) / kernel, mode="same")
    with np.errstate(divide="ignore", invalid="ignore"):
        prominence = np.where(smoothed > 0, median_spectrum / np.maximum(smoothed, 1e-12), 0.0)
    prominence[~in_range] = 0.0

    candidates = np.argsort(prominence)[::-1]
    chosen: list[int] = []
    for idx in candidates:
        if prominence[idx] < prominence_ratio:
            break
        # Keep peaks apart so three adjacent bins are not treated as three
        # separate resonances.
        if any(abs(freqs[idx] - freqs[c]) < 100.0 for c in chosen):
            continue
        chosen.append(int(idx))
        if len(chosen) >= max_resonances:
            break

    if not chosen:
        return mono.copy()

    for idx in chosen:
        centre = freqs[idx]
        width = max(centre * 0.05, 30.0)  # narrow: resonances are not wide
        band_mask = (freqs >= centre - width) & (freqs <= centre + width)
        band = _band_energy(mag, freqs, centre - width, centre + width)
        reference = float(np.median(band[band > 0])) if np.any(band > 0) else 0.0
        if reference <= 0.0:
            continue
        excess = np.maximum(band / reference - 1.0, 0.0)
        reduction_db = -max_reduction_db * (excess / (excess + 1.0))
        gain = (10.0 ** (reduction_db / 20.0)).astype(np.float32)
        mag[band_mask] *= gain[None, :]

    out = librosa.istft(mag * np.exp(1j * phase), hop_length=HOP_LENGTH, length=mono.size)
    return out.astype(np.float32)


def saturate(
    audio: np.ndarray,
    sample_rate: int,
    drive_db: float = 6.0,
    character: float = 0.5,
    mix: float = 0.5,
    oversample: int = 4,
) -> np.ndarray:
    """Oversampled, blended soft saturation.

    Three things separate this from raw `Distortion`:

    1. Oversampling. A nonlinearity generates harmonics above the original
       bandwidth; at 1x those fold back down as inharmonic aliasing, which is the
       harsh digital grit that makes cheap saturation unusable on vocals. Running
       at 4x and filtering before decimation keeps the added harmonics musical.
    2. A character control between a soft tanh curve (warm, compressive) and a
       harder cubic-clip curve (aggressive, more odd harmonics).
    3. A wet/dry mix, so the dry transient survives. Fully-wet saturation flattens
       consonants; blending keeps articulation while adding density.
    """
    mono = np.asarray(audio, dtype=np.float32)
    if mono.ndim == 2:
        mono = mono[:, 0]
    if mono.size == 0:
        return mono.copy()

    factor = max(1, int(oversample))
    drive = 10.0 ** (float(drive_db) / 20.0)
    blend = float(np.clip(mix, 0.0, 1.0))
    char = float(np.clip(character, 0.0, 1.0))

    if factor > 1:
        up = np.interp(
            np.linspace(0, mono.size - 1, mono.size * factor, dtype=np.float64),
            np.arange(mono.size),
            mono,
        ).astype(np.float32)
    else:
        up = mono.copy()

    driven = up * drive
    soft = np.tanh(driven)
    hard = np.clip(driven - (driven ** 3) / 3.0, -2.0 / 3.0, 2.0 / 3.0) * 1.5
    shaped = ((1.0 - char) * soft + char * hard).astype(np.float32)

    if factor > 1:
        # Pre-decimation lowpass: without it the harmonics we just created alias.
        taps = factor * 8 + 1
        window = np.hanning(taps).astype(np.float32)
        sinc = np.sinc(np.linspace(-4, 4, taps) / factor).astype(np.float32)
        kernel = window * sinc
        kernel /= np.sum(kernel)
        shaped = np.convolve(shaped, kernel, mode="same").astype(np.float32)
        shaped = shaped[::factor][: mono.size]
    if shaped.size < mono.size:
        shaped = np.pad(shaped, (0, mono.size - shaped.size))

    # Level-match the wet branch so `mix` changes character, not loudness.
    dry_rms, wet_rms = _rms(mono), _rms(shaped)
    if wet_rms > 0 and dry_rms > 0:
        shaped = shaped * np.float32(dry_rms / wet_rms)

    return ((1.0 - blend) * mono + blend * shaped).astype(np.float32)
