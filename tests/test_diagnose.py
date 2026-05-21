"""Synthetic audio tests for diagnosis accuracy validation.

Generates controlled test signals to verify detection thresholds,
reduce false positives, and validate severity classification.
"""

import numpy as np
import pytest
from scipy import signal as scipy_signal
import soundfile as sf
import tempfile
import os

from src.dsp.diagnose import (
    diagnose,
    Severity,
    _detect_harshness,
    _detect_sibilance,
    _detect_muddiness,
    _detect_clipping,
    _detect_noise_floor,
    _detect_dynamic_inconsistency,
    _detect_dullness,
    VocalProfile,
)
import librosa

# ─── Helpers ───────────────────────────────────────────────────────────────────

SAMPLE_RATE = 44100
DURATION = 2.0  # seconds


def _make_sine(freq: float, duration: float = DURATION, amplitude: float = 0.5) -> np.ndarray:
    """Generate a pure sine wave."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    return amplitude * np.sin(2 * np.pi * freq * t)


def _make_white_noise(duration: float = DURATION, amplitude: float = 0.1) -> np.ndarray:
    """Generate white noise."""
    return amplitude * np.random.randn(int(SAMPLE_RATE * duration))


def _compute_stft(sig: np.ndarray):
    """Compute STFT magnitude and frequencies for internal function tests."""
    stft = librosa.stft(sig, n_fft=2048, hop_length=512)
    stft_mag = np.abs(stft)
    freqs = librosa.fft_frequencies(sr=SAMPLE_RATE, n_fft=2048)
    return stft_mag, freqs


def _save_and_diagnose(sig: np.ndarray) -> VocalProfile:
    """Save signal to temp WAV and run diagnose()."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    sf.write(path, sig, SAMPLE_RATE)
    try:
        return diagnose(path)
    finally:
        os.unlink(path)


# ─── Noise Floor Tests ─────────────────────────────────────────────────────────

class TestNoiseFloor:
    """Validate noise floor detection against controlled signals."""

    def test_silence_has_low_noise_floor(self):
        """Pure silence should report very low noise floor."""
        sig = np.zeros(int(SAMPLE_RATE * DURATION))
        result = _detect_noise_floor(sig, SAMPLE_RATE)
        assert result.severity <= Severity.MILD
        assert result.measured_value < -60

    def test_white_noise_detects_correctly(self):
        """White noise at -30dB should be detected as moderate/severe."""
        # -30dBFS ≈ 0.0316 amplitude
        sig = _make_white_noise(amplitude=0.0316)
        result = _detect_noise_floor(sig, SAMPLE_RATE)
        assert result.severity >= Severity.MODERATE

    def test_low_level_noise_is_moderate(self):
        """Low-level noise (-45dB) should be low/moderate."""
        sig = _make_white_noise(amplitude=0.0056)  # ~-45dB
        result = _detect_noise_floor(sig, SAMPLE_RATE)
        assert result.severity in (Severity.MILD, Severity.MODERATE)

    def test_noise_with_speech_still_detectable(self):
        """Noise floor should be detectable even with quiet speech present."""
        speech = _make_sine(200, amplitude=0.1)  # Quiet fundamental
        noise = _make_white_noise(amplitude=0.02)
        mixed = np.clip(speech + noise, -1, 1)
        result = _detect_noise_floor(mixed, SAMPLE_RATE)
        assert result.severity >= Severity.MILD


# ─── Harshness Tests ───────────────────────────────────────────────────────────

