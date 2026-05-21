"""Core DSP pipeline using Spotify Pedalboard.

Supports two modes:
1. Generic cleanup chain (Alpha 1) — fixed parameters, backward compatible.
2. Adaptive chain (Alpha 2) — driven by VocalProfile diagnosis results.
"""

from __future__ import annotations

from dataclasses import dataclass

import librosa
import numpy as np
import soundfile as sf
from pedalboard import (
    Compressor,
    Gain,
    HighpassFilter,
    HighShelfFilter,
    Limiter,
    NoiseGate,
    Pedalboard,
    PeakFilter,
)

from src.dsp.diagnose import Severity, VocalProfile


@dataclass(frozen=True)
class CleanupParams:
    """Bounded parameters for the generic cleanup DSP chain."""

    # Highpass filter
    highpass_hz: float = 80.0  # min=20, max=500

    # De-harsh EQ: cut harsh upper-mid frequencies
    harsh_freq_hz: float = 3500.0  # min=2000, max=8000
    harsh_gain_db: float = -4.0  # min=-12, max=0
    harsh_q: float = 1.5  # min=0.5, max=5.0

    # Secondary presence taming
    presence_freq_hz: float = 6500.0  # min=4000, max=10000
    presence_gain_db: float = -2.5  # min=-12, max=0
    presence_q: float = 2.0  # min=0.5, max=5.0

    # Compression
    comp_threshold_db: float = -18.0  # min=-40, max=0
    comp_ratio: float = 3.0  # min=1.0, max=20.0
    comp_attack_ms: float = 10.0  # min=0.1, max=100
    comp_release_ms: float = 100.0  # min=10, max=1000

    # Noise gate
    gate_threshold_db: float = -40.0  # min=-80, max=-10
    gate_attack_ms: float = 1.0  # min=0.1, max=50
    gate_release_ms: float = 100.0  # min=10, max=500

    # Output gain normalization
    output_gain_db: float = 2.0  # min=-12, max=12


def build_cleanup_chain(params: CleanupParams | None = None) -> Pedalboard:
    """Build the generic cleanup-stage Pedalboard chain (Alpha 1 behavior)."""
    if params is None:
        params = CleanupParams()

    return Pedalboard([
        HighpassFilter(cutoff_frequency_hz=params.highpass_hz),
        PeakFilter(
            cutoff_frequency_hz=params.harsh_freq_hz,
            gain_db=params.harsh_gain_db,
            q=params.harsh_q,
        ),
        PeakFilter(
            cutoff_frequency_hz=params.presence_freq_hz,
            gain_db=params.presence_gain_db,
            q=params.presence_q,
        ),
        Compressor(
            threshold_db=params.comp_threshold_db,
            ratio=params.comp_ratio,
            attack_ms=params.comp_attack_ms,
            release_ms=params.comp_release_ms,
        ),
        NoiseGate(
            threshold_db=params.gate_threshold_db,
            attack_ms=params.gate_attack_ms,
            release_ms=params.gate_release_ms,
        ),
        Gain(gain_db=params.output_gain_db),
    ])


# ---------------------------------------------------------------------------
# Adaptive chain (driven by VocalProfile)
# ---------------------------------------------------------------------------


def _gain_for_severity(severity: Severity, mild: float, moderate: float, severe: float) -> float:
    """Map severity to a parameter value."""
    return {Severity.MILD: mild, Severity.MODERATE: moderate, Severity.SEVERE: severe}.get(
        severity, 0.0
    )


