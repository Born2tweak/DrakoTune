"""Vocal diagnostic engine — analyzes raw audio and produces a VocalProfile.

Milestone Alpha 2: Detects 7 highest-impact vocal issues using Librosa/Numpy.
The VocalProfile drives adaptive DSP chain construction in pipeline.py.

Categories detected:
  1. Harshness — elevated energy in 2.5-6kHz
  2. Sibilance — transient spikes in 5-8kHz
  3. Muddiness — excessive energy in 200-400Hz
  4. Clipping — samples near digital full scale
  5. Noise floor — energy in silent regions
  6. Dynamic inconsistency — large RMS variance
  7. Dullness — low energy above 5kHz
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


class Severity(IntEnum):
    NONE = 0
    MILD = 1
    MODERATE = 2
    SEVERE = 3


@dataclass(frozen=True)
class DiagnosisResult:
    """Single diagnostic finding."""

    category: str
    severity: Severity
    confidence: float  # 0.0-1.0
    detected_frequency_hz: float | None = None
    measured_value: float | None = None
    threshold: float | None = None
    recommendation: str = ""


@dataclass
class VocalProfile:
    """Complete diagnostic report for a raw vocal file."""

    file_path: str
    sample_rate: int
    duration_seconds: float
    diagnoses: list[DiagnosisResult] = field(default_factory=list)
    overall_quality_score: float = 0.0  # 0-100
    warnings: list[str] = field(default_factory=list)

    @property
    def has_severe(self) -> bool:
        return any(d.severity == Severity.SEVERE for d in self.diagnoses)

    def get_diagnosis(self, category: str) -> DiagnosisResult | None:
        for d in self.diagnoses:
            if d.category == category:
                return d
        return None

    def summary(self) -> str:
        lines = [
            f"Vocal Profile: {Path(self.file_path).name}",
            f"Duration: {self.duration_seconds:.1f}s | Sample rate: {self.sample_rate}Hz",
            f"Quality score: {self.overall_quality_score:.0f}/100",
            "",
        ]
        active = [d for d in self.diagnoses if d.severity != Severity.NONE]
        if not active:
            lines.append("  No issues detected.")
        else:
            for d in active:
                freq_str = (
                    f" (peak at {d.detected_frequency_hz:.0f}Hz)"
                    if d.detected_frequency_hz
                    else ""
                )
                lines.append(f"  {d.category}: {d.severity.name}{freq_str}")
                if d.recommendation:
                    lines.append(f"    -> {d.recommendation}")
        if self.warnings:
            lines.append("")
            for w in self.warnings:
                lines.append(f"  WARNING: {w}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Band energy helpers (operate on pre-computed STFT)
# ---------------------------------------------------------------------------


def _band_energy(
    stft_mag: np.ndarray, freqs: np.ndarray, low_hz: float, high_hz: float
) -> float:
    """Mean sum-of-squares in a frequency band."""
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.sum(stft_mag[mask, :] ** 2, axis=1)))


def _band_energy_ratio(
    stft_mag: np.ndarray,
    freqs: np.ndarray,
    num_low: float,
    num_high: float,
    den_low: float,
    den_high: float,
) -> float:
    """Ratio of energy in numerator band to denominator band."""
    num = _band_energy(stft_mag, freqs, num_low, num_high)
    den = _band_energy(stft_mag, freqs, den_low, den_high)
    if den < 1e-12:
        return 0.0
    return num / den


def _find_peak_frequency(
    stft_mag: np.ndarray, freqs: np.ndarray, low_hz: float, high_hz: float
) -> float:
    """Frequency with highest average energy in a band."""
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(mask):
        return (low_hz + high_hz) / 2.0
    band_energy = np.mean(stft_mag[mask, :] ** 2, axis=1)
    return float(freqs[mask][np.argmax(band_energy)])


def _severity_from_thresholds(
    value: float, mild: float, moderate: float, severe: float
) -> Severity:
    """Map a measured value to severity. Higher value = worse."""
    if value >= severe:
        return Severity.SEVERE
    if value >= moderate:
        return Severity.MODERATE
    if value >= mild:
        return Severity.MILD
    return Severity.NONE


# ---------------------------------------------------------------------------
# 7 diagnostic checks
# ---------------------------------------------------------------------------


def _detect_harshness(
    audio: np.ndarray, sr: int, stft_mag: np.ndarray, freqs: np.ndarray
) -> DiagnosisResult:
    # Harshness = narrow-band energy concentration in 2.5-6kHz, not just high energy
    harsh_band = _band_energy(stft_mag, freqs, 2500, 6000)
    ref_band = _band_energy(stft_mag, freqs, 200, 2000)
    ratio = harsh_band / ref_band if ref_band > 1e-12 else 0.0

    # Spectral contrast: harsh = concentrated peaks, not broad energy
    # Compute spectral flatness in harsh band (low flatness = tonal/harsh)
    mask = (freqs >= 2500) & (freqs <= 6000)
    if np.any(mask):
        # Get mean energy per frequency bin across time
        harsh_energy = np.mean(stft_mag[mask, :] ** 2, axis=1)
        # Add small constant to avoid log(0)
        harsh_energy_db = 10 * np.log10(harsh_energy + 1e-12)
        # Spectral contrast = max - mean in harsh band
        # High contrast = narrow peaks = harsh
        spectral_contrast = float(np.max(harsh_energy_db) - np.mean(harsh_energy_db))
        # Normalize: contrast > 10dB = likely harsh, < 3dB = broad spectrum
        contrast_factor = max(0.0, min(1.0, (spectral_contrast - 3.0) / 7.0))
    else:
        contrast_factor = 0.0

    # Only flag as harsh if both: high ratio AND high spectral contrast (narrow peaks)
    # Broad-spectrum bright signals have low contrast
    effective_ratio = ratio * contrast_factor

    severity = _severity_from_thresholds(effective_ratio, 0.10, 0.25, 0.50)
    peak_freq = _find_peak_frequency(stft_mag, freqs, 2500, 6000)

    rec = {
        Severity.MILD: f"Gentle EQ cut at {peak_freq:.0f}Hz (-2dB, Q=1.5)",
        Severity.MODERATE: f"EQ cut at {peak_freq:.0f}Hz (-4dB, Q=1.5)",
        Severity.SEVERE: f"Strong EQ cut at {peak_freq:.0f}Hz (-5dB, Q=1.2)",
    }.get(severity, "")

    return DiagnosisResult(
        category="harshness",
        severity=severity,
        confidence=min(1.0, effective_ratio / 0.50),
        detected_frequency_hz=peak_freq if severity != Severity.NONE else None,
        measured_value=effective_ratio,
        threshold=0.10,
        recommendation=rec,
    )


def _detect_sibilance(
    audio: np.ndarray, sr: int, stft_mag: np.ndarray, freqs: np.ndarray
) -> DiagnosisResult:
    sib = _band_energy(stft_mag, freqs, 5000, 8000)
    mid = _band_energy(stft_mag, freqs, 200, 4000)
    ratio = sib / mid if mid > 1e-12 else 0.0
    severity = _severity_from_thresholds(ratio, 0.15, 0.30, 0.50)
    peak_freq = _find_peak_frequency(stft_mag, freqs, 5000, 8000)

    rec = {
        Severity.MILD: f"Gentle sibilance cut at {peak_freq:.0f}Hz (-2dB, Q=4.0)",
        Severity.MODERATE: f"Sibilance cut at {peak_freq:.0f}Hz (-4dB, Q=4.0)",
        Severity.SEVERE: f"Strong sibilance cut at {peak_freq:.0f}Hz (-5dB, Q=3.5)",
    }.get(severity, "")

    return DiagnosisResult(
        category="sibilance",
        severity=severity,
        confidence=min(1.0, ratio / 0.50),
        detected_frequency_hz=peak_freq if severity != Severity.NONE else None,
        measured_value=ratio,
        threshold=0.15,
        recommendation=rec,
    )


def _detect_muddiness(
    audio: np.ndarray, sr: int, stft_mag: np.ndarray, freqs: np.ndarray
) -> DiagnosisResult:
    # Muddiness = excess energy in 200-500Hz (extended to catch boxy resonance)
    mud_energy = _band_energy(stft_mag, freqs, 200, 500)
    mid_energy = _band_energy(stft_mag, freqs, 1000, 4000)
    high_energy = _band_energy(stft_mag, freqs, 4000, 8000)
    total_energy = _band_energy(stft_mag, freqs, 20, 20000)

    # If mud energy is negligible compared to total, not muddy
    mud_ratio_total = mud_energy / total_energy if total_energy > 1e-12 else 0.0
    if mud_ratio_total < 0.05:
        return DiagnosisResult(
            category="muddiness",
            severity=Severity.NONE,
            confidence=0.8,
            recommendation="No significant muddiness detected",
        )

    # Compute mud ratio vs mids+highs
    ref_energy = mid_energy + high_energy
    if ref_energy < 1e-12:
        # No mids/highs at all — if mud is dominant, it's muddy
        ratio = mud_ratio_total
        severity = _severity_from_thresholds(ratio, 0.30, 0.50, 0.80)
        peak_freq = _find_peak_frequency(stft_mag, freqs, 200, 500)
        rec = {
            Severity.MILD: f"Gentle mud cut at {peak_freq:.0f}Hz (-2dB, Q=0.8)",
            Severity.MODERATE: f"Mud cut at {peak_freq:.0f}Hz (-3dB, Q=0.8)",
            Severity.SEVERE: f"Strong mud cut at {peak_freq:.0f}Hz (-4dB, Q=0.8)",
        }.get(severity, "")
        return DiagnosisResult(
            category="muddiness",
            severity=severity,
            confidence=min(1.0, ratio / 0.80),
            detected_frequency_hz=peak_freq if severity != Severity.NONE else None,
            measured_value=ratio,
            threshold=0.30,
            recommendation=rec,
        )

    ratio = mud_energy / ref_energy
    severity = _severity_from_thresholds(ratio, 0.45, 0.70, 1.0)
    mean_flatness = float(np.mean(librosa.feature.spectral_flatness(y=audio)[0]))
    if severity == Severity.SEVERE and mean_flatness < 0.01:
        severity = Severity.MODERATE
    peak_freq = _find_peak_frequency(stft_mag, freqs, 200, 500)

    rec = {
        Severity.MILD: f"Gentle mud cut at {peak_freq:.0f}Hz (-2dB, Q=0.8)",
        Severity.MODERATE: f"Mud cut at {peak_freq:.0f}Hz (-3dB, Q=0.8)",
        Severity.SEVERE: f"Strong mud cut at {peak_freq:.0f}Hz (-4dB, Q=0.8)",
    }.get(severity, "")

    return DiagnosisResult(
        category="muddiness",
        severity=severity,
        confidence=min(1.0, ratio / 1.0),
        detected_frequency_hz=peak_freq if severity != Severity.NONE else None,
        measured_value=ratio,
        threshold=0.45,
        recommendation=rec,
    )


def _detect_clipping(audio: np.ndarray, sr: int) -> DiagnosisResult:
    total = len(audio)
    if total == 0:
        return DiagnosisResult(category="clipping", severity=Severity.NONE, confidence=1.0)

    # Hard clipping: samples at or near digital full scale (±0.99)
    hard_clip_count = int(np.sum(np.abs(audio) > 0.99))
    # Soft clipping: samples in near-full-scale region (±0.95-0.99)
    soft_clip_count = int(np.sum((np.abs(audio) > 0.95) & (np.abs(audio) <= 0.99)))

    # Weight soft clipping less than hard clipping
    clip_count = hard_clip_count + (soft_clip_count // 4)
    clip_ratio = clip_count / total
    severity = _severity_from_thresholds(clip_ratio, 0.001, 0.005, 0.02)

    rec = {
        Severity.MILD: "Minor clipping — apply -1dB gain then limiter",
        Severity.MODERATE: "Clipping detected — apply -3dB gain then limiter at -1dBFS",
        Severity.SEVERE: "Severe clipping — consider re-recording. Applying -6dB gain + limiter",
    }.get(severity, "")

    return DiagnosisResult(
        category="clipping",
        severity=severity,
        confidence=1.0,
        measured_value=clip_ratio,
        threshold=0.001,
        recommendation=rec,
    )


def _detect_noise_floor(audio: np.ndarray, sr: int) -> DiagnosisResult:
    # Remove DC offset before measuring noise floor
    audio_ac = audio - np.mean(audio)

    intervals = librosa.effects.split(audio_ac, top_db=25)

    if len(intervals) == 0:
        # No speech/silence distinction — signal is continuous
        # Check if signal is tonal (low spectral flatness) — tonal signals have no meaningful noise floor
        spectral_flatness = librosa.feature.spectral_flatness(y=audio_ac)[0]
        mean_flatness = float(np.mean(spectral_flatness))
        if mean_flatness < 0.01:
            # Highly tonal signal (e.g., sine wave) — noise floor is not applicable
            return DiagnosisResult(
                category="noise_floor",
                severity=Severity.NONE,
                confidence=0.9,
                measured_value=-80.0,
                threshold=-50.0,
                recommendation="No measurable noise floor — signal is tonal",
            )
        # For non-tonal continuous signals, estimate noise floor from troughs
        hop_length = sr // 50
        frame_length = hop_length * 2
        rms = librosa.feature.rms(y=audio_ac, frame_length=frame_length, hop_length=hop_length)[0]
        noise_rms = float(np.percentile(rms, 5))
    else:
        silent_mask = np.ones(len(audio_ac), dtype=bool)
        for start, end in intervals:
            silent_mask[start:end] = False

        silent_samples = audio_ac[silent_mask]
        if len(silent_samples) < sr // 10:
            # Not enough silence — check if signal is tonal
            spectral_flatness = librosa.feature.spectral_flatness(y=audio_ac)[0]
            mean_flatness = float(np.mean(spectral_flatness))
            if mean_flatness < 0.01:
                return DiagnosisResult(
                    category="noise_floor",
                    severity=Severity.NONE,
                    confidence=0.9,
                    measured_value=-80.0,
                    threshold=-50.0,
                    recommendation="No measurable noise floor — signal is tonal",
                )
            # Use percentile approach for non-tonal continuous signals
            hop_length = sr // 50
            frame_length = hop_length * 2
            rms = librosa.feature.rms(y=audio_ac, frame_length=frame_length, hop_length=hop_length)[0]
            noise_rms = float(np.percentile(rms, 5))
        else:
            noise_rms = float(np.sqrt(np.mean(silent_samples**2)))

    noise_db = float(20 * np.log10(noise_rms + 1e-12))

    if noise_db > -35:
        severity = Severity.SEVERE
    elif noise_db > -42:
        severity = Severity.MODERATE
    elif noise_db > -50:
        severity = Severity.MILD
    else:
        severity = Severity.NONE

    rec = {
        Severity.MILD: f"Noise floor at {noise_db:.0f}dBFS — apply noise gate",
        Severity.MODERATE: f"Noise floor at {noise_db:.0f}dBFS — gate + gentle high-freq cut",
        Severity.SEVERE: f"Noise floor at {noise_db:.0f}dBFS — consider re-recording",
    }.get(severity, "")

    return DiagnosisResult(
        category="noise_floor",
        severity=severity,
        confidence=0.8,
        measured_value=noise_db,
        threshold=-50.0,
        recommendation=rec,
    )


def _detect_dynamic_inconsistency(audio: np.ndarray, sr: int) -> DiagnosisResult:
    hop_length = sr // 10
    frame_length = hop_length * 2
    rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]

    if len(rms) < 5:
        return DiagnosisResult(
            category="dynamic_inconsistency",
            severity=Severity.NONE,
            confidence=0.5,
        )

    # Use all frames including silence — large swings indicate inconsistency
    # But ignore very low-level noise floor
    rms_threshold = np.max(rms) * 0.02
    vocal_rms = rms[rms > rms_threshold]

    if len(vocal_rms) < 5:
        return DiagnosisResult(
            category="dynamic_inconsistency",
            severity=Severity.NONE,
            confidence=0.5,
        )

    cv = float(np.std(vocal_rms) / (np.mean(vocal_rms) + 1e-12))
    severity = _severity_from_thresholds(cv, 0.15, 0.40, 0.70)

    rec = {
        Severity.MILD: "Mild dynamics — gentle compression (3:1, -18dB threshold)",
        Severity.MODERATE: "Uneven dynamics — moderate compression (4:1, -16dB threshold)",
        Severity.SEVERE: "Very inconsistent dynamics — consider serial compression",
    }.get(severity, "")

    return DiagnosisResult(
        category="dynamic_inconsistency",
        severity=severity,
        confidence=min(1.0, cv / 0.70),
        measured_value=cv,
        threshold=0.15,
        recommendation=rec,
    )


def _detect_dullness(
    audio: np.ndarray, sr: int, stft_mag: np.ndarray, freqs: np.ndarray
) -> DiagnosisResult:
    ratio = _band_energy_ratio(stft_mag, freqs, 5000, 12000, 200, 4000)
    mean_flatness = float(np.mean(librosa.feature.spectral_flatness(y=audio)[0]))

    if ratio < 0.03:
        severity = Severity.SEVERE
    elif ratio < 0.06:
        severity = Severity.MODERATE
    elif ratio < 0.10:
        severity = Severity.MILD
    else:
        severity = Severity.NONE

    if severity == Severity.SEVERE and mean_flatness < 0.01:
        severity = Severity.MODERATE

    rec = {
        Severity.MILD: "Slightly dull — gentle air boost at 10kHz (+1.5dB)",
        Severity.MODERATE: "Dull vocal — air boost at 10kHz (+2.5dB)",
        Severity.SEVERE: "Very dull — air boost at 10kHz (+3dB), check mic quality",
    }.get(severity, "")

    return DiagnosisResult(
        category="dullness",
        severity=severity,
        confidence=1.0 - min(1.0, ratio / 0.10),
        measured_value=ratio,
        threshold=0.10,
        recommendation=rec,
    )


# ---------------------------------------------------------------------------
# Cross-reference rules
# ---------------------------------------------------------------------------


def _sev_int(s: Severity) -> int:
    """Convert Severity to comparable int."""
    return {Severity.NONE: 0, Severity.MILD: 1, Severity.MODERATE: 2, Severity.SEVERE: 3}.get(s, 0)


def _cross_reference(diagnoses: list[DiagnosisResult]) -> list[str]:
    by_cat = {d.category: d for d in diagnoses}
    warnings: list[str] = []

    harsh = by_cat.get("harshness")
    dull = by_cat.get("dullness")
    noise = by_cat.get("noise_floor")
    clip = by_cat.get("clipping")

    if harsh and _sev_int(harsh.severity) >= _sev_int(Severity.MILD) and dull and _sev_int(dull.severity) >= _sev_int(Severity.MILD):
        warnings.append(
            "Harshness + Dullness — uneven frequency response. "
            "Cut harshness first, then reassess dullness. Do NOT boost air yet."
        )

    if noise and _sev_int(noise.severity) >= _sev_int(Severity.MILD) and dull and _sev_int(dull.severity) >= _sev_int(Severity.MILD):
        warnings.append(
            "Noise floor + Dullness — boosting air will amplify noise. "
            "Address noise first."
        )

    if clip and _sev_int(clip.severity) >= _sev_int(Severity.MODERATE):
        warnings.append(
            "Significant clipping — other diagnoses may be unreliable on clipped audio. "
            "Consider re-recording."
        )

    return warnings


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def diagnose(audio_path: str) -> VocalProfile:
    """Analyze a preprocessed WAV and return a VocalProfile.

    Args:
        audio_path: Path to preprocessed WAV (44100Hz, 16-bit, mono).

    Returns:
        VocalProfile with diagnostic results for 7 categories.
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    audio, sr = sf.read(str(path), dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]

    duration = len(audio) / sr

    # Compute STFT once — shared across all spectral checks
    stft = librosa.stft(audio, n_fft=2048, hop_length=512)
    stft_mag = np.abs(stft)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

    diagnoses = [
        _detect_harshness(audio, sr, stft_mag, freqs),
        _detect_sibilance(audio, sr, stft_mag, freqs),
        _detect_muddiness(audio, sr, stft_mag, freqs),
        _detect_clipping(audio, sr),
        _detect_noise_floor(audio, sr),
        _detect_dynamic_inconsistency(audio, sr),
        _detect_dullness(audio, sr, stft_mag, freqs),
    ]

    warnings = _cross_reference(diagnoses)

    penalty_map = {Severity.MILD: 5, Severity.MODERATE: 12, Severity.SEVERE: 20}
    total_penalty = sum(penalty_map.get(d.severity, 0) for d in diagnoses)
    quality_score = max(0.0, 100.0 - total_penalty)

    return VocalProfile(
        file_path=audio_path,
        sample_rate=sr,
        duration_seconds=duration,
        diagnoses=diagnoses,
        overall_quality_score=quality_score,
        warnings=warnings,
    )


