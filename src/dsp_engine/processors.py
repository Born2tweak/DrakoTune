"""Bounded DSP processor registry (M09).

Each Alpha processor is wrapped as a module that declares the objective it
serves, safe parameter ranges, artifact risk, and reversibility. The executor
clamps every parameter to these ranges before building a plugin, so a plan can
never drive a processor outside safe bounds.

This module contains no decision logic — it only describes how to realize a
named processor safely.
"""

from dataclasses import dataclass
from typing import Callable

from pedalboard import (
    Chorus,
    Clipping,
    Compressor,
    Delay,
    Distortion,
    Gain,
    HighpassFilter,
    HighShelfFilter,
    Limiter,
    LowpassFilter,
    LowShelfFilter,
    NoiseGate,
    PeakFilter,
    Pedalboard,
    PitchShift,
    Reverb,
)

from src.dsp_engine.deesser import de_ess
from src.dsp_engine.dynamics import (
    dynamic_eq,
    saturate,
    suppress_resonances,
    vocal_rider,
)

# 1.1.0 (M30): array processors + DeEsser
# 2.0.0 (DT-94): graph routing (serial/parallel/send) + explicit channel
#   contracts + 8 previously-unexposed pedalboard primitives. Major because the
#   registry grew from 9 to 17 entries and buffers are now canonical 2-D.
# 2.1.0 (DT-96): VocalRider, DynamicEQ, ResonanceSuppressor and oversampled
#   Saturation — implementations, not aliases (see dsp_engine/dynamics.py).
PROCESSOR_ENGINE_VERSION = "2.1.0"


@dataclass(frozen=True)
class ProcessorSpec:
    """How to safely realize one named processor.

    Exactly one of `factory` (returns a pedalboard plugin) or `process`
    (pure array function: (mono float32, sample_rate, params) -> mono float32)
    is set. Array processors let the executor run DSP that pedalboard has no
    plugin for (M30: the frame-level de-esser) while keeping the same bounded,
    clamped, plan-authored contract.
    """

    processor: str
    objective: str
    safe_ranges: dict[str, tuple[float, float]]
    artifact_risk: str  # low | medium | high
    reversible: bool
    factory: Callable[[dict], object] | None = None
    process: Callable[..., object] | None = None