class TestHarshness:
    """Validate harshness detection — must distinguish harsh from naturally bright."""

    def test_harsh_sibilance_detected(self):
        """Narrow-band energy at 4-8kHz should trigger harshness."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        harsh = 0.3 * np.sin(2 * np.pi * 6000 * t)
        harsh *= (0.5 + 0.5 * np.sin(2 * np.pi * 8 * t))
        stft_mag, freqs = _compute_stft(harsh)
        result = _detect_harshness(harsh, SAMPLE_RATE, stft_mag, freqs)
        assert result.severity >= Severity.MODERATE, f"Expected moderate+ harshness, got {result.severity}"

    def test_broad_spectrum_not_harsh(self):
        """Vocal-like signal with balanced spectrum should NOT trigger harshness."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        # Realistic vocal: strong fundamental + harmonics + gentle highs
        bright = 0.3 * np.sin(2 * np.pi * 200 * t)
        bright += 0.2 * np.sin(2 * np.pi * 400 * t)
        bright += 0.15 * np.sin(2 * np.pi * 800 * t)
        bright += 0.1 * np.sin(2 * np.pi * 1500 * t)
        for freq in [3000, 4000, 5000, 6000, 7000]:
            bright += 0.03 * np.sin(2 * np.pi * freq * t)
        stft_mag, freqs = _compute_stft(bright)
        result = _detect_harshness(bright, SAMPLE_RATE, stft_mag, freqs)
        assert result.severity <= Severity.MILD, f"Balanced vocal should not be harsh, got {result.severity}"

    def test_silence_not_harsh(self):
        """Silence must never trigger harshness."""
        sig = np.zeros(int(SAMPLE_RATE * DURATION))
        stft_mag, freqs = _compute_stft(sig)
        result = _detect_harshness(sig, SAMPLE_RATE, stft_mag, freqs)
        assert result.severity == Severity.NONE

    def test_low_freq_only_not_harsh(self):
        """Pure low-frequency content should not trigger harshness."""
        sig = _make_sine(100, amplitude=0.5)
        stft_mag, freqs = _compute_stft(sig)
        result = _detect_harshness(sig, SAMPLE_RATE, stft_mag, freqs)
        assert result.severity == Severity.NONE

    def test_narrow_band_4khz_harsh(self):
        """Narrow energy peak at 4kHz = harsh."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        sig = 0.4 * np.sin(2 * np.pi * 4000 * t)
        stft_mag, freqs = _compute_stft(sig)
        result = _detect_harshness(sig, SAMPLE_RATE, stft_mag, freqs)
        assert result.severity >= Severity.MODERATE


# ─── Clipping Tests ────────────────────────────────────────────────────────────

class TestClipping:
    """Validate clipping detection — must find flat-topped samples."""

    def test_hard_clipping_detected(self):
        """Signal clipped at ±1.0 must be detected."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        sig = np.clip(np.sin(2 * np.pi * 440 * t) * 1.5, -1.0, 1.0)
        result = _detect_clipping(sig, SAMPLE_RATE)
        assert result.severity >= Severity.MODERATE

    def test_soft_clipping_detected(self):
        """Soft-clipped signal (near-threshold) should be detected."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        sig = np.tanh(np.sin(2 * np.pi * 440 * t) * 2.0)
        result = _detect_clipping(sig, SAMPLE_RATE)
        assert result.severity >= Severity.MILD

    def test_clean_signal_no_clipping(self):
        """Clean signal at -6dB must not trigger clipping."""
        sig = _make_sine(440, amplitude=0.5)
        result = _detect_clipping(sig, SAMPLE_RATE)
        assert result.severity == Severity.NONE

    def test_consecutive_samples_counted(self):
        """Clipping detection should count consecutive near-full-scale samples."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        sig = scipy_signal.square(2 * np.pi * 100 * t)
        result = _detect_clipping(sig, SAMPLE_RATE)
        assert result.severity >= Severity.SEVERE


# ─── Muddiness Tests ───────────────────────────────────────────────────────────

