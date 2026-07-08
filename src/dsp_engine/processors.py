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
    Compressor,
    Gain,
    HighpassFilter,
    HighShelfFilter,
    Limiter,
    NoiseGate,
    PeakFilter,
)

PROCESSOR_ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class ProcessorSpec:
    """How to safely realize one named processor."""

    processor: str
    objective: str
    safe_ranges: dict[str, tuple[float, float]]
    artifact_risk: str  # low | medium | high
    reversible: bool
    factory: Callable[[dict], object]


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
