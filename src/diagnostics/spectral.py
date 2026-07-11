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

SPECTRAL_ANALYZER_VERSION = "1.2.0"
# 1.2.0 (M26): evidence-based recalibration against corpus-v1 (80 real clean
# clips + recipe-labeled degradations; see reports/evaluations/corpus-v1/):
#   - rumble: per-bin mean-density ratio (values >1 on noise, 57.5% FP on
#     clean real vocals) replaced by a true energy FRACTION with a corpus-set
#     threshold (clean p90≈0.007 vs LF-loaded ≥0.02).
#   - harshness: threshold 0.12 -> 0.06 (clean p90=0.057, strong-defect
#     median=0.089; old threshold gave 17-33% recall).
#   - sibilance: static whole-clip ratio cannot separate defects from clean
#     on real vocals (0% recall); interpretation now uses the 95th-percentile
#     per-frame E(5-8k)/E(full). Known limitation: overlaps with genuinely
#     sibilant/noisy consumer-device recordings (vocadito) — confidence stays
#     single-metric-capped.

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
RUMBLE_FRACTION_MIN = 0.02   # sum-energy fraction E(20-80)/E(20-20k), corpus-calibrated
MUD_RATIO_MIN = 0.60
# Muddiness also requires a low spectral centroid: calibration (M17) showed the
# mud_ratio alone gives a 100% false-positive rate on clean harmonic voices
# (clean centroid ~925Hz, muddy ~413-456Hz). The centroid gate separates them.
MUD_CENTROID_MAX = 700.0
HARSHNESS_RATIO_MIN = 0.06
SIBILANCE_FRAME_P95_MIN = 0.18  # 95th-pct per-frame E(5-8k)/E(full)
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

    def _band_sum(lo: float, hi: float) -> float:
        mask = (freqs >= lo) & (freqs <= hi)
        return float(np.sum(stft_mag[mask, :] ** 2)) if np.any(mask) else 0.0

    # Rumble is a true energy fraction (sum-based), not a per-bin density ratio:
    # the 20-80 Hz band spans ~3 bins and per-bin means explode on LF noise.
    rumble_fraction = _ratio(_band_sum(*BANDS["rumble"]), _band_sum(*BANDS["full"]))
    mud_ratio = _ratio(e["mud"], e["clarity_ref"])
    harshness_ratio = _ratio(e["harshness"], e["low_ref"])
    sibilance_ratio = _ratio(e["sibilance"], e["mid_ref"])
    air_ratio = _ratio(e["air"], e["mid_ref"])

    # Frame-level sibilance: sibilant events are short; whole-clip ratios
    # dilute them below any usable threshold on real vocals (corpus-v1 evidence).
    sib_mask = (freqs >= BANDS["sibilance"][0]) & (freqs <= BANDS["sibilance"][1])
    frame_full = np.sum(stft_mag ** 2, axis=0) + 1e-20
    sibilance_frame_p95 = float(np.percentile(np.sum(stft_mag[sib_mask, :] ** 2, axis=0) / frame_full, 95))

    centroid_hz = float(np.mean(librosa.feature.spectral_centroid(y=mono, sr=sample_rate)[0]))

    frame_rms = librosa.feature.rms(y=mono, frame_length=RMS_FRAME_LENGTH, hop_length=RMS_HOP_LENGTH)[0]
    noise_floor_dbfs = 20.0 * math.log10(float(np.percentile(frame_rms, 5)) + 1e-12)

    observations = [
        Observation(id="spectral.rumble_fraction", metric="rumble_fraction", value=rumble_fraction,
                    units="fraction", confidence=1.0, evidence="sum E(20-80) / sum E(20-20k)"),
        Observation(id="spectral.mud_ratio", metric="mud_ratio", value=mud_ratio,
                    units="ratio", confidence=1.0, evidence="E(200-500)/E(1k-4k)"),
        Observation(id="spectral.harshness_ratio", metric="harshness_ratio", value=harshness_ratio,
                    units="ratio", confidence=1.0, evidence="E(2.5k-6k)/E(200-2k)"),
        Observation(id="spectral.sibilance_ratio", metric="sibilance_ratio", value=sibilance_ratio,
                    units="ratio", confidence=1.0, evidence="E(5k-8k)/E(200-4k)"),
        Observation(id="spectral.sibilance_frame_p95", metric="sibilance_frame_p95",
                    value=sibilance_frame_p95, units="fraction", confidence=0.9,
                    evidence="95th-pct per-frame E(5k-8k)/E(full)"),
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
            "rumble_fraction_min": RUMBLE_FRACTION_MIN,
            "mud_ratio_min": MUD_RATIO_MIN,
            "harshness_ratio_min": HARSHNESS_RATIO_MIN,
            "mud_centroid_max": MUD_CENTROID_MAX,
            "sibilance_frame_p95_min": SIBILANCE_FRAME_P95_MIN,
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

    add("rumble", "spectral.rumble_fraction", by_metric["rumble_fraction"].value,
        RUMBLE_FRACTION_MIN, 0.08, corroborated=False, corroborating_id=None,
        rationale="Sub-80Hz energy fraction elevated (corpus-calibrated).")

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
        HARSHNESS_RATIO_MIN, 0.25, corroborated=centroid > 3000,
        corroborating_id="spectral.centroid_hz",
        rationale="Upper-mid (2.5-6kHz) energy elevated"
                  + ("; high centroid corroborates." if centroid > 3000 else "."))

    add("sibilance", "spectral.sibilance_frame_p95", by_metric["sibilance_frame_p95"].value,
        SIBILANCE_FRAME_P95_MIN, 0.25, corroborated=False, corroborating_id=None,
        rationale="Frames with 5-8kHz dominance (95th pct) exceed the corpus-"
                  "calibrated bound; known overlap with genuinely sibilant "
                  "consumer-device recordings keeps confidence single-metric-capped.")

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
