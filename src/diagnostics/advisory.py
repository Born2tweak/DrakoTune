"""Advisory-only diagnostics (M25): hum, recording level, reverb, plosives.

ADVISORY CONTRACT: these diagnoses NEVER control DSP. The decision planner has
no processing specs for these issue names, so even if their interpretations
were passed to build_plan they would produce no actions; by policy they are
kept out of the plan path entirely and surface only in calibration reports and
(M27) user reports. Promotion to DSP-controlling status requires passing the
graded-severity calibration gate (roadmap M25/M26; ADR 0004 discipline).

Estimator honesty notes:
- hum: narrowband energy at 50/60 Hz + harmonics vs local band median. Robust.
- recording_level: integrated LUFS vs policy window. Robust.
- reverb: envelope floor + post-peak decay slope. EXPERIMENTAL — expected to
  confuse dense reverb with broadband noise; measured by calibrate_corpus.
- plosives: low-frequency transient bursts. Heuristic event counter.
"""

import math

import librosa
import numpy as np
import pyloudnorm
import soundfile as sf

from src.shared_types import DiagnosticResult, Interpretation, Observation

ADVISORY_ANALYZER_VERSION = "1.0.0"

# hum: a true mains hum is a narrow spectral spike that stands out from its
# immediate spectral neighborhood at multiple harmonics. Contrast against the
# local ring (not a global median — sparse harmonic voices make medians ~0).
HUM_BASES_HZ = (50.0, 60.0)
HUM_HARMONICS = 4
HUM_TOLERANCE_HZ = 2.0
HUM_RING_HZ = (5.0, 20.0)      # ring around each harmonic used as local floor
HUM_CONTRAST_MIN = 20.0        # peak/ring contrast for one harmonic to count
HUM_HARMONICS_MIN = 2          # >= this many contrasting harmonics -> hum
HUM_ABS_ENERGY_FRAC = 1e-8     # harmonic peak must carry this fraction of total
                               # energy — empty bins otherwise produce spurious
                               # contrast (numeric noise / numeric noise)

# recording level (policy window for a raw vocal handed to processing)
LEVEL_LOW_LUFS = -30.0
LEVEL_HIGH_LUFS = -10.0

# reverb (experimental): elevated inter-phrase floor with a decay rate in the
# "tail" band. Near-constant floors (hum, steady noise) decay slower than
# REVERB_DECAY_RANGE[0]; dry phrase endings decay faster than [1].
REVERB_FLOOR_RATIO_MIN = 0.05  # 20th-pct envelope vs 95th-pct envelope
REVERB_DECAY_RANGE_DB_PER_S = (10.0, 60.0)

# plosives
PLOSIVE_BAND_HZ = (30.0, 150.0)
PLOSIVE_BURST_FACTOR = 4.0     # LF frame energy vs median LF energy
PLOSIVE_LF_DOMINANCE = 0.5     # LF/full energy in the burst frame
PLOSIVE_RATE_MIN_PER_MIN = 4.0

_FRAME = 2048
_HOP = 512

ADVISORY_ISSUES = ("hum", "recording_level_low", "recording_level_high", "reverb", "plosives")


def _mono(audio: np.ndarray) -> np.ndarray:
    return audio.astype(np.float32) if audio.ndim == 1 else audio[:, 0].astype(np.float32)