def build_adaptive_chain(profile: VocalProfile) -> Pedalboard:
    """Build a DSP chain that responds to the vocal's diagnosed problems.

    Alpha 2.2: keep the Alpha 2 baseline and add only light control.
    """
    plugins: list = []
    chain_description: list[str] = []

    clip_diag = profile.get_diagnosis("clipping")
    harsh_diag = profile.get_diagnosis("harshness")
    sib_diag = profile.get_diagnosis("sibilance")
    mud_diag = profile.get_diagnosis("muddiness")
    noise_diag = profile.get_diagnosis("noise_floor")
    dyn_diag = profile.get_diagnosis("dynamic_inconsistency")
    dull_diag = profile.get_diagnosis("dullness")

    def _s(sev) -> int:
        return {Severity.NONE: 0, Severity.MILD: 1, Severity.MODERATE: 2, Severity.SEVERE: 3}.get(sev, 0)

    # 1. Gain staging — pull back if clipping
    if clip_diag and _s(clip_diag.severity) >= _s(Severity.MILD):
        gain_db = _gain_for_severity(clip_diag.severity, -1.0, -3.0, -6.0)
        plugins.append(Gain(gain_db=gain_db))
        chain_description.append(f"Gain({gain_db:.0f}dB)")

    # 2. Highpass — always apply, more aggressive if muddy
    hpf_hz = 80.0
    if mud_diag and _s(mud_diag.severity) >= _s(Severity.MODERATE):
        hpf_hz = 100.0
    plugins.append(HighpassFilter(cutoff_frequency_hz=hpf_hz))
    chain_description.append(f"HPF({hpf_hz:.0f}Hz)")

    # 3a. Mud cut (200-400Hz) — only if detected
    if mud_diag and _s(mud_diag.severity) >= _s(Severity.MILD):
        freq = mud_diag.detected_frequency_hz or 300.0
        gain = _gain_for_severity(mud_diag.severity, -2.0, -3.0, -4.0)
        plugins.append(PeakFilter(cutoff_frequency_hz=freq, gain_db=gain, q=0.8))
        chain_description.append(f"mud cut({freq:.0f}Hz, {gain:.0f}dB)")

    # 3b. Harshness cut — one surgical notch, not a broad sweep
    if harsh_diag and _s(harsh_diag.severity) >= _s(Severity.MILD):
        freq = harsh_diag.detected_frequency_hz or 3500.0
        gain = _gain_for_severity(harsh_diag.severity, -2.0, -3.5, -4.5)
        plugins.append(PeakFilter(cutoff_frequency_hz=freq, gain_db=gain, q=1.4))
        chain_description.append(f"harsh cut({freq:.0f}Hz, {gain:.0f}dB)")

    # 3c. Sibilance cut — mild static help, real cleanup happens in localized refinement
    if sib_diag and _s(sib_diag.severity) >= _s(Severity.MILD):
        freq = sib_diag.detected_frequency_hz or 6200.0
        gain = _gain_for_severity(sib_diag.severity, -1.5, -2.5, -3.5)
        plugins.append(PeakFilter(cutoff_frequency_hz=freq, gain_db=gain, q=3.5))
        chain_description.append(f"sibilance cut({freq:.0f}Hz, {gain:.0f}dB)")

    # 4. Noise gate — only if noise floor is problematic
    if noise_diag and _s(noise_diag.severity) >= _s(Severity.MILD):
        noise_db = noise_diag.measured_value or -50.0
        gate_threshold = min(-42.0, noise_db + 6.0)
        plugins.append(NoiseGate(
            threshold_db=gate_threshold,
            attack_ms=1.0,
            release_ms=250.0,
        ))
        chain_description.append(f"gate({gate_threshold:.0f}dB)")

    # 5. Compression — only if dynamics are inconsistent
    if dyn_diag and _s(dyn_diag.severity) >= _s(Severity.MILD):
        threshold = _gain_for_severity(dyn_diag.severity, -22.0, -20.0, -18.0)
        ratio = _gain_for_severity(dyn_diag.severity, 2.5, 3.0, 3.5)
        plugins.append(Compressor(
            threshold_db=threshold,
            ratio=ratio,
            attack_ms=15.0,
            release_ms=75.0,
        ))
        chain_description.append(f"comp({ratio:.1f}:1, {threshold:.0f}dB)")

    # 6. Air boost — only if dull AND noise floor is acceptable AND not harsh
    noise_ok = not noise_diag or _s(noise_diag.severity) < _s(Severity.MODERATE)
    harsh_ok = not harsh_diag or _s(harsh_diag.severity) < _s(Severity.MILD)
    if dull_diag and _s(dull_diag.severity) >= _s(Severity.MILD) and noise_ok and harsh_ok:
        gain = _gain_for_severity(dull_diag.severity, 1.5, 2.5, 3.0)
        plugins.append(HighShelfFilter(cutoff_frequency_hz=10000, gain_db=gain, q=0.7))
        chain_description.append(f"air(+{gain:.1f}dB)")

    # 7. Output limiter — softer ceiling, final trim handled in localized refinement
    plugins.append(Limiter(threshold_db=-1.2, release_ms=250.0))
    chain_description.append("limiter(-1.2dB)")

    board = Pedalboard(plugins)
    board._chain_description = chain_description  # type: ignore[attr-defined]
    return board


def get_chain_description(board: Pedalboard) -> str:
    """Get human-readable chain description if available."""
    desc = getattr(board, "_chain_description", None)
    if desc:
        return " -> ".join(desc)
    return "generic cleanup chain"


def _frame_band_energy(
    stft_mag: np.ndarray,
    freqs: np.ndarray,
    low_hz: float,
    high_hz: float,
) -> np.ndarray:
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(mask):
        return np.zeros(stft_mag.shape[1], dtype=np.float32)
    return np.mean(stft_mag[mask, :] ** 2, axis=0).astype(np.float32)


def _interpolate_frame_curve(values: np.ndarray, num_samples: int, hop_length: int) -> np.ndarray:
    if len(values) == 0:
        return np.ones(num_samples, dtype=np.float32)
    frame_positions = np.arange(len(values), dtype=np.float32) * hop_length
    sample_positions = np.arange(num_samples, dtype=np.float32)
    envelope = np.interp(sample_positions, frame_positions, values, left=values[0], right=values[-1])
    return envelope.astype(np.float32)