PROCESSORS: dict[str, ProcessorSpec] = {
    "Gain": ProcessorSpec(
        "Gain", "gain_stage", {"gain_db": (-24.0, 12.0)}, "low", True,
        lambda p: Gain(**p),
    ),
    "HighpassFilter": ProcessorSpec(
        "HighpassFilter", "reduce_rumble", {"cutoff_frequency_hz": (20.0, 500.0)}, "low", True,
        lambda p: HighpassFilter(**p),
    ),
    "PeakFilter": ProcessorSpec(
        "PeakFilter", "corrective_eq",
        {"cutoff_frequency_hz": (20.0, 20000.0), "gain_db": (-12.0, 12.0), "q": (0.3, 8.0)},
        "medium", True,
        lambda p: PeakFilter(**p),
    ),
    "HighShelfFilter": ProcessorSpec(
        "HighShelfFilter", "boost_air",
        {"cutoff_frequency_hz": (2000.0, 20000.0), "gain_db": (-6.0, 6.0), "q": (0.3, 4.0)},
        "medium", True,
        lambda p: HighShelfFilter(**p),
    ),
    "Compressor": ProcessorSpec(
        "Compressor", "stabilize_dynamics",
        {"threshold_db": (-60.0, 0.0), "ratio": (1.0, 20.0),
         "attack_ms": (0.1, 100.0), "release_ms": (10.0, 1000.0)},
        "high", True,
        lambda p: Compressor(**p),
    ),
    "NoiseGate": ProcessorSpec(
        "NoiseGate", "reduce_noise",
        {"threshold_db": (-80.0, -10.0), "attack_ms": (0.1, 50.0), "release_ms": (10.0, 500.0)},
        "high", True,
        lambda p: NoiseGate(**p),
    ),
    "Limiter": ProcessorSpec(
        "Limiter", "output_safety",
        {"threshold_db": (-12.0, 0.0), "release_ms": (10.0, 1000.0)},
        "low", True,
        lambda p: Limiter(**p),
    ),
    # M30: frame-level dynamic de-esser (array processor; pedalboard has no
    # de-esser plugin). Evidence: static sibilance cut left the sibilance
    # diagnosis firing on 3/3 user-tested processed files (informal_listening_
    # notes.md). Attenuates only sibilant frames' band bins, hard-capped depth
    # (lisp guard), smoothed release.
    "DeEsser": ProcessorSpec(
        "DeEsser", "reduce_sibilance",
        {"band_lo_hz": (4000.0, 6000.0), "band_hi_hz": (7000.0, 11000.0),
         "frame_threshold": (0.10, 0.50), "max_reduction_db": (2.0, 10.0)},
        "medium", True,
        process=lambda audio, sr, p: de_ess(audio, sr, **p),
    ),
    # M28: narrow notches at the mains base + harmonics. Only reachable via
    # the strictly gated "hum_confirmed" interpretation (0% clean FP on
    # corpus-v1); a false trigger at 120/180 Hz could hit a vocal fundamental,
    # hence the high-Q, bounded-depth, max-3-harmonics design.
    "HumNotch": ProcessorSpec(
        "HumNotch", "reduce_hum",
        {"base_hz": (45.0, 65.0), "gain_db": (-15.0, -3.0),
         "q": (4.0, 12.0), "harmonics": (1, 3)},
        "medium", True,
        lambda p: Pedalboard([
            PeakFilter(cutoff_frequency_hz=p["base_hz"] * k,
                       gain_db=p["gain_db"], q=p["q"])
            for k in range(1, int(p["harmonics"]) + 1)
        ]),
    ),
    # ---------------------------------------------------------------------
    # DT-94: primitives that ship with pedalboard but were never exposed.
    #
    # Exposing a primitive removes a dependency/licensing barrier; it does NOT
    # make a finished production processor. Naming here is deliberately literal
    # about what the code does — the tuned, composite versions (tasteful
    # saturation, ducked plate-style sends, mono-safe doubling) are DT-96, and
    # the honest-naming rule is recorded in MILESTONES/DT_93_106.md.
    # ---------------------------------------------------------------------
    "LowShelfFilter": ProcessorSpec(
        "LowShelfFilter", "shape_body",
        {"cutoff_frequency_hz": (60.0, 600.0), "gain_db": (-12.0, 12.0), "q": (0.3, 4.0)},
        "medium", True,
        lambda p: LowShelfFilter(**p),
    ),
    "LowpassFilter": ProcessorSpec(
        "LowpassFilter", "reduce_brightness",
        {"cutoff_frequency_hz": (2000.0, 20000.0)},
        "medium", True,
        lambda p: LowpassFilter(**p),
    ),
    # Generic algorithmic reverb. NOT a plate — pedalboard's Reverb is a
    # Freeverb-style room. Mode presets tune it; none of them may be labelled
    # "plate" until a real plate implementation exists.
    "Reverb": ProcessorSpec(
        "Reverb", "add_space",
        {"room_size": (0.0, 1.0), "damping": (0.0, 1.0), "wet_level": (0.0, 1.0),
         "dry_level": (0.0, 1.0), "width": (0.0, 1.0), "freeze_mode": (0.0, 0.0)},
        "medium", True,
        lambda p: Reverb(**p),
    ),
    "Delay": ProcessorSpec(
        "Delay", "add_depth",
        {"delay_seconds": (0.0, 2.0), "feedback": (0.0, 0.9), "mix": (0.0, 1.0)},
        "medium", True,
        lambda p: Delay(**p),
    ),
    # Raw nonlinearity. Tasteful saturation needs a drive curve, oversampling and
    # a program-dependent wet/dry blend on top of this — that is DT-96 work, not
    # an inherited capability.
    "Distortion": ProcessorSpec(
        "Distortion", "add_harmonics",
        {"drive_db": (0.0, 24.0)},
        "high", True,
        lambda p: Distortion(**p),
    ),
    "Clipping": ProcessorSpec(
        "Clipping", "soft_clip",
        {"threshold_db": (-24.0, 0.0)},
        "high", True,
        lambda p: Clipping(**p),
    ),
    "Chorus": ProcessorSpec(
        "Chorus", "add_movement",
        {"rate_hz": (0.1, 5.0), "depth": (0.0, 1.0), "centre_delay_ms": (1.0, 30.0),
         "feedback": (0.0, 0.5), "mix": (0.0, 1.0)},
        "medium", True,
        lambda p: Chorus(**p),
    ),
    # TRANSPOSITION ONLY. This shifts the whole signal by a fixed interval; it
    # performs no pitch detection and no per-note correction. It must never be
    # surfaced as "tuning", "pitch correction" or "Auto-Tune" (DT-100 is the
    # milestone that would earn those words).
    "PitchShift": ProcessorSpec(
        "PitchShift", "transpose",
        {"semitones": (-12.0, 12.0)},
        "high", True,
        lambda p: PitchShift(**p),
    ),
    # ---------------------------------------------------------------------
    # DT-96: substantive processors. Each exists because no pedalboard plugin
    # does the job — see src/dsp_engine/dynamics.py for why in each case.
    # ---------------------------------------------------------------------
    "VocalRider": ProcessorSpec(
        "VocalRider", "level_performance",
        {"target_percentile": (40.0, 90.0), "max_boost_db": (0.0, 12.0),
         "max_cut_db": (0.0, 12.0), "smoothing_ms": (20.0, 500.0),
         "silence_floor_db": (-70.0, -25.0)},
        "medium", True,
        process=lambda audio, sr, p: vocal_rider(audio, sr, **p),
    ),
    "DynamicEQ": ProcessorSpec(
        "DynamicEQ", "dynamic_tone",
        {"band_lo_hz": (50.0, 8000.0), "band_hi_hz": (100.0, 16000.0),
         "threshold_ratio": (1.0, 4.0), "max_reduction_db": (0.0, 12.0),
         "smoothing_ms": (20.0, 300.0)},
        "medium", True,
        process=lambda audio, sr, p: dynamic_eq(audio, sr, **p),
    ),
    "ResonanceSuppressor": ProcessorSpec(
        "ResonanceSuppressor", "suppress_resonance",
        {"search_lo_hz": (80.0, 1000.0), "search_hi_hz": (1000.0, 12000.0),
         "max_resonances": (1, 6), "prominence_ratio": (1.2, 5.0),
         "max_reduction_db": (0.0, 12.0)},
        "medium", True,
        process=lambda audio, sr, p: suppress_resonances(audio, sr, **p),
    ),
    "Saturation": ProcessorSpec(
        "Saturation", "add_density",
        {"drive_db": (0.0, 18.0), "character": (0.0, 1.0),
         "mix": (0.0, 1.0), "oversample": (1, 8)},
        "medium", True,
        process=lambda audio, sr, p: saturate(audio, sr, **p),
    ),
}


def clamp_params(processor: str, params: dict) -> tuple[dict, list[str]]:
    """Clamp params to the processor's safe ranges. Returns (params, clamped_keys)."""
    spec = PROCESSORS.get(processor)
    if spec is None:
        return dict(params), []
    out: dict = {}
    clamped: list[str] = []
    for key, value in params.items():
        rng = spec.safe_ranges.get(key)
        if rng is None:
            out[key] = value
            continue
        lo, hi = rng
        new_value = min(max(value, lo), hi)
        out[key] = new_value
        if new_value != value:
            clamped.append(key)
    return out, clamped
