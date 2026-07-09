"""Spectral and noise diagnostics with a clean observation/interpretation split (M06).

This module demonstrates the layered discipline the architecture requires:

  measure_spectral()   -> Observations only (measured band energies/ratios)
  interpret_spectral() -> Interpretations only (hypotheses citing observations)

Interpretations carry NO processing actions or recommendations — that is the
decision engine's job (M07/M08). A single elevated metric never yields a strong
claim: uncorroborated interpretations are capped at SINGLE_METRIC_CAP (MEDIUM
band). A second, independent observation must agree to raise confidence.

Band definitions are named and versioned (SPECTRAL_ANALYZER_VERSION); they are
stored in measurement_context so results can be pinned by fixtures.
"""

import math

import librosa
import numpy as np
import soundfile as sf

from src.shared_types import DiagnosticResult, Interpretation, Observation

SPECTRAL_ANALYZER_VERSION = "1.1.0"

# --- Named, versioned frequency bands (Hz) ---
BANDS = {
    "rumble": (20, 80),
    "mud": (200, 500),
    "clarity_ref": (1000, 4000),
    "low_ref": (200, 2000),
    "harshness": (2500, 6000),
    "sibilance": (5000, 8000),
    "mid_ref": (200, 4000),
    "air": (10000, 16000),
    "full": (20, 20000),
}

# --- Interpretation thresholds (ratio above which an issue is hypothesized) ---
RUMBLE_RATIO_MIN = 0.06
MUD_RATIO_MIN = 0.60
# Muddiness also requires a low spectral centroid: calibration (M17) showed the
# mud_ratio alone gives a 100% false-positive rate on clean harmonic voices
# (clean centroid ~925Hz, muddy ~413-456Hz). The centroid gate separates them.
MUD_CENTROID_MAX = 700.0
HARSHNESS_RATIO_MIN = 0.12
SIBILANCE_RATIO_MIN = 0.18
NOISE_FLOOR_DBFS_MIN = -50.0  # louder (less negative) than this -> noise hypothesis

# Confidence caps (Bible: single metrics do not produce strong quality claims).
SINGLE_METRIC_CAP = 0.6   # MEDIUM band ceiling for one supporting observation
CORROBORATED_CAP = 0.9    # ceiling once a second observation agrees

RMS_FRAME_LENGTH = 2048
RMS_HOP_LENGTH = 512


def _to_mono(audio: np.ndarray) -> np.ndarray:
    return audio.astype(np.float32) if audio.ndim == 1 else audio[:, 0].astype(np.float32)


def _band_energy(stft_mag: np.ndarray, freqs: np.ndarray, lo: float, hi: float) -> float:
    mask = (freqs >= lo) & (freqs <= hi)
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.sum(stft_mag[mask, :] ** 2, axis=1)))


def _ratio(num: float, den: float) -> float:
    return num / den if den > 1e-12 else 0.0


def _ratio_confidence(value: float, threshold: float, span: float, cap: float) -> float:
    """How strongly `value` exceeds `threshold`, scaled to [0, cap]."""
    return float(np.clip((value - threshold) / span, 0.0, 1.0) * cap)


def measure_spectral(audio: np.ndarray, sample_rate: int) -> tuple[list[Observation], dict]:
    """Measured spectral observations only — no interpretation."""
    mono = _to_mono(audio)
    if mono.shape[0] < RMS_FRAME_LENGTH:
        return [], {"analyzer_version": SPECTRAL_ANALYZER_VERSION, "reason": "signal_too_short"}

    stft_mag = np.abs(librosa.stft(mono, n_fft=2048, hop_length=RMS_HOP_LENGTH))
    freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=2048)

    e = {name: _band_energy(stft_mag, freqs, lo, hi) for name, (lo, hi) in BANDS.items()}

    rumble_ratio = _ratio(e["rumble"], e["full"])
    mud_ratio = _ratio(e["mud"], e["clarity_ref"])
    harshness_ratio = _ratio(e["harshness"], e["low_ref"])
    sibilance_ratio = _ratio(e["sibilance"], e["mid_ref"])
    air_ratio = _ratio(e["air"], e["mid_ref"])

    centroid_hz = float(np.mean(librosa.feature.spectral_centroid(y=mono, sr=sample_rate)[0]))

    frame_rms = librosa.feature.rms(y=mono, frame_length=RMS_FRAME_LENGTH, hop_length=RMS_HOP_LENGTH)[0]
    noise_floor_dbfs = 20.0 * math.log10(float(np.percentile(frame_rms, 5)) + 1e-12)

    observations = [
        Observation(id="spectral.rumble_ratio", metric="rumble_ratio", value=rumble_ratio,
                    units="ratio", confidence=1.0, evidence="E(20-80)/E(full)"),
        Observation(id="spectral.mud_ratio", metric="mud_ratio", value=mud_ratio,
                    units="ratio", confidence=1.0, evidence="E(200-500)/E(1k-4k)"),
        Observation(id="spectral.harshness_ratio", metric="harshness_ratio", value=harshness_ratio,
                    units="ratio", confidence=1.0, evidence="E(2.5k-6k)/E(200-2k)"),
        Observation(id="spectral.sibilance_ratio", metric="sibilance_ratio", value=sibilance_ratio,
                    units="ratio", confidence=1.0, evidence="E(5k-8k)/E(200-4k)"),
        Observation(id="spectral.air_ratio", metric="air_ratio", value=air_ratio,
                    units="ratio", confidence=1.0, evidence="E(10k-16k)/E(200-4k)"),
        Observation(id="spectral.centroid_hz", metric="centroid_hz", value=centroid_hz,
                    units="Hz", confidence=0.9, evidence="mean spectral centroid"),
        Observation(id="spectral.noise_floor_dbfs", metric="noise_floor_dbfs", value=noise_floor_dbfs,
                    units="dBFS", confidence=0.8, evidence="5th-percentile frame RMS"),
    ]
    context = {
        "analyzer_version": SPECTRAL_ANALYZER_VERSION,
        "sample_rate": int(sample_rate),
        "bands_hz": {k: list(v) for k, v in BANDS.items()},
        "thresholds": {
            "rumble_ratio_min": RUMBLE_RATIO_MIN,
            "mud_ratio_min": MUD_RATIO_MIN,
            "harshness_ratio_min": HARSHNESS_RATIO_MIN,
            "mud_centroid_max": MUD_CENTROID_MAX,
            "sibilance_ratio_min": SIBILANCE_RATIO_MIN,
            "noise_floor_dbfs_min": NOISE_FLOOR_DBFS_MIN,
        },
        "single_metric_cap": SINGLE_METRIC_CAP,
    }
    return observations, context