def apply_alpha22_refinement(audio: np.ndarray, sample_rate: int) -> tuple[np.ndarray, list[str]]:
    """Apply very light localized control without changing the core chain tone."""
    if audio.ndim == 1:
        audio = audio.reshape(-1, 1)

    mono = audio[:, 0].astype(np.float32)
    if len(mono) < 2048:
        return audio, []

    hop_length = 256
    stft = librosa.stft(mono, n_fft=2048, hop_length=hop_length)
    stft_mag = np.abs(stft)
    freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=2048)

    total_energy = np.mean(stft_mag**2, axis=0) + 1e-12
    low_ratio = _frame_band_energy(stft_mag, freqs, 80, 220) / total_energy
    sib_ratio = _frame_band_energy(stft_mag, freqs, 5000, 8500) / total_energy
    harsh_ratio = _frame_band_energy(stft_mag, freqs, 2500, 6000) / total_energy

    peak_env = librosa.feature.rms(
        y=np.abs(mono),
        frame_length=2048,
        hop_length=hop_length,
        center=True,
    )[0]
    rms_env = librosa.feature.rms(
        y=mono,
        frame_length=2048,
        hop_length=hop_length,
        center=True,
    )[0]

    median_rms = float(np.median(rms_env) + 1e-12)
    low_threshold = max(0.18, float(np.percentile(low_ratio, 90)))
    sib_threshold = max(0.12, float(np.percentile(sib_ratio, 92)))
    harsh_threshold = max(0.10, float(np.percentile(harsh_ratio, 94)))

    plosive_db = np.where(
        (low_ratio > low_threshold) & (peak_env > median_rms * 1.8),
        np.clip((low_ratio - low_threshold) / max(low_threshold, 1e-6), 0.0, 1.0) * 1.0,
        0.0,
    )
    de_ess_db = np.where(
        (sib_ratio > sib_threshold) & (peak_env > median_rms * 1.25),
        np.clip((sib_ratio - sib_threshold) / max(sib_threshold, 1e-6), 0.0, 1.0) * 1.25,
        0.0,
    )
    peak_control_db = np.where(
        (harsh_ratio > harsh_threshold) & (peak_env > median_rms * 1.6),
        np.clip((harsh_ratio - harsh_threshold) / max(harsh_threshold, 1e-6), 0.0, 1.0) * 1.15,
        0.0,
    )

    total_db = np.minimum(plosive_db + de_ess_db + peak_control_db, 2.5).astype(np.float32)
    if np.any(total_db > 0.05):
        smoothing = np.array([0.15, 0.35, 1.0, 0.35, 0.15], dtype=np.float32)
        smoothing /= np.sum(smoothing)
        total_db = np.convolve(total_db, smoothing, mode="same").astype(np.float32)
        gain_curve = _interpolate_frame_curve(10.0 ** (-total_db / 20.0), len(mono), hop_length)
        refined = (audio * gain_curve[:, None]).astype(np.float32)
        steps = [
            "localized plosive smoothing",
            "localized de-essing",
            "localized high-note peak control",
        ]
    else:
        refined = audio.astype(np.float32)
        steps = []

    peak = float(np.max(np.abs(refined)))
    if peak > 0.92:
        safety_gain_db = -0.75 if peak <= 0.97 else -1.25
        refined *= np.float32(10.0 ** (safety_gain_db / 20.0))
        steps.append(f"output trim({safety_gain_db:.2f}dB)")

    return refined, steps


# ---------------------------------------------------------------------------
# Audio processing
# ---------------------------------------------------------------------------


def process_audio(
    input_path: str,
    output_path: str,
    params: CleanupParams | None = None,
    profile: VocalProfile | None = None,
) -> dict:
    """Run DSP chain on a WAV file.

    If profile is provided, builds an adaptive chain. Otherwise uses the
    generic cleanup chain (backward compatible with Alpha 1).

    Args:
        input_path: Path to preprocessed WAV (44100Hz, 16-bit, mono).
        output_path: Path where processed WAV will be written.
        params: Optional custom cleanup parameters (ignored if profile given).
        profile: Optional VocalProfile for adaptive processing.

    Returns:
        Dict with processing metadata.
    """
    audio, sample_rate = sf.read(input_path, dtype="float32")

    if audio.ndim == 1:
        audio = audio.reshape(-1, 1)

    if profile is not None:
        board = build_adaptive_chain(profile)
    else:
        board = build_cleanup_chain(params)

    # Pedalboard expects (channels, samples) float32
    audio_transposed = audio.T
    processed = board(audio_transposed, sample_rate)

    # Transpose back to (samples, channels) for soundfile
    processed_out = processed.T
    refinement_steps: list[str] = []
    if profile is not None:
        processed_out, refinement_steps = apply_alpha22_refinement(processed_out, sample_rate)
    processed_out = np.clip(processed_out, -1.0, 1.0)

    sf.write(output_path, processed_out, sample_rate, subtype="PCM_16")

    duration_seconds = len(processed_out) / sample_rate

    return {
        "sample_rate": sample_rate,
        "duration_seconds": float(duration_seconds),
        "total_samples": len(processed_out),
        "output_path": output_path,
        "chain_description": " -> ".join(
            part for part in [get_chain_description(board), *refinement_steps] if part
        ),
    }