def measure_advisory(audio: np.ndarray, sample_rate: int) -> tuple[list[Observation], dict]:
    mono = _mono(audio)
    if len(mono) < _FRAME * 4:
        return [], {"analyzer_version": ADVISORY_ANALYZER_VERSION, "reason": "signal_too_short"}

    observations: list[Observation] = []

    # --- hum ---
    spectrum = np.abs(np.fft.rfft(mono.astype(np.float64))) ** 2
    freqs = np.fft.rfftfreq(len(mono), 1.0 / sample_rate)
    total_energy = float(np.sum(spectrum)) + 1e-20
    best_base, best_count, best_contrast = HUM_BASES_HZ[0], 0, 0.0
    for base in HUM_BASES_HZ:
        contrasts = []
        for k in range(1, HUM_HARMONICS + 1):
            center = base * k
            peak_mask = np.abs(freqs - center) <= HUM_TOLERANCE_HZ
            ring_dist = np.abs(freqs - center)
            ring_mask = (ring_dist > HUM_RING_HZ[0]) & (ring_dist <= HUM_RING_HZ[1])
            if not (np.any(peak_mask) and np.any(ring_mask)):
                continue
            peak = float(np.max(spectrum[peak_mask]))
            if peak < HUM_ABS_ENERGY_FRAC * total_energy:
                contrasts.append(0.0)  # insignificant bin: cannot be audible hum
                continue
            contrasts.append(peak / (float(np.median(spectrum[ring_mask])) + 1e-20))
        count = sum(1 for c in contrasts if c > HUM_CONTRAST_MIN)
        if count > best_count or (count == best_count and contrasts and
                                  float(np.median(contrasts)) > best_contrast):
            best_base, best_count = base, count
            best_contrast = float(np.median(contrasts)) if contrasts else 0.0
    observations.append(Observation(
        id="advisory.hum_harmonic_count", metric="hum_harmonic_count", value=float(best_count),
        units="count", confidence=0.9,
        evidence=f"{best_base:.0f}Hz harmonics with peak/ring contrast > {HUM_CONTRAST_MIN}"))
    observations.append(Observation(
        id="advisory.hum_contrast", metric="hum_contrast", value=best_contrast, units="ratio",
        confidence=0.8, evidence="median peak/local-ring contrast across harmonics"))

    # --- recording level ---
    try:
        lufs = float(pyloudnorm.Meter(sample_rate).integrated_loudness(mono.astype(np.float64)))
    except Exception:
        lufs = -120.0
    observations.append(Observation(
        id="advisory.integrated_lufs", metric="advisory_integrated_lufs", value=lufs,
        units="LUFS", confidence=0.9 if lufs > -70 else 0.2, evidence="BS.1770 integrated"))

    # --- envelope floor + decay (reverb, experimental) ---
    rms = librosa.feature.rms(y=mono, frame_length=_FRAME, hop_length=_HOP)[0]
    peak_ref = float(np.percentile(rms, 95)) + 1e-12
    floor_ratio = float(np.percentile(rms, 20)) / peak_ref
    db = 20.0 * np.log10(rms / peak_ref + 1e-12)
    frame_s = _HOP / sample_rate
    window = max(int(0.3 / frame_s), 3)
    decay_rates = []
    median_db = float(np.median(db))
    for i in range(1, len(db) - window - 1):
        if db[i] > median_db and db[i] >= db[i - 1] and db[i] > db[i + 1]:  # local peak
            seg = db[i:i + window]
            slope = -float(np.polyfit(np.arange(window) * frame_s, seg, 1)[0])
            if slope > 0:
                decay_rates.append(slope)
    decay_db_per_s = float(np.median(decay_rates)) if decay_rates else float("inf")
    observations.append(Observation(
        id="advisory.envelope_floor_ratio", metric="envelope_floor_ratio", value=floor_ratio,
        units="ratio", confidence=0.7, evidence="20th-pct frame RMS vs 95th-pct"))
    observations.append(Observation(
        id="advisory.decay_db_per_s", metric="decay_db_per_s",
        value=decay_db_per_s if math.isfinite(decay_db_per_s) else 1e6,
        units="dB/s", confidence=0.5, evidence="median post-peak envelope decay (experimental)"))

    # --- plosives ---
    stft = np.abs(librosa.stft(mono, n_fft=_FRAME, hop_length=_HOP)) ** 2
    stft_freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=_FRAME)
    lf = stft[(stft_freqs >= PLOSIVE_BAND_HZ[0]) & (stft_freqs <= PLOSIVE_BAND_HZ[1])].sum(axis=0)
    full = stft.sum(axis=0) + 1e-20
    lf_median = float(np.median(lf)) + 1e-20
    burst = (lf > PLOSIVE_BURST_FACTOR * lf_median) & (lf / full > PLOSIVE_LF_DOMINANCE)
    events = int(np.sum(np.diff(burst.astype(int)) == 1))
    minutes = len(mono) / sample_rate / 60.0
    observations.append(Observation(
        id="advisory.plosive_rate", metric="plosive_rate_per_min",
        value=events / minutes if minutes > 0 else 0.0, units="events/min",
        confidence=0.6, evidence=f"{events} LF transient bursts"))

    context = {
        "analyzer_version": ADVISORY_ANALYZER_VERSION,
        "sample_rate": int(sample_rate),
        "thresholds": {
            "hum_contrast_min": HUM_CONTRAST_MIN, "hum_harmonics_min": HUM_HARMONICS_MIN,
            "level_low_lufs": LEVEL_LOW_LUFS, "level_high_lufs": LEVEL_HIGH_LUFS,
            "reverb_floor_ratio_min": REVERB_FLOOR_RATIO_MIN,
            "reverb_decay_range_db_per_s": list(REVERB_DECAY_RANGE_DB_PER_S),
            "plosive_rate_min_per_min": PLOSIVE_RATE_MIN_PER_MIN,
        },
        "advisory_only": True,
    }
    return observations, context


