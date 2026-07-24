"""Raw→wet transformation delta profiling (DT-55C).

Per aligned phrase: compact, robust features on both sides; the delta is
wet − raw. MP3-derived sources exclude codec-unreliable content above 16 kHz.
Deltas from lossy sources are DIRECTIONAL GUIDANCE, never exact targets.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.paired_corpus.alignment import AlignmentMap, envelope

BANDS = {
    "lowmid_250_500": (250.0, 500.0),
    "box_300_700": (300.0, 700.0),
    "harsh_2500_5000": (2500.0, 5000.0),
    "sib_5500_12000": (5500.0, 12000.0),
    "air_10000_16000": (10000.0, 16000.0),
}
TILT_LO, TILT_HI = 200.0, 8000.0


def _db(x: float) -> float:
    return 20.0 * np.log10(max(x, 1e-10))


def phrase_features(x: np.ndarray, sr: int) -> dict[str, float]:
    x = x.astype(np.float64)
    rms = float(np.sqrt(np.mean(x**2) + 1e-20))
    peak = float(np.max(np.abs(x)) + 1e-20)
    feats: dict[str, float] = {
        "rms_db": round(_db(rms), 3),
        "peak_db": round(_db(peak), 3),
        "crest_db": round(_db(peak) - _db(rms), 3),
    }
    spec = np.abs(np.fft.rfft(x)) ** 2
    freqs = np.fft.rfftfreq(len(x), 1.0 / sr)
    total = float(np.sum(spec[(freqs >= 60) & (freqs <= 16000)])) + 1e-20
    for name, (lo, hi) in BANDS.items():
        feats[name] = round(float(np.sum(spec[(freqs >= lo) & (freqs <= hi)])) / total, 6)
    # Spectral tilt: dB per octave via linear fit of log-power vs log2(freq).
    m = (freqs >= TILT_LO) & (freqs <= TILT_HI) & (spec > 0)
    if int(np.sum(m)) > 16:
        slope = np.polyfit(np.log2(freqs[m]), 10 * np.log10(spec[m]), 1)[0]
        feats["tilt_db_per_oct"] = round(float(slope), 3)
    else:
        feats["tilt_db_per_oct"] = 0.0
    # Intra-phrase floor: 10th percentile envelope (attack/decay dynamics proxy).
    env = envelope(x, sr)
    feats["phrase_floor_db"] = round(_db(float(np.percentile(env, 10))), 3)
    return feats


def gap_noise_floor_db(x: np.ndarray, sr: int) -> float:
    """Noise floor measured in the INTER-phrase gaps, relative to signal RMS.

    This is the honest noise measure: intra-phrase percentiles track level, not
    noise. Returns median gap-envelope level (dB) minus overall RMS (dB).
    """
    from src.paired_corpus.alignment import segment_phrases

    env = envelope(x, sr)
    from src.paired_corpus.alignment import ENV_HZ

    mask = np.ones(len(env), dtype=bool)
    for a, b in segment_phrases(x, sr):
        mask[int(a * ENV_HZ): int(b * ENV_HZ) + 1] = False
    if not np.any(mask):
        return 0.0
    gap_db = _db(float(np.median(env[mask])))
    rms_db = _db(float(np.sqrt(np.mean(x.astype(np.float64) ** 2) + 1e-20)))
    return round(gap_db - rms_db, 3)


@dataclass(frozen=True)
class PhraseDelta:
    raw_start_s: float
    raw: dict
    wet: dict
    delta: dict           # wet - raw per feature


@dataclass(frozen=True)
class TransformProfile:
    pair_id: str
    n_phrases_aligned: int
    n_phrases_total: int
    phrase_deltas: tuple[PhraseDelta, ...]
    summary: dict         # median delta per feature + phrase-level consistency
    source_quality: str = "lossy_mp3"
    limitation: str = "Directional guidance only: lossy sources; >16 kHz excluded."


def _slice(x: np.ndarray, sr: int, a: float, b: float) -> np.ndarray:
    i, j = max(int(a * sr), 0), min(int(b * sr), len(x))
    return x[i:j] if j > i else np.zeros(1, dtype=x.dtype)


def profile_pair(pair_id: str, raw: np.ndarray, wet: np.ndarray, sr: int,
                 amap: AlignmentMap) -> TransformProfile:
    deltas: list[PhraseDelta] = []
    for p in amap.aligned():
        fr = phrase_features(_slice(raw, sr, p.raw_start_s, p.raw_end_s), sr)
        fw = phrase_features(_slice(wet, sr, p.wet_start_s, p.wet_end_s), sr)
        deltas.append(PhraseDelta(
            p.raw_start_s, fr, fw,
            {k: round(fw[k] - fr[k], 6) for k in fr},
        ))
    summary: dict[str, float] = {}
    if deltas:
        keys = deltas[0].delta.keys()
        for k in keys:
            vals = np.array([d.delta[k] for d in deltas], dtype=float)
            summary[f"median_d_{k}"] = round(float(np.median(vals)), 4)
        # Phrase-level consistency: wet phrase RMS spread minus raw spread
        # (negative = the wet is more level-consistent, i.e. pro leveling).
        raw_rms = np.array([d.raw["rms_db"] for d in deltas])
        wet_rms = np.array([d.wet["rms_db"] for d in deltas])
        summary["phrase_rms_spread_raw_db"] = round(float(np.std(raw_rms)), 3)
        summary["phrase_rms_spread_wet_db"] = round(float(np.std(wet_rms)), 3)
        summary["d_phrase_consistency_db"] = round(
            float(np.std(wet_rms) - np.std(raw_rms)), 3)
        # Gap-based noise floor (whole-signal, level-relative): the honest noise measure.
        nf_raw = gap_noise_floor_db(raw, sr)
        nf_wet = gap_noise_floor_db(wet, sr)
        summary["gap_noise_floor_raw_db"] = nf_raw
        summary["gap_noise_floor_wet_db"] = nf_wet
        summary["d_gap_noise_floor_db"] = round(nf_wet - nf_raw, 3)
    return TransformProfile(
        pair_id, len(deltas), len(amap.phrases), tuple(deltas), summary,
    )
