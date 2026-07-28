"""Mode and intensity contracts (DT-95).

Each mode is a function from `Intensity` to a `GraphNode`. Intensity changes
topology, not just magnitude:

    SUBTLE    repair and corrective tone only. No parallel bus, no sends.
    BALANCED  + tone shaping and light character.
    BOLD      + parallel compression and ducked sends. The default.
    EXTREME   + stronger drive, more space, wider treatment.

That distinction matters: multiplying every parameter by a constant produces
four versions of the same sound. Adding and removing whole branches is what
makes Subtle and Bold recognisably different things.

All parameter values are authored and bounded; the registry clamps them again at
render time, so a mode cannot drive a processor outside its safe range.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from src.dsp_engine.graph import GraphNode, Parallel, Processor, Send, Serial

MODE_CONTRACT_VERSION = "1.0.0"


class Intensity(Enum):
    SUBTLE = "subtle"
    BALANCED = "balanced"
    BOLD = "bold"
    EXTREME = "extreme"


INTENSITY_ORDER = (
    Intensity.SUBTLE,
    Intensity.BALANCED,
    Intensity.BOLD,
    Intensity.EXTREME,
)


def _at_least(intensity: Intensity, floor: Intensity) -> bool:
    return INTENSITY_ORDER.index(intensity) >= INTENSITY_ORDER.index(floor)


@dataclass(frozen=True)
class ModeSpec:
    """A named production chain.

    `capabilities` is the honest list of what the chain actually does. It is
    surfaced to the UI and must not name a capability the engine lacks.
    """

    name: str
    title: str
    summary: str
    capabilities: tuple[str, ...]
    build: Callable[[Intensity], GraphNode]
    default_intensity: Intensity = Intensity.BOLD


# ---------------------------------------------------------------------------
# Natural — the conservative baseline, close to the pre-V3 champion behavior.
# Kept so there is always an honest low-intervention option to compare against.
# ---------------------------------------------------------------------------
def _natural(intensity: Intensity) -> GraphNode:
    nodes: list[GraphNode] = [
        Processor("HighpassFilter", {"cutoff_frequency_hz": 75.0}),
        Processor("PeakFilter", {"cutoff_frequency_hz": 300.0, "gain_db": -2.0, "q": 1.0}),
        Processor("DeEsser", {"band_lo_hz": 5000.0, "band_hi_hz": 9000.0,
                              "frame_threshold": 0.22, "max_reduction_db": 4.0}),
    ]
    if _at_least(intensity, Intensity.BALANCED):
        nodes.append(Processor("Compressor", {"threshold_db": -20.0, "ratio": 2.0,
                                              "attack_ms": 12.0, "release_ms": 140.0}))
        nodes.append(Processor("HighShelfFilter", {"cutoff_frequency_hz": 9000.0,
                                                   "gain_db": 1.5, "q": 0.7}))
    if _at_least(intensity, Intensity.BOLD):
        nodes.append(Processor("LowShelfFilter", {"cutoff_frequency_hz": 180.0,
                                                  "gain_db": 1.5, "q": 0.7}))
    return Serial(nodes)


# ---------------------------------------------------------------------------
# Rescue — for weak microphones and untreated rooms.
#
# V1 SCOPE, stated honestly: this chain has NO broadband denoiser and NO
# dereverberation. It has a gate, rumble/hum removal, static resonance cuts, and
# tonal reduction of room-coloured low-mids. Real denoising and room reduction
# are DT-101 and arrive in Rescue V2.
# ---------------------------------------------------------------------------
def _rescue(intensity: Intensity) -> GraphNode:
    nodes: list[GraphNode] = [
        # Repair: rumble, mains hum, then a gate (a gate, not a denoiser).
        Processor("HighpassFilter", {"cutoff_frequency_hz": 95.0}),
        Processor("HumNotch", {"base_hz": 60.0, "gain_db": -9.0, "q": 8.0, "harmonics": 2}),
        Processor("NoiseGate", {"threshold_db": -46.0, "attack_ms": 2.0, "release_ms": 220.0}),
        # Tonal room reduction: cut the boxy low-mid build-up a small untreated
        # room adds. This is EQ, not dereverberation — the reflections remain.
        Processor("PeakFilter", {"cutoff_frequency_hz": 300.0, "gain_db": -5.0, "q": 1.1}),
        Processor("PeakFilter", {"cutoff_frequency_hz": 500.0, "gain_db": -3.0, "q": 1.6}),
        # Static resonance cut. The dynamic version is DT-96.
        Processor("PeakFilter", {"cutoff_frequency_hz": 2400.0, "gain_db": -3.5, "q": 3.5}),
        Processor("DeEsser", {"band_lo_hz": 4800.0, "band_hi_hz": 9500.0,
                              "frame_threshold": 0.16, "max_reduction_db": 7.0}),
    ]

    if _at_least(intensity, Intensity.BALANCED):
        nodes += [
            Processor("Compressor", {"threshold_db": -22.0, "ratio": 3.0,
                                     "attack_ms": 8.0, "release_ms": 120.0}),
            Processor("HighShelfFilter", {"cutoff_frequency_hz": 8000.0,
                                          "gain_db": 3.0, "q": 0.7}),
        ]

    if _at_least(intensity, Intensity.BOLD):
        # Parallel density: a crushed copy under the dry so thin, distant
        # recordings gain weight without the dry being flattened.
        nodes.append(Parallel(
            branch=Serial([
                Processor("Compressor", {"threshold_db": -32.0, "ratio": 6.0,
                                         "attack_ms": 3.0, "release_ms": 110.0}),
                Processor("Distortion", {"drive_db": 6.0}),
                Processor("Gain", {"gain_db": 3.0}),
            ]),
            blend=0.35, label="rescue_density",
        ))
        nodes.append(Processor("LowShelfFilter", {"cutoff_frequency_hz": 190.0,
                                                  "gain_db": 2.5, "q": 0.7}))
        # Tight, short generic room so the vocal is placed rather than dry-flat.
        nodes.append(Send(
            branch=Processor("Reverb", {"room_size": 0.22, "damping": 0.65,
                                        "wet_level": 1.0, "dry_level": 0.0, "width": 0.8}),
            level=0.14, duck=0.75, label="rescue_room",
        ))

    if intensity is Intensity.EXTREME:
        nodes.append(Processor("Clipping", {"threshold_db": -4.0}))
        nodes.append(Processor("HighShelfFilter", {"cutoff_frequency_hz": 11000.0,
                                                   "gain_db": 2.5, "q": 0.7}))

    return Serial(nodes)


# ---------------------------------------------------------------------------
# Modern Rap — forward, dense, bright, tightly controlled.
# ---------------------------------------------------------------------------
def _modern_rap(intensity: Intensity) -> GraphNode:
    nodes: list[GraphNode] = [
        Processor("HighpassFilter", {"cutoff_frequency_hz": 105.0}),
        Processor("PeakFilter", {"cutoff_frequency_hz": 320.0, "gain_db": -4.0, "q": 1.3}),
        Processor("DeEsser", {"band_lo_hz": 5200.0, "band_hi_hz": 10000.0,
                              "frame_threshold": 0.15, "max_reduction_db": 8.0}),
        # Serial stage one: fast peak control so no word stabs.
        Processor("Compressor", {"threshold_db": -18.0, "ratio": 3.0,
                                 "attack_ms": 4.0, "release_ms": 90.0}),
    ]

    if _at_least(intensity, Intensity.BALANCED):
        nodes += [
            # Serial stage two: slower levelling, so neither compressor works hard.
            Processor("Compressor", {"threshold_db": -26.0, "ratio": 2.5,
                                     "attack_ms": 25.0, "release_ms": 220.0}),
            Processor("PeakFilter", {"cutoff_frequency_hz": 3200.0, "gain_db": 2.5, "q": 1.1}),
            Processor("HighShelfFilter", {"cutoff_frequency_hz": 9500.0,
                                          "gain_db": 3.5, "q": 0.7}),
        ]

    if _at_least(intensity, Intensity.BOLD):
        nodes.append(Parallel(
            branch=Serial([
                Processor("Compressor", {"threshold_db": -34.0, "ratio": 10.0,
                                         "attack_ms": 1.5, "release_ms": 80.0}),
                Processor("Distortion", {"drive_db": 9.0}),
                Processor("Gain", {"gain_db": 4.0}),
            ]),
            blend=0.45, label="rap_density",
        ))
        nodes.append(Processor("LowShelfFilter", {"cutoff_frequency_hz": 160.0,
                                                  "gain_db": 2.0, "q": 0.7}))
        # Slap delay for depth, ducked so it sits behind the words.
        nodes.append(Send(
            branch=Processor("Delay", {"delay_seconds": 0.09, "feedback": 0.12, "mix": 1.0}),
            level=0.18, duck=0.7, label="rap_slap",
        ))
        # Short bright room. Generic algorithmic reverb — not a plate.
        nodes.append(Send(
            branch=Processor("Reverb", {"room_size": 0.3, "damping": 0.35,
                                        "wet_level": 1.0, "dry_level": 0.0, "width": 1.0}),
            level=0.16, duck=0.8, label="rap_room",
        ))

    if intensity is Intensity.EXTREME:
        nodes.append(Processor("Clipping", {"threshold_db": -3.0}))
        nodes.append(Send(
            branch=Processor("Chorus", {"rate_hz": 0.7, "depth": 0.35,
                                        "centre_delay_ms": 14.0, "feedback": 0.1, "mix": 1.0}),
            level=0.22, duck=0.5, label="rap_width",
        ))

    return Serial(nodes)


MODES: dict[str, ModeSpec] = {
    "natural": ModeSpec(
        name="natural",
        title="Natural",
        summary="Low-intervention cleanup. The honest baseline to compare against.",
        capabilities=(
            "rumble removal",
            "corrective low-mid cut",
            "sibilance control",
            "gentle levelling",
        ),
        build=_natural,
        default_intensity=Intensity.BALANCED,
    ),
    "rescue": ModeSpec(
        name="rescue",
        title="Rescue",
        summary="For weak microphones and untreated rooms: repair, weight and control.",
        capabilities=(
            "rumble removal",
            "mains hum removal",
            "noise gating (not broadband denoising)",
            "tonal room-colour reduction (not dereverberation)",
            "static resonance reduction",
            "sibilance control",
            "parallel density",
            "tight ducked room",
        ),
        build=_rescue,
    ),
    "modern_rap": ModeSpec(
        name="modern_rap",
        title="Modern Rap",
        summary="Forward, dense and bright, with tight ducked space.",
        capabilities=(
            "rumble removal",
            "low-mid cut",
            "serial two-stage compression",
            "parallel density",
            "presence and air",
            "ducked slap delay",
            "ducked short room",
        ),
        build=_modern_rap,
    ),
}


def list_modes() -> tuple[str, ...]:
    return tuple(MODES)


def get_mode(name: str) -> ModeSpec:
    try:
        return MODES[name]
    except KeyError:
        raise KeyError(f"unknown mode {name!r}; available: {', '.join(sorted(MODES))}") from None


def build_graph(name: str, intensity: Intensity | str | None = None) -> GraphNode:
    """Build the graph for `name` at `intensity` (defaults to the mode's own default)."""
    spec = get_mode(name)
    if intensity is None:
        resolved = spec.default_intensity
    elif isinstance(intensity, str):
        resolved = Intensity(intensity)
    else:
        resolved = intensity
    return spec.build(resolved)


def describe_mode(name: str, intensity: Intensity | str | None = None) -> str:
    return build_graph(name, intensity).describe()
