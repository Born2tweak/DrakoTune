"""Technical-safety diagnostics (M04).

Deterministic measurements that gate safe processing: peak, approximate true
peak, headroom, DC offset, clipping ratio, duration, and silence percentage.

These are *measurements only* — they emit canonical Observations and integrity
flags, never DSP actions or interpretations (that separation is the whole point
of the layered architecture). Clipping is measured independently of peak level:
a hot-but-clean signal has a high peak and near-zero clipping ratio.

Analyzer settings (thresholds, frame sizes, oversample factor) are stored in the
DiagnosticResult.measurement_context so results can be pinned and compared.
"""

import math

import librosa
import numpy as np
import soundfile as sf

from src.shared_types import DiagnosticResult, Observation

SAFETY_ANALYZER_VERSION = "1.0.0"

# --- Named policy settings (versioned; change deliberately) ---
TRUE_PEAK_OVERSAMPLE = 4       # 4x band-limited upsample for inter-sample peaks
RMS_FRAME_LENGTH = 2048
RMS_HOP_LENGTH = 512
SILENCE_FRAME_DBFS = -60.0     # frames quieter than this count as silent

# --- Integrity-flag thresholds ---
CLIP_FLAG_RATIO = 0.001        # >=0.1% full-scale samples -> clipping flag
DC_FLAG_ABS = 0.01             # |mean| above this -> dc_offset flag
HEADROOM_MIN_DB = 1.0          # true-peak headroom below this -> no_headroom flag
MOSTLY_SILENT_PCT = 90.0       # more silent than this -> mostly_silent flag

_FULL_SCALE = 0.999            # sample magnitude counted as clipped


def _dbfs(linear: float) -> float:
    return 20.0 * math.log10(linear + 1e-12)


def _to_mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio.astype(np.float32)
    return audio[:, 0].astype(np.float32)


def measure_safety(audio: np.ndarray, sample_rate: int) -> tuple[list[Observation], list[str], dict]:
    """Return (observations, integrity_flags, measurement_context) for one signal."""
    mono = _to_mono(audio)
    total = int(mono.shape[0])

    if total == 0:
        obs = [Observation(id="safety.duration_seconds", metric="duration_seconds",
                            value=0.0, units="s", confidence=1.0, evidence="empty signal")]
        return obs, ["empty_audio"], {"analyzer_version": SAFETY_ANALYZER_VERSION, "sample_rate": int(sample_rate)}

    peak = float(np.max(np.abs(mono)))
    peak_dbfs = _dbfs(peak)

    # Approximate true peak via band-limited oversampling.
    try:
        upsampled = librosa.resample(
            mono, orig_sr=sample_rate, target_sr=sample_rate * TRUE_PEAK_OVERSAMPLE
        )
        true_peak = float(np.max(np.abs(upsampled)))
    except Exception:  # noqa: BLE001 - fall back to sample peak if resample fails
        true_peak = peak
    true_peak_dbtp = _dbfs(true_peak)
    headroom_db = -true_peak_dbtp

    dc_offset = float(np.mean(mono))
    clipping_ratio = float(np.mean(np.abs(mono) >= _FULL_SCALE))
    duration_seconds = total / sample_rate if sample_rate else 0.0

    rms = librosa.feature.rms(y=mono, frame_length=RMS_FRAME_LENGTH, hop_length=RMS_HOP_LENGTH)[0]
    rms_dbfs = 20.0 * np.log10(rms + 1e-12)
    silence_percentage = float(np.mean(rms_dbfs < SILENCE_FRAME_DBFS) * 100.0)

    observations = [
        Observation(id="safety.peak_dbfs", metric="peak_dbfs", value=peak_dbfs,
                    units="dBFS", confidence=1.0, evidence=f"peak={peak:.4f}"),
        Observation(id="safety.true_peak_dbtp", metric="true_peak_dbtp", value=true_peak_dbtp,
                    units="dBTP", confidence=0.9, evidence=f"{TRUE_PEAK_OVERSAMPLE}x oversample"),
        Observation(id="safety.headroom_db", metric="headroom_db", value=headroom_db,
                    units="dB", confidence=0.9, evidence="margin to 0 dBTP"),
        Observation(id="safety.dc_offset", metric="dc_offset", value=dc_offset,
                    units="linear", confidence=1.0, evidence="signal mean"),
        Observation(id="safety.clipping_ratio", metric="clipping_ratio", value=clipping_ratio,
                    units="ratio", confidence=1.0,
                    evidence=f"fraction of |x|>={_FULL_SCALE}"),
        Observation(id="safety.duration_seconds", metric="duration_seconds", value=duration_seconds,
                    units="s", confidence=1.0, evidence=f"{total} samples"),
        Observation(id="safety.silence_percentage", metric="silence_percentage",
                    value=silence_percentage, units="percent", confidence=0.9,
                    evidence=f"frames < {SILENCE_FRAME_DBFS} dBFS"),
    ]

    flags: list[str] = []
    if clipping_ratio >= CLIP_FLAG_RATIO:
        flags.append("clipping")
    if abs(dc_offset) > DC_FLAG_ABS:
        flags.append("dc_offset")
    if headroom_db < HEADROOM_MIN_DB:
        flags.append("no_headroom")
    if silence_percentage > MOSTLY_SILENT_PCT:
        flags.append("mostly_silent")

    context = {
        "analyzer_version": SAFETY_ANALYZER_VERSION,
        "sample_rate": int(sample_rate),
        "true_peak_oversample": TRUE_PEAK_OVERSAMPLE,
        "rms_frame_length": RMS_FRAME_LENGTH,
        "rms_hop_length": RMS_HOP_LENGTH,
        "silence_frame_dbfs": SILENCE_FRAME_DBFS,
        "thresholds": {
            "clip_flag_ratio": CLIP_FLAG_RATIO,
            "dc_flag_abs": DC_FLAG_ABS,
            "headroom_min_db": HEADROOM_MIN_DB,
            "mostly_silent_pct": MOSTLY_SILENT_PCT,
        },
    }
    return observations, flags, context


def diagnose_safety(audio_path: str, asset_id: str = "unknown") -> DiagnosticResult:
    """Read a WAV and produce a technical-safety DiagnosticResult."""
    audio, sample_rate = sf.read(audio_path, dtype="float32")
    observations, flags, context = measure_safety(audio, int(sample_rate))
    return DiagnosticResult(
        id=f"safety:{asset_id}",
        audio_asset_id=asset_id,
        analyzer_version=SAFETY_ANALYZER_VERSION,
        measurement_context=context,
        observations=tuple(observations),
        integrity_flags=tuple(flags),
    )
