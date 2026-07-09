"""Loudness and dynamics diagnostics (M05).

Deterministic full-file and frame-based measurements: RMS loudness, crest
factor, dynamic range, and loudness consistency. Emitted as canonical
Observations with explicit `window` ("full" vs "frame") and confidence that
degrades when there is too little voiced material to measure reliably.

LUFS: gated BS.1770-4 integrated loudness is provided via pyloudnorm (M18). It
is emitted as `integrated_lufs` when measurable; for signals shorter than one
400ms block, silence, or if the library is unavailable, the value is marked
unavailable (confidence 0, `lufs_unavailable` flag) rather than faked. `rms_dbfs`
is retained as a simple secondary measure.

Silence handling: frames quieter than SILENCE_FRAME_DBFS are excluded from
voiced dynamics stats. If fewer than MIN_VOICED_FRAMES remain, dynamics
observations are marked low-confidence and the `insufficient_voiced_content`
flag is set. This is documented policy, versioned via LOUDNESS_ANALYZER_VERSION.
"""

import math

import librosa
import numpy as np
import soundfile as sf

try:  # BS.1770 integrated loudness (M18). Optional so the core imports without it.
    import pyloudnorm as _pyln
    _HAS_PYLN = True
except Exception:  # noqa: BLE001
    _HAS_PYLN = False

from src.shared_types import DiagnosticResult, Observation, band_from_confidence

LOUDNESS_ANALYZER_VERSION = "1.1.0"

RMS_FRAME_LENGTH = 2048
RMS_HOP_LENGTH = 512
SILENCE_FRAME_DBFS = -60.0
MIN_VOICED_FRAMES = 5          # below this, dynamics stats are unreliable
CONFIDENT_VOICED_FRAMES = 20   # at/above this, full confidence in dynamics
LUFS_MIN_SECONDS = 0.4         # BS.1770 needs at least one 400ms block


def _integrated_lufs(mono: np.ndarray, sample_rate: int) -> float | None:
    """Gated BS.1770 integrated loudness, or None if not measurable."""
    if not _HAS_PYLN or mono.shape[0] < int(LUFS_MIN_SECONDS * sample_rate):
        return None
    try:
        value = _pyln.Meter(sample_rate).integrated_loudness(mono.astype(np.float64))
    except Exception:  # noqa: BLE001 - pyloudnorm raises on too-short/degenerate input
        return None
    return float(value) if math.isfinite(value) else None


def _dbfs(linear: float) -> float:
    return 20.0 * math.log10(linear + 1e-12)


def _to_mono(audio: np.ndarray) -> np.ndarray:
    return audio.astype(np.float32) if audio.ndim == 1 else audio[:, 0].astype(np.float32)


def _dynamics_confidence(voiced_count: int) -> float:
    if voiced_count >= CONFIDENT_VOICED_FRAMES:
        return 0.9
    if voiced_count >= MIN_VOICED_FRAMES:
        return 0.6
    return 0.3


def measure_loudness(audio: np.ndarray, sample_rate: int) -> tuple[list[Observation], list[str], dict]:
    """Return (observations, flags, measurement_context) for one signal."""
    mono = _to_mono(audio)
    total = int(mono.shape[0])

    if total == 0:
        return (
            [Observation(id="loudness.rms_dbfs", metric="rms_dbfs", value=-120.0,
                         units="dBFS", confidence=0.3, evidence="empty signal")],
            ["insufficient_voiced_content"],
            {"analyzer_version": LOUDNESS_ANALYZER_VERSION, "voiced_frames": 0},
        )

    full_rms = float(np.sqrt(np.mean(mono**2)))
    rms_dbfs = _dbfs(full_rms)
    peak_dbfs = _dbfs(float(np.max(np.abs(mono))))
    crest_factor_db = peak_dbfs - rms_dbfs

    frame_rms = librosa.feature.rms(y=mono, frame_length=RMS_FRAME_LENGTH, hop_length=RMS_HOP_LENGTH)[0]
    frame_dbfs = 20.0 * np.log10(frame_rms + 1e-12)
    voiced_mask = frame_dbfs > SILENCE_FRAME_DBFS
    voiced_rms = frame_rms[voiced_mask]
    voiced_dbfs = frame_dbfs[voiced_mask]
    voiced_count = int(voiced_rms.size)

    if voiced_count >= 2:
        dynamic_range_db = float(np.percentile(voiced_dbfs, 95) - np.percentile(voiced_dbfs, 5))
        consistency_cv = float(np.std(voiced_rms) / (np.mean(voiced_rms) + 1e-12))
    else:
        dynamic_range_db = 0.0
        consistency_cv = 0.0

    dyn_conf = _dynamics_confidence(voiced_count)
    band = band_from_confidence(dyn_conf).value

    lufs = _integrated_lufs(mono, sample_rate)

    observations = [
        Observation(id="loudness.integrated_lufs", metric="integrated_lufs",
                    value=lufs if lufs is not None else -120.0, units="LUFS", window="full",
                    confidence=0.9 if lufs is not None else 0.0,
                    evidence="BS.1770 gated" if lufs is not None else "unavailable (short/silent/no lib)"),
        Observation(id="loudness.rms_dbfs", metric="rms_dbfs", value=rms_dbfs,
                    units="dBFS", window="full", confidence=1.0, evidence="full-file RMS"),
        Observation(id="loudness.crest_factor_db", metric="crest_factor_db", value=crest_factor_db,
                    units="dB", window="full", confidence=1.0, evidence="peak_dbfs - rms_dbfs"),
        Observation(id="loudness.dynamic_range_db", metric="dynamic_range_db", value=dynamic_range_db,
                    units="dB", window="frame", confidence=dyn_conf,
                    evidence=f"p95-p5 of {voiced_count} voiced frames, band={band}"),
        Observation(id="loudness.consistency_cv", metric="consistency_cv", value=consistency_cv,
                    units="ratio", window="frame", confidence=dyn_conf,
                    evidence=f"std/mean of {voiced_count} voiced frames, band={band}"),
    ]

    flags: list[str] = []
    if voiced_count < MIN_VOICED_FRAMES:
        flags.append("insufficient_voiced_content")
    if lufs is None:
        flags.append("lufs_unavailable")

    context = {
        "analyzer_version": LOUDNESS_ANALYZER_VERSION,
        "sample_rate": int(sample_rate),
        "rms_frame_length": RMS_FRAME_LENGTH,
        "rms_hop_length": RMS_HOP_LENGTH,
        "silence_frame_dbfs": SILENCE_FRAME_DBFS,
        "voiced_frames": voiced_count,
        "total_frames": int(frame_rms.size),
        "lufs_implemented": _HAS_PYLN,
        "lufs_standard": "BS.1770-4 (pyloudnorm)",
    }
    return observations, flags, context


def diagnose_loudness(audio_path: str, asset_id: str = "unknown") -> DiagnosticResult:
    """Read a WAV and produce a loudness/dynamics DiagnosticResult."""
    audio, sample_rate = sf.read(audio_path, dtype="float32")
    observations, flags, context = measure_loudness(audio, int(sample_rate))
    return DiagnosticResult(
        id=f"loudness:{asset_id}",
        audio_asset_id=asset_id,
        analyzer_version=LOUDNESS_ANALYZER_VERSION,
        measurement_context=context,
        observations=tuple(observations),
        integrity_flags=tuple(flags),
    )
