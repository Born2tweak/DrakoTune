"""Tests for DrakoTune Alpha pipeline.

Generates synthetic test audio (harsh sine wave with noise)
and validates the full pipeline produces valid output.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from src.dsp.diagnose import diagnose
from src.dsp.export import export_before_after
from src.dsp.pipeline import (
    CleanupParams,
    apply_alpha22_refinement,
    build_adaptive_chain,
    build_cleanup_chain,
    process_audio,
)
from src.dsp.preprocess import preprocess


SAMPLE_RATE = 44100
DURATION_SECONDS = 3.0


def _generate_harsh_vocal(path: str, sample_rate: int = SAMPLE_RATE) -> None:
    """Generate a synthetic harsh vocal-like signal for testing.

    Creates a signal with:
    - Fundamental at 200Hz (vocal range)
    - Harsh upper harmonics at 3.5kHz and 6.5kHz
    - Background noise
    - Some clipping
    """
    t = np.linspace(0, DURATION_SECONDS, int(sample_rate * DURATION_SECONDS), dtype=np.float32)

    # Fundamental vocal frequency
    signal = 0.4 * np.sin(2 * np.pi * 200 * t)

    # Harsh upper harmonics (the frequencies we want the chain to tame)
    signal += 0.3 * np.sin(2 * np.pi * 3500 * t)
    signal += 0.2 * np.sin(2 * np.pi * 6500 * t)

    # Background noise
    rng = np.random.default_rng(42)
    signal += 0.05 * rng.standard_normal(len(t)).astype(np.float32)

    # Simulate some clipping
    signal = np.clip(signal, -0.9, 0.9)

    sf.write(path, signal, sample_rate, subtype="PCM_16")


@pytest.fixture
def harsh_wav(tmp_path: Path) -> Path:
    """Create a temporary harsh vocal WAV for testing."""
    wav_path = tmp_path / "harsh_vocal.wav"
    _generate_harsh_vocal(str(wav_path))
    return wav_path


class TestPreprocess:
    def test_normalizes_wav(self, harsh_wav: Path, tmp_path: Path) -> None:
        output = tmp_path / "normalized.wav"
        result = preprocess(harsh_wav, output)

        assert result.exists()

        info = sf.info(str(result))
        assert info.samplerate == 44100
        assert info.channels == 1
        assert info.subtype == "PCM_16"

    def test_missing_input_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            preprocess(tmp_path / "nonexistent.wav", tmp_path / "out.wav")


class TestPipeline:
    def test_build_cleanup_chain_returns_pedalboard(self) -> None:
        from pedalboard import Pedalboard

        board = build_cleanup_chain()
        assert isinstance(board, Pedalboard)
        assert len(board) == 6  # highpass, 2x EQ, compressor, gate, gain

    def test_process_audio_produces_valid_output(self, harsh_wav: Path, tmp_path: Path) -> None:
        # First preprocess to get normalized input
        normalized = tmp_path / "normalized.wav"
        preprocess(harsh_wav, normalized)

        processed = tmp_path / "processed.wav"
        result = process_audio(str(normalized), str(processed))

        assert Path(result["output_path"]).exists()
        assert result["sample_rate"] == SAMPLE_RATE
        assert result["duration_seconds"] > 0
        assert result["total_samples"] > 0

        # Verify output is valid audio
        audio, sr = sf.read(str(processed))
        assert sr == SAMPLE_RATE
        assert len(audio) > 0
        assert np.all(np.isfinite(audio))
        assert np.max(np.abs(audio)) <= 1.0

    def test_processed_audio_has_reduced_harshness(
        self, harsh_wav: Path, tmp_path: Path
    ) -> None:
        """Verify the DSP chain actually reduces energy in the harsh frequency band."""
        normalized = tmp_path / "normalized.wav"
        preprocess(harsh_wav, normalized)

        processed_path = tmp_path / "processed.wav"
        process_audio(str(normalized), str(processed_path))

        original, sr = sf.read(str(normalized), dtype="float32")
        processed, _ = sf.read(str(processed_path), dtype="float32")

        # Compute FFT energy in the harsh band (2-8kHz)
        def harsh_band_energy(audio: np.ndarray, sample_rate: int) -> float:
            fft = np.fft.rfft(audio)
            freqs = np.fft.rfftfreq(len(audio), 1.0 / sample_rate)
            mask = (freqs >= 2000) & (freqs <= 8000)
            return float(np.sum(np.abs(fft[mask]) ** 2))

        original_harsh = harsh_band_energy(original, sr)
        processed_harsh = harsh_band_energy(processed, sr)

        # Processed should have less energy in the harsh band
        assert processed_harsh < original_harsh, (
            f"Processed harsh energy ({processed_harsh:.0f}) should be less than "
            f"original ({original_harsh:.0f})"
        )

    def test_process_audio_emits_versioned_record(self, harsh_wav: Path, tmp_path: Path) -> None:
        from src.shared_types import SCHEMA_VERSION, ProcessingRecord

        normalized = tmp_path / "normalized.wav"
        preprocess(harsh_wav, normalized)

        processed = tmp_path / "processed.wav"
        profile = diagnose(str(normalized))
        result = process_audio(str(normalized), str(processed), profile=profile)

        # Version metadata is present.
        assert result["schema_version"] == SCHEMA_VERSION
        assert result["analyzer_version"]
        assert result["policy_version"]

        # The processing record is serialized and reconstructable.
        rec_dict = result["processing_record"]
        assert rec_dict["schema_version"] == SCHEMA_VERSION
        record = ProcessingRecord.from_dict(rec_dict)
        assert record.asset.sample_rate == SAMPLE_RATE
        assert record.diagnostics is not None
        assert len(record.diagnostics.observations) >= 1
        assert len(record.plan.actions) >= 1

    def test_custom_params(self, harsh_wav: Path, tmp_path: Path) -> None:
        normalized = tmp_path / "normalized.wav"
        preprocess(harsh_wav, normalized)

        processed = tmp_path / "processed.wav"
        custom = CleanupParams(
            highpass_hz=100.0,
            harsh_gain_db=-6.0,
            comp_ratio=4.0,
        )
        result = process_audio(str(normalized), str(processed), params=custom)
        assert Path(result["output_path"]).exists()

    def test_pipeline_completes_within_time_limit(
        self, harsh_wav: Path, tmp_path: Path
    ) -> None:
        """Pipeline should complete in under 30 seconds for a ~3s test file."""
        import time

        normalized = tmp_path / "normalized.wav"
        preprocess(harsh_wav, normalized)

        processed = tmp_path / "processed.wav"
        start = time.time()
        process_audio(str(normalized), str(processed))
        elapsed = time.time() - start

        # 3 seconds of audio should process very fast (well under 30s limit)
        assert elapsed < 10.0, f"Pipeline took {elapsed:.1f}s — too slow"

    def test_adaptive_chain_description_stays_light(self, harsh_wav: Path, tmp_path: Path) -> None:
        normalized = tmp_path / "normalized.wav"
        preprocess(harsh_wav, normalized)

        profile = diagnose(str(normalized))
        board = build_adaptive_chain(profile)
        chain = getattr(board, "_chain_description")

        assert all("harsh sweep" not in step for step in chain)
        assert all("painful highs cut" not in step for step in chain)
        assert any("limiter(-1.2dB)" == step for step in chain)

    def test_alpha22_refinement_reduces_peak_without_overcutting(self) -> None:
        t = np.linspace(0, 1.0, SAMPLE_RATE, dtype=np.float32, endpoint=False)
        signal = 0.45 * np.sin(2 * np.pi * 180 * t)
        signal += 0.20 * np.sin(2 * np.pi * 1200 * t)
        signal += 0.16 * np.sin(2 * np.pi * 6400 * t)
        signal[6000:6400] += 0.45
        signal[20000:20512] += 0.30 * np.sin(2 * np.pi * 7200 * t[:512])
        signal = np.clip(signal, -1.0, 1.0).reshape(-1, 1)

        refined, steps = apply_alpha22_refinement(signal, SAMPLE_RATE)

        assert refined.shape == signal.shape
        assert np.max(np.abs(refined)) <= np.max(np.abs(signal))
        assert np.sqrt(np.mean(refined**2)) > np.sqrt(np.mean(signal**2)) * 0.75
        assert steps


class TestExport:
    def test_export_creates_before_after(self, harsh_wav: Path, tmp_path: Path) -> None:
        normalized = tmp_path / "normalized.wav"
        preprocess(harsh_wav, normalized)

        processed = tmp_path / "processed.wav"
        process_audio(str(normalized), str(processed))

        output_dir = tmp_path / "export"
        result = export_before_after(normalized, processed, output_dir, "test_vocal")

        assert Path(result["before"]).exists()
        assert Path(result["after"]).exists()
        assert "test_vocal_before.wav" in result["before"]
        assert "test_vocal_after.wav" in result["after"]

    def test_export_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            export_before_after(
                tmp_path / "nope.wav",
                tmp_path / "also_nope.wav",
                tmp_path / "out",
            )