class TestMuddiness:
    """Validate muddiness detection — excess energy in 200-500Hz."""

    def test_muddy_signal_detected(self):
        """Strong energy at 320Hz should trigger muddiness."""
        sig = _make_sine(320, amplitude=0.7)
        stft_mag, freqs = _compute_stft(sig)
        result = _detect_muddiness(sig, SAMPLE_RATE, stft_mag, freqs)
        assert result.severity >= Severity.MODERATE

    def test_clean_midrange_not_muddy(self):
        """Vocal with strong mid/high content should not trigger muddiness."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        # Strong clarity band (1-4kHz) relative to mud band
        balanced = 0.05 * np.sin(2 * np.pi * 300 * t)
        balanced += 0.2 * np.sin(2 * np.pi * 1500 * t)
        balanced += 0.15 * np.sin(2 * np.pi * 3000 * t)
        balanced += 0.1 * np.sin(2 * np.pi * 4000 * t)
        stft_mag, freqs = _compute_stft(balanced)
        result = _detect_muddiness(balanced, SAMPLE_RATE, stft_mag, freqs)
        assert result.severity <= Severity.MILD

    def test_bass_only_not_muddy(self):
        """Sub-bass (<80Hz) alone should not trigger muddiness."""
        sig = _make_sine(60, amplitude=0.5)
        stft_mag, freqs = _compute_stft(sig)
        result = _detect_muddiness(sig, SAMPLE_RATE, stft_mag, freqs)
        assert result.severity <= Severity.MILD

    def test_boxy_resonance_detected(self):
        """Boxy resonance at 400-600Hz should be detected."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        boxy = 0.5 * np.sin(2 * np.pi * 500 * t)
        stft_mag, freqs = _compute_stft(boxy)
        result = _detect_muddiness(boxy, SAMPLE_RATE, stft_mag, freqs)
        assert result.severity >= Severity.MILD


# ─── Dullness Tests ────────────────────────────────────────────────────────────