def interpret_advisory(observations: list[Observation]) -> list[Interpretation]:
    """Advisory interpretations. The planner has no specs for these issues."""
    by = {o.metric: o for o in observations}
    if not by:
        return []
    out: list[Interpretation] = []

    hum_count = by["hum_harmonic_count"].value
    hum_fired = hum_count >= HUM_HARMONICS_MIN
    if hum_fired:
        out.append(Interpretation(
            id="interp.hum", issue="hum",
            supporting_observation_ids=("advisory.hum_harmonic_count", "advisory.hum_contrast"),
            confidence=min(0.6 + 0.1 * hum_count, 0.9),
            rationale=f"{hum_count:.0f} mains harmonics stand out from their spectral "
                      f"neighborhood (median contrast {by['hum_contrast'].value:.0f}x)."))

    lufs = by["advisory_integrated_lufs"].value
    if -70.0 < lufs < LEVEL_LOW_LUFS:
        out.append(Interpretation(
            id="interp.recording_level_low", issue="recording_level_low",
            supporting_observation_ids=("advisory.integrated_lufs",), confidence=0.8,
            rationale=f"Integrated loudness {lufs:.1f} LUFS below policy minimum {LEVEL_LOW_LUFS}."))
    elif lufs > LEVEL_HIGH_LUFS:
        out.append(Interpretation(
            id="interp.recording_level_high", issue="recording_level_high",
            supporting_observation_ids=("advisory.integrated_lufs",), confidence=0.8,
            rationale=f"Integrated loudness {lufs:.1f} LUFS above policy maximum {LEVEL_HIGH_LUFS}."))

    floor = by["envelope_floor_ratio"].value
    decay = by["decay_db_per_s"].value
    lo, hi = REVERB_DECAY_RANGE_DB_PER_S
    if floor > REVERB_FLOOR_RATIO_MIN and lo <= decay <= hi and not hum_fired:
        # hum guard: a constant mains floor also raises the envelope floor;
        # when hum fired, the reverb hypothesis is suppressed (documented limit).
        out.append(Interpretation(
            id="interp.reverb", issue="reverb",
            supporting_observation_ids=("advisory.envelope_floor_ratio", "advisory.decay_db_per_s"),
            confidence=0.5,  # experimental estimator: capped LOW on purpose
            rationale=f"Elevated envelope floor ({floor:.2f}) decaying at {decay:.0f} dB/s "
                      f"(tail band {lo:.0f}-{hi:.0f}); reverb suspected (experimental)."))

    plosive_rate = by["plosive_rate_per_min"].value
    if plosive_rate > PLOSIVE_RATE_MIN_PER_MIN:
        out.append(Interpretation(
            id="interp.plosives", issue="plosives",
            supporting_observation_ids=("advisory.plosive_rate",), confidence=0.55,
            rationale=f"{plosive_rate:.1f} low-frequency transient bursts/min."))
    return out


def diagnose_advisory(
    audio_path: str, asset_id: str = "unknown"
) -> tuple[DiagnosticResult, tuple[Interpretation, ...]]:
    audio, sample_rate = sf.read(audio_path, dtype="float32")
    observations, context = measure_advisory(audio, int(sample_rate))
    interpretations = interpret_advisory(observations)
    return DiagnosticResult(
        id=f"advisory:{asset_id}", audio_asset_id=asset_id,
        analyzer_version=ADVISORY_ANALYZER_VERSION, measurement_context=context,
        observations=tuple(observations), integrity_flags=(),
    ), tuple(interpretations)