@dataclass(frozen=True)
class ArtifactWindow:
    """A localized artifact detected in a time window."""

    start_sec: float
    end_sec: float
    issue: str  # "clipping_burst" or "hf_spike"
    measured_value: float


def scan_artifacts(
    audio_path: str, window_sec: float = 1.0
) -> list[ArtifactWindow]:
    """Scan audio in 1-second windows for localized clipping bursts and HF spikes.

    Args:
        audio_path: Path to preprocessed WAV.
        window_sec: Window size in seconds (default 1.0).

    Returns:
        List of ArtifactWindow indicating suspicious timestamps.
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    audio, sr = sf.read(str(path), dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]

    window_samples = int(sr * window_sec)
    total_samples = len(audio)
    artifacts: list[ArtifactWindow] = []

    # Pre-compute global HF energy baseline for spike detection
    stft_global = librosa.stft(audio, n_fft=2048, hop_length=512)
    freqs_global = librosa.fft_frequencies(sr=sr, n_fft=2048)
    hf_mask = (freqs_global >= 6000) & (freqs_global <= 10000)
    global_hf_energy = float(np.mean(np.abs(stft_global[hf_mask, :]) ** 2))

    for start in range(0, total_samples, window_samples):
        end = min(start + window_samples, total_samples)
        chunk = audio[start:end]

        if len(chunk) < sr // 10:
            continue

        start_sec = start / sr
        end_sec = end / sr

        # Clipping burst: >1% of samples above 0.99 in this window
        clip_count = int(np.sum(np.abs(chunk) > 0.99))
        clip_ratio = clip_count / len(chunk)
        if clip_ratio > 0.01:
            artifacts.append(ArtifactWindow(
                start_sec=start_sec,
                end_sec=end_sec,
                issue="clipping_burst",
                measured_value=clip_ratio,
            ))

        # HF spike: window HF energy > 2.5x the global average
        if global_hf_energy > 1e-12:
            stft_chunk = librosa.stft(chunk, n_fft=2048, hop_length=512)
            freqs_chunk = librosa.fft_frequencies(sr=sr, n_fft=2048)
            hf_mask_chunk = (freqs_chunk >= 6000) & (freqs_chunk <= 10000)
            chunk_hf_energy = float(np.mean(np.abs(stft_chunk[hf_mask_chunk, :]) ** 2))
            ratio = chunk_hf_energy / global_hf_energy
            if ratio > 2.5:
                artifacts.append(ArtifactWindow(
                    start_sec=start_sec,
                    end_sec=end_sec,
                    issue="hf_spike",
                    measured_value=ratio,
                ))

    return artifacts


def print_artifacts(artifacts: list[ArtifactWindow]) -> None:
    """Print artifact scan results to stdout."""
    if not artifacts:
        print("  No localized artifacts detected.")
        return
    for a in artifacts:
        if a.issue == "clipping_burst":
            detail = f"{a.measured_value * 100:.1f}% clipped samples"
        else:
            detail = f"{a.measured_value:.1f}x HF energy vs average"
        print(f"  [{a.start_sec:.1f}s - {a.end_sec:.1f}s] {a.issue}: {detail}")


def print_profile(profile: VocalProfile) -> None:
    """Print a VocalProfile to stdout in a human-readable format."""
    print()
    print(f"  Vocal Profile: {profile.file_path}")
    print(f"  Duration: {profile.duration_seconds:.1f}s | SR: {profile.sample_rate}Hz")
    print(f"  Quality Score: {profile.overall_quality_score:.0f}/100")
    print()

    severity_labels = {
        Severity.NONE: "OK",
        Severity.MILD: "Mild",
        Severity.MODERATE: "Moderate",
        Severity.SEVERE: "Severe",
    }

    for d in profile.diagnoses:
        label = severity_labels.get(d.severity, str(d.severity))
        freq_info = ""
        if d.detected_frequency_hz is not None:
            freq_info = f" @ {d.detected_frequency_hz:.0f}Hz"
        print(f"  [{label:>8}] {d.category}{freq_info}")
        if d.recommendation:
            print(f"             {d.recommendation}")

    if profile.warnings:
        print()
        print("  Warnings:")
        for w in profile.warnings:
            print(f"    - {w}")
    print()
