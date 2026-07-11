"""Loudness-matched A/B pair export (M23).

Every comparison — human or metric — must be loudness-matched first
(ADR 0004 §1): both stimuli at TARGET_LUFS integrated, true-peak-guarded,
and the pair is refused if the post-match difference exceeds MAX_MISMATCH_LU.
Attenuation is preferred; gain-up is applied only when needed to reach the
target and is always peak-guarded (which may cause a refusal — by design,
rather than emitting a bias-carrying pair).
"""

import math
from dataclasses import dataclass

import numpy as np
import pyloudnorm
import soundfile as sf

AB_EXPORT_VERSION = "1.0.0"

TARGET_LUFS = -23.0
PEAK_CEILING_DBFS = -1.5      # sample-peak guard applied post-gain
MAX_MISMATCH_LU = 0.5


class LoudnessMatchError(ValueError):
    """The pair could not be matched within tolerance; do not compare it."""


@dataclass(frozen=True)
class MatchedPair:
    a: np.ndarray
    b: np.ndarray
    sample_rate: int
    a_gain_db: float
    b_gain_db: float
    a_lufs: float
    b_lufs: float

    def to_dict(self) -> dict:
        return {
            "version": AB_EXPORT_VERSION, "target_lufs": TARGET_LUFS,
            "a_gain_db": round(self.a_gain_db, 3), "b_gain_db": round(self.b_gain_db, 3),
            "a_lufs": round(self.a_lufs, 3), "b_lufs": round(self.b_lufs, 3),
        }


def _integrated_lufs(audio: np.ndarray, sample_rate: int) -> float:
    lufs = pyloudnorm.Meter(sample_rate).integrated_loudness(audio.astype(np.float64))
    if not math.isfinite(lufs) or lufs <= -70.0:
        raise LoudnessMatchError("integrated loudness unmeasurable (too short or silent)")
    return float(lufs)


def _match_one(audio: np.ndarray, sample_rate: int, target_lufs: float) -> tuple[np.ndarray, float, float]:
    gain_db = target_lufs - _integrated_lufs(audio, sample_rate)
    out = audio.astype(np.float32) * (10.0 ** (gain_db / 20.0))
    ceiling = 10.0 ** (PEAK_CEILING_DBFS / 20.0)
    peak = float(np.max(np.abs(out)))
    if peak > ceiling:  # peak guard wins over exact loudness
        out = out * (ceiling / peak)
        gain_db += 20.0 * math.log10(ceiling / peak)
    return out, gain_db, _integrated_lufs(out, sample_rate)


def loudness_matched_pair(
    a: np.ndarray, b: np.ndarray, sample_rate: int, target_lufs: float = TARGET_LUFS
) -> MatchedPair:
    """Match both signals to target LUFS. Raises LoudnessMatchError on failure."""
    a_out, a_gain, a_lufs = _match_one(a, sample_rate, target_lufs)
    b_out, b_gain, b_lufs = _match_one(b, sample_rate, target_lufs)
    mismatch = abs(a_lufs - b_lufs)
    if mismatch > MAX_MISMATCH_LU:
        raise LoudnessMatchError(
            f"post-match loudness differs by {mismatch:.2f} LU "
            f"(> {MAX_MISMATCH_LU}); pair refused to prevent loudness bias"
        )
    return MatchedPair(a_out, b_out, sample_rate, a_gain, b_gain, a_lufs, b_lufs)


def export_matched_pair(
    a_path: str, b_path: str, out_a_path: str, out_b_path: str
) -> MatchedPair:
    """File-based convenience wrapper used by listening-session preparation."""
    a, sr_a = sf.read(a_path, dtype="float32")
    b, sr_b = sf.read(b_path, dtype="float32")
    if sr_a != sr_b:
        raise LoudnessMatchError(f"sample-rate mismatch: {sr_a} vs {sr_b}")
    pair = loudness_matched_pair(a, b, int(sr_a))
    sf.write(out_a_path, pair.a, pair.sample_rate, subtype="PCM_16")
    sf.write(out_b_path, pair.b, pair.sample_rate, subtype="PCM_16")
    return pair