def interpret_spectral(observations: list[Observation]) -> list[Interpretation]:
    """Derive issue hypotheses from observations. No actions, no recommendations."""
    by_metric = {o.metric: o for o in observations}
    if not by_metric:
        return []

    centroid = by_metric["centroid_hz"].value
    interpretations: list[Interpretation] = []

    def add(issue: str, obs_id: str, value: float, threshold: float, span: float,
            corroborated: bool, corroborating_id: str | None, rationale: str) -> None:
        if value <= threshold:
            return
        cap = CORROBORATED_CAP if corroborated else SINGLE_METRIC_CAP
        conf = _ratio_confidence(value, threshold, span, cap)
        supporting = [obs_id] + ([corroborating_id] if corroborated and corroborating_id else [])
        interpretations.append(
            Interpretation(
                id=f"interp.{issue}",
                issue=issue,
                supporting_observation_ids=tuple(supporting),
                confidence=conf,
                rationale=rationale,
            )
        )

    add("rumble", "spectral.rumble_ratio", by_metric["rumble_ratio"].value,
        RUMBLE_RATIO_MIN, 0.10, corroborated=False, corroborating_id=None,
        rationale="Sub-80Hz energy elevated relative to full band.")

    # Muddiness requires BOTH high mud_ratio and a low centroid (evidence-based
    # gate from M17 calibration). Low centroid is the corroborating observation.
    mud_ratio = by_metric["mud_ratio"].value
    if mud_ratio > MUD_RATIO_MIN and centroid < MUD_CENTROID_MAX:
        conf = _ratio_confidence(mud_ratio, MUD_RATIO_MIN, 4.0, CORROBORATED_CAP)
        interpretations.append(Interpretation(
            id="interp.muddiness",
            issue="muddiness",
            supporting_observation_ids=("spectral.mud_ratio", "spectral.centroid_hz"),
            confidence=conf,
            rationale=f"Low-mid (200-500Hz) dominates and the centroid is low "
                      f"({centroid:.0f}Hz), consistent with muddiness.",
        ))

    add("harshness", "spectral.harshness_ratio", by_metric["harshness_ratio"].value,
        HARSHNESS_RATIO_MIN, 0.38, corroborated=centroid > 3000,
        corroborating_id="spectral.centroid_hz",
        rationale="Upper-mid (2.5-6kHz) energy elevated"
                  + ("; high centroid corroborates." if centroid > 3000 else "."))

    add("sibilance", "spectral.sibilance_ratio", by_metric["sibilance_ratio"].value,
        SIBILANCE_RATIO_MIN, 0.32, corroborated=centroid > 4000,
        corroborating_id="spectral.centroid_hz",
        rationale="5-8kHz energy elevated"
                  + ("; high centroid corroborates." if centroid > 4000 else "."))

    noise_dbfs = by_metric["noise_floor_dbfs"].value
    if noise_dbfs > NOISE_FLOOR_DBFS_MIN:
        conf = _ratio_confidence(noise_dbfs, NOISE_FLOOR_DBFS_MIN, 15.0, SINGLE_METRIC_CAP)
        interpretations.append(
            Interpretation(
                id="interp.noise_floor",
                issue="noise_floor",
                supporting_observation_ids=("spectral.noise_floor_dbfs",),
                confidence=conf,
                rationale=f"Estimated noise floor {noise_dbfs:.0f} dBFS above policy minimum.",
            )
        )
    return interpretations


def diagnose_spectral(
    audio_path: str, asset_id: str = "unknown"
) -> tuple[DiagnosticResult, tuple[Interpretation, ...]]:
    """Read a WAV; return (observations as DiagnosticResult, interpretations)."""
    audio, sample_rate = sf.read(audio_path, dtype="float32")
    observations, context = measure_spectral(audio, int(sample_rate))
    interpretations = interpret_spectral(observations)
    result = DiagnosticResult(
        id=f"spectral:{asset_id}",
        audio_asset_id=asset_id,
        analyzer_version=SPECTRAL_ANALYZER_VERSION,
        measurement_context=context,
        observations=tuple(observations),
        integrity_flags=(),
    )
    return result, tuple(interpretations)