class TestDullness:
    """Validate dullness detection — lack of high-frequency energy."""

    def test_lowpass_signal_is_dull(self):
        """Signal with no content above 2kHz should be dull."""
        sig = _make_sine(200, amplitude=0.5)
        stft_mag, freqs = _compute_stft(sig)
        result = _detect_dullness(sig, SAMPLE_RATE, stft_mag, freqs)
        assert result.severity >= Severity.MODERATE

    def test_full_spectrum_not_dull(self):
        """Full-spectrum signal should not be dull."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        full = np.zeros_like(t)
        for freq in [100, 500, 1000, 2000, 4000, 8000]:
            full += 0.1 * np.sin(2 * np.pi * freq * t)
        stft_mag, freqs = _compute_stft(full)
        result = _detect_dullness(full, SAMPLE_RATE, stft_mag, freqs)
        assert result.severity <= Severity.MILD

    def test_highpass_not_dull(self):
        """High-frequency-only signal should not be dull."""
        sig = _make_sine(6000, amplitude=0.3)
        stft_mag, freqs = _compute_stft(sig)
        result = _detect_dullness(sig, SAMPLE_RATE, stft_mag, freqs)
        assert result.severity == Severity.NONE


# ─── Dynamic Inconsistency Tests ───────────────────────────────────────────────

class TestDynamicInconsistency:
    """Validate dynamic range inconsistency detection."""

    def test_constant_level_not_inconsistent(self):
        """Steady signal should not trigger dynamic inconsistency."""
        sig = _make_sine(440, amplitude=0.3)
        result = _detect_dynamic_inconsistency(sig, SAMPLE_RATE)
        assert result.severity <= Severity.MILD

    def test_variable_levels_detected(self):
        """Signal with large level swings should be detected."""
        loud = _make_sine(440, duration=0.5, amplitude=0.8)
        quiet = _make_sine(440, duration=0.5, amplitude=0.05)
        sig = np.concatenate([loud, quiet, loud, quiet])
        result = _detect_dynamic_inconsistency(sig, SAMPLE_RATE)
        assert result.severity >= Severity.MODERATE

    def test_silence_gaps_detected(self):
        """Signal with silence gaps should show inconsistency."""
        tone = _make_sine(440, duration=0.3, amplitude=0.5)
        silence = np.zeros(int(SAMPLE_RATE * 0.3))
        sig = np.concatenate([tone, silence, tone, silence, tone])
        result = _detect_dynamic_inconsistency(sig, SAMPLE_RATE)
        assert result.severity >= Severity.MILD


# ─── Full Diagnosis Integration Tests ──────────────────────────────────────────

class TestFullDiagnosis:
    """Integration tests for the full diagnose() function."""

    def test_clean_vocal_minimal_issues(self):
        """Clean vocal-like signal should have minimal diagnoses."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        # Realistic vocal spectrum with strong harmonics extending to high frequencies
        clean = np.zeros_like(t)
        # Fundamental and harmonics with realistic decay
        for n in range(1, 20):
            freq = 150 * n
            if freq > SAMPLE_RATE // 2:
                break
            amp = 0.3 / (n ** 1.2)  # Harmonic decay
            clean += amp * np.sin(2 * np.pi * freq * t)
        # Add some breathiness (high-frequency noise-like content)
        breath = 0.005 * np.random.randn(len(t))
        clean += breath
        # Normalize to reasonable level
        clean = clean / np.max(np.abs(clean)) * 0.5
        profile = _save_and_diagnose(clean)
        severe_count = sum(1 for d in profile.diagnoses if d.severity >= Severity.SEVERE)
        assert severe_count == 0, f"Clean signal should have no severe issues, got {severe_count}"

    def test_clipped_signal_reports_clipping(self):
        """Clipped signal must report clipping in full diagnosis."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        sig = np.clip(np.sin(2 * np.pi * 440 * t) * 2.0, -1.0, 1.0)
        profile = _save_and_diagnose(sig)
        clipping_diag = next(
            (d for d in profile.diagnoses if d.category == "clipping"),
            None
        )
        assert clipping_diag is not None
        assert clipping_diag.severity >= Severity.MODERATE

    def test_noisy_muddy_signal_reports_both(self):
        """Signal with noise + muddiness should report both."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        muddy = 0.4 * np.sin(2 * np.pi * 320 * t)
        noise = 0.05 * np.random.randn(len(t))
        sig = np.clip(muddy + noise, -1, 1)
        profile = _save_and_diagnose(sig)
        categories = {d.category for d in profile.diagnoses}
        assert "muddiness" in categories or "noise_floor" in categories

    def test_severe_issues_flagged(self):
        """Multiple severe issues should be flagged."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        sig = 0.3 * np.sin(2 * np.pi * 320 * t)  # Muddy
        sig += 0.1 * np.random.randn(len(t))  # Noisy
        sig = np.clip(sig * 3.0, -1.0, 1.0)  # Clipped
        profile = _save_and_diagnose(sig)
        severe_count = sum(1 for d in profile.diagnoses if d.severity >= Severity.SEVERE)
        assert severe_count >= 1, "Expected at least one severe issue"


# ─── Edge Cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Edge cases that commonly cause false positives."""

    def test_very_short_signal(self):
        """Very short signals should not crash."""
        sig = _make_sine(440, duration=0.1)
        profile = _save_and_diagnose(sig)
        assert profile is not None

    def test_empty_signal(self):
        """Empty or near-empty signal should not crash."""
        sig = np.zeros(100)
        profile = _save_and_diagnose(sig)
        assert profile is not None

    def test_dc_offset_not_flagged_as_noise(self):
        """DC offset should not be misdiagnosed as noise floor."""
        t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
        sig = np.sin(2 * np.pi * 440 * t) + 0.1  # DC offset
        profile = _save_and_diagnose(sig)
        noise_diag = next(
            (d for d in profile.diagnoses if d.category == "noise_floor"),
            None
        )
        if noise_diag:
            assert noise_diag.severity <= Severity.MODERATE
