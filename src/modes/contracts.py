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

from src.dsp_engine.graph import (
    DoubleVoice,
    Doubler,
    GraphNode,
    Parallel,
    Processor,
    Send,
    Serial,
)

# 1.1.0 — DT-107 retuned Modern Rap's presence/harshness stages. Chains changed,
# so rendered output changes; the mode set and contract shape did not.
MODE_CONTRACT_VERSION = "1.1.0"


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
# dereverberation. It has a gate, rumble/hum removal, dynamic low-mid control,
# and measured resonance suppression. Suppressing a room's ringing frequencies
# reduces its tonal signature; it does not remove the reflections themselves.
# Real denoising and dereverberation are DT-101 and arrive in Rescue V2.
# ---------------------------------------------------------------------------
def _rescue(intensity: Intensity) -> GraphNode:
    nodes: list[GraphNode] = [
        # Repair: rumble, mains hum, then a gate (a gate, not a denoiser).
        Processor("HighpassFilter", {"cutoff_frequency_hz": 95.0}),
        Processor("HumNotch", {"base_hz": 60.0, "gain_db": -9.0, "q": 8.0, "harmonics": 2}),
        Processor("NoiseGate", {"threshold_db": -46.0, "attack_ms": 2.0, "release_ms": 220.0}),
        # Tonal room reduction: cut the boxy low-mid build-up a small untreated
        # room adds. This is EQ, not dereverberation — the reflections remain.
        Processor("PeakFilter", {"cutoff_frequency_hz": 300.0, "gain_db": -3.0, "q": 1.1}),
        # DT-96: dynamic low-mid control. Acts only while the boxiness is
        # actually excessive, so sustained notes in that range are not gutted the
        # way the previous always-on cut did.
        Processor("DynamicEQ", {"band_lo_hz": 220.0, "band_hi_hz": 520.0,
                                "threshold_ratio": 1.25, "max_reduction_db": 6.0,
                                "smoothing_ms": 60.0}),
        # DT-96: find this room's actual ringing frequencies instead of assuming
        # a fixed 2.4 kHz notch that may hit nothing at all.
        Processor("ResonanceSuppressor", {"search_lo_hz": 180.0, "search_hi_hz": 5000.0,
                                          "max_resonances": 3, "prominence_ratio": 1.8,
                                          "max_reduction_db": 6.0}),
        Processor("DeEsser", {"band_lo_hz": 4800.0, "band_hi_hz": 9500.0,
                              "frame_threshold": 0.16, "max_reduction_db": 7.0}),
    ]

    if _at_least(intensity, Intensity.BALANCED):
        nodes += [
            # DT-96: ride levels BEFORE compression so the compressor is left
            # with far less to do. Weak-mic takes vary wildly word to word.
            Processor("VocalRider", {"target_percentile": 70.0, "max_boost_db": 7.0,
                                     "max_cut_db": 5.0, "smoothing_ms": 130.0,
                                     "silence_floor_db": -45.0}),
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
                # DT-96: oversampled, blended saturation rather than raw
                # Distortion — a thin weak-mic take needs harmonics that are not
                # aliased grit.
                Processor("Saturation", {"drive_db": 7.0, "character": 0.35,
                                         "mix": 0.7, "oversample": 4}),
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
        # DT-96: rider first — every word forward before any compressor acts.
        Processor("VocalRider", {"target_percentile": 75.0, "max_boost_db": 6.0,
                                 "max_cut_db": 6.0, "smoothing_ms": 100.0,
                                 "silence_floor_db": -45.0}),
        # Serial stage one: fast peak control so no word stabs.
        Processor("Compressor", {"threshold_db": -18.0, "ratio": 3.0,
                                 "attack_ms": 4.0, "release_ms": 90.0}),
    ]

    if _at_least(intensity, Intensity.BALANCED):
        nodes += [
            # Serial stage two: slower levelling, so neither compressor works hard.
            Processor("Compressor", {"threshold_db": -26.0, "ratio": 2.5,
                                     "attack_ms": 25.0, "release_ms": 220.0}),
            # DT-107: dynamic harshness control, retuned to 2.5-5 kHz. The band was
            # 2-4.5 kHz, which straddled the static presence boost below and left
            # the top of the harsh region uncovered.
            Processor("DynamicEQ", {"band_lo_hz": 2500.0, "band_hi_hz": 5000.0,
                                    "threshold_ratio": 1.25, "max_reduction_db": 6.0,
                                    "smoothing_ms": 40.0}),
            # DT-107: presence moved 3200 -> 1700 Hz at the same +2.5 dB.
            # The chain previously boosted 3.2 kHz statically while dynamically
            # cutting 2-4.5 kHz -- lifting and taming the same band. Moving the
            # lift below the harsh region lets the dynamic stage do its job, and
            # measured lower harsh-band energy with higher presence on every
            # fixture. Gain is unchanged, so this is placement, not more boost.
            Processor("PeakFilter", {"cutoff_frequency_hz": 1700.0, "gain_db": 2.5, "q": 1.1}),
            Processor("HighShelfFilter", {"cutoff_frequency_hz": 9500.0,
                                          "gain_db": 3.5, "q": 0.7}),
        ]

    if _at_least(intensity, Intensity.BOLD):
        nodes.append(Parallel(
            branch=Serial([
                Processor("Compressor", {"threshold_db": -34.0, "ratio": 10.0,
                                         "attack_ms": 1.5, "release_ms": 80.0}),
                # DT-96: harder character than Rescue (more odd harmonics), still
                # oversampled and blended so consonants survive.
                Processor("Saturation", {"drive_db": 9.0, "character": 0.6,
                                         "mix": 0.8, "oversample": 4}),
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

        # DT-98: artificial doubling. Two detuned, time-offset copies panned
        # opposite, under the dry. This is width, not tuning — the same take
        # shifted, never a second performance and never note correction.
        nodes.append(Doubler(
            voices=(DoubleVoice(detune_cents=-9.0, delay_ms=17.0, pan=-0.7),
                    DoubleVoice(detune_cents=+11.0, delay_ms=25.0, pan=+0.7)),
            level=0.32, label="rap_double",
        ))

    if intensity is Intensity.EXTREME:
        nodes.append(Processor("Clipping", {"threshold_db": -3.0}))
        nodes.append(Send(
            branch=Processor("Chorus", {"rate_hz": 0.7, "depth": 0.35,
                                        "centre_delay_ms": 14.0, "feedback": 0.1, "mix": 1.0}),
            level=0.22, duck=0.5, label="rap_width",
        ))

    return Serial(nodes)


# ---------------------------------------------------------------------------
# DT-108 challenger chains — reconstructed from instructional video, one creator
# each. These are EXPERIMENTAL and deliberately NOT merged with each other: the
# creators contradict one another on real parameters (see the spec document at
# docs/research/video_derived_chains.md), and averaging them would produce a
# compromise none of them endorsed.
#
# Every value is one of: VISIBLE (read off a plugin in a frame), STATED (spoken
# by the creator), INFERRED (deduced from the interface), or APPROX (a DrakoTune
# stand-in for a proprietary plugin's function). The per-line tags below say
# which. Nothing here is invented: where a value was unreadable it is left at a
# DrakoTune default and tagged UNKNOWN in the spec.
# ---------------------------------------------------------------------------

def _chain_angelomota(intensity: Intensity) -> GraphNode:
    """Video 170352 — @angelomota, 11-plugin FabFilter/API/Distressor chain.

    Signature move: cuts 2.5-5 kHz and puts every additive boost OUTSIDE that
    band (1.2k, 1.7k, 8k). Directly opposes _chain_leteveon below.
    """
    nodes: list[GraphNode] = [
        # VISIBLE: Gate threshold -52.0 dB, attack 9.54 ms, release 145 ms.
        Processor("NoiseGate", {"threshold_db": -52.0, "attack_ms": 9.5, "release_ms": 145.0}),
        # STATED: "low cut below like 80 cuz I got a low voice" — voice-conditioned.
        Processor("HighpassFilter", {"cutoff_frequency_hz": 80.0}),
        # STATED: dip between 200 and 500 for muddiness.
        Processor("PeakFilter", {"cutoff_frequency_hz": 350.0, "gain_db": -3.0, "q": 1.0}),
        # STATED: "a dip at 1k get rid of some more muddiness".
        Processor("PeakFilter", {"cutoff_frequency_hz": 1000.0, "gain_db": -2.0, "q": 1.2}),
        # STATED: "get rid of a little at the top around two and a half to 5k".
        Processor("PeakFilter", {"cutoff_frequency_hz": 3500.0, "gain_db": -2.5, "q": 0.9}),
        # STATED: 2 ms attack, 80 ms release, 4:1, ~6 dB GR. VISIBLE: Pro-C 2,
        # style Clean, mono. Threshold INFERRED to land near 6 dB GR.
        Processor("Compressor", {"threshold_db": -18.0, "ratio": 4.0,
                                 "attack_ms": 2.0, "release_ms": 80.0}),
        # STATED: API 2500, 6:1, quick attack, again about -6 dB.
        Processor("Compressor", {"threshold_db": -24.0, "ratio": 6.0,
                                 "attack_ms": 5.0, "release_ms": 150.0}),
    ]

    if _at_least(intensity, Intensity.BALANCED):
        nodes += [
            # STATED: boosts at 1700, 1.2k and 8k "for bite".
            Processor("PeakFilter", {"cutoff_frequency_hz": 1700.0, "gain_db": 2.0, "q": 1.1}),
            Processor("PeakFilter", {"cutoff_frequency_hz": 1200.0, "gain_db": 1.5, "q": 1.1}),
            Processor("HighShelfFilter", {"cutoff_frequency_hz": 8000.0,
                                          "gain_db": 2.0, "q": 0.7}),
            # STATED: Distressor, 6:1, only ~4 dB GR. APPROX: the Distressor's
            # harmonic character is a compressor plus saturation here; DrakoTune
            # has no Distressor-style program-dependent detector.
            Processor("Compressor", {"threshold_db": -20.0, "ratio": 6.0,
                                     "attack_ms": 8.0, "release_ms": 120.0}),
            Processor("Saturation", {"drive_db": 4.0, "character": 0.35,
                                     "mix": 0.5, "oversample": 4}),
            # VISIBLE: Fresh Air, knobs read 18 and 24. APPROX: Fresh Air is a
            # spectral exciter that generates new HF content; a high shelf only
            # lifts what is already there. Documented limitation.
            Processor("HighShelfFilter", {"cutoff_frequency_hz": 12000.0,
                                          "gain_db": 2.5, "q": 0.7}),
        ]

    if _at_least(intensity, Intensity.BOLD):
        # STATED: Thermal with width and heat, drive turned down, dry/wet adjusted.
        # APPROX: blended saturation; DrakoTune has no multiband wavefolder.
        nodes.append(Processor("Saturation", {"drive_db": 5.0, "character": 0.45,
                                              "mix": 0.4, "oversample": 4}))
        # VISIBLE: Polyverse Wider at 10%. STATED: "a little wide but not super
        # crazy wide". APPROX: Wider is a phase/delay-based widener on a mono
        # source; the closest DrakoTune primitive is a very low-level doubler.
        nodes.append(Doubler(
            voices=(DoubleVoice(detune_cents=-5.0, delay_ms=11.0, pan=-0.35),
                    DoubleVoice(detune_cents=+6.0, delay_ms=16.0, pan=+0.35)),
            level=0.10, label="angelomota_wider",
        ))
        # STATED: FabFilter Timeless 2 delay, then a reverb. Values UNKNOWN.
        nodes.append(Send(
            branch=Processor("Delay", {"delay_seconds": 0.11, "feedback": 0.18, "mix": 1.0}),
            level=0.14, duck=0.72, label="angelomota_delay",
        ))
        nodes.append(Send(
            branch=Processor("Reverb", {"room_size": 0.28, "damping": 0.45,
                                        "wet_level": 1.0, "dry_level": 0.0, "width": 0.9}),
            level=0.13, duck=0.8, label="angelomota_verb",
        ))

    if intensity is Intensity.EXTREME:
        nodes.append(Processor("Clipping", {"threshold_db": -3.5}))
    return Serial(nodes)


def _chain_leteveon(intensity: Intensity) -> GraphNode:
    """Video 170615 — @leteveon_, autotune-forward "underground" chain.

    Signature move: BOOSTS 3.2k and 6.4k, and high-passes at 90-115 Hz. This is
    the direct opposite of @angelomota on both counts, which is exactly why the
    two are kept as separate modes.

    Pitch correction is NOT included: this chain's first move is a hard autotune,
    and no mode surfaces pitch correction (see module docstring).
    """
    nodes: list[GraphNode] = [
        # VISIBLE caption: "Noise Gate — use as 1st effect in your preset".
        Processor("NoiseGate", {"threshold_db": -45.0, "attack_ms": 3.0, "release_ms": 180.0}),
        # VISIBLE caption: "Pro Q4: cut at 90 and adjust later"; an alternate
        # caption offers "high pass at 115 instead". 90 taken as the primary.
        Processor("HighpassFilter", {"cutoff_frequency_hz": 90.0}),
        # STATED: "EQ very lightly, less is more."
        Processor("PeakFilter", {"cutoff_frequency_hz": 300.0, "gain_db": -2.0, "q": 1.0}),
        # STATED: compressor "very lightly just to grab the peaks".
        Processor("Compressor", {"threshold_db": -14.0, "ratio": 2.5,
                                 "attack_ms": 5.0, "release_ms": 100.0}),
        # STATED: wideband de-esser mixed around 60%. VISIBLE: threshold -2.4 dB
        # on the plugin, which is its own scale and not DrakoTune's -- INFERRED
        # here as a moderate reduction.
        Processor("DeEsser", {"band_lo_hz": 5000.0, "band_hi_hz": 10000.0,
                              "frame_threshold": 0.18, "max_reduction_db": 6.0}),
    ]

    if _at_least(intensity, Intensity.BALANCED):
        nodes += [
            # STATED: "clean up between 10 to 15K", then a high shelf.
            Processor("PeakFilter", {"cutoff_frequency_hz": 12500.0, "gain_db": -2.5, "q": 0.8}),
            # VISIBLE caption: "high shelf starting around 10k".
            Processor("HighShelfFilter", {"cutoff_frequency_hz": 10000.0,
                                          "gain_db": 3.0, "q": 0.7}),
            # VISIBLE caption: "Graphic EQ — boost 3.2k & 6.4k". This is the
            # band Modern Rap now deliberately avoids; kept verbatim here.
            Processor("PeakFilter", {"cutoff_frequency_hz": 3200.0, "gain_db": 2.5, "q": 1.2}),
            Processor("PeakFilter", {"cutoff_frequency_hz": 6400.0, "gain_db": 2.0, "q": 1.2}),
        ]

    if _at_least(intensity, Intensity.BOLD):
        # VISIBLE: Aphex Exciter. APPROX: harmonic excitement via saturation.
        nodes.append(Processor("Saturation", {"drive_db": 5.0, "character": 0.5,
                                              "mix": 0.45, "oversample": 4}))
        # STATED: delay, then reverb, then a stereo widener.
        nodes.append(Send(
            branch=Processor("Delay", {"delay_seconds": 0.35, "feedback": 0.2, "mix": 1.0}),
            level=0.16, duck=0.7, label="leteveon_delay",
        ))
        nodes.append(Send(
            branch=Processor("Reverb", {"room_size": 0.35, "damping": 0.4,
                                        "wet_level": 1.0, "dry_level": 0.0, "width": 1.0}),
            level=0.18, duck=0.75, label="leteveon_verb",
        ))
        # STATED: "stereo whitener" [widener]. APPROX as a doubler, as above.
        nodes.append(Doubler(
            voices=(DoubleVoice(detune_cents=-7.0, delay_ms=14.0, pan=-0.5),
                    DoubleVoice(detune_cents=+8.0, delay_ms=20.0, pan=+0.5)),
            level=0.18, label="leteveon_wide",
        ))

    if intensity is Intensity.EXTREME:
        nodes.append(Processor("Clipping", {"threshold_db": -3.0}))
    return Serial(nodes)


def _chain_mixedbytra(intensity: Intensity) -> GraphNode:
    """Video 170828 — @mixedbytra, lead vocal chain for YNW Melly "772".

    Signature move: restraint. The creator states he was pleased to reopen the
    session and find he "didn't do much". Frames also reveal a parallel duplicate
    track the narration never mentions.

    This chain carries the only fully VISIBLE compressor settings in the corpus.
    """
    nodes: list[GraphNode] = [
        # STATED: Metric Halo ChannelStrip EQ, "took out all the bad frequencies,
        # all that muddiness". VISIBLE: a high-pass and low-mid dips in the EQ
        # transfer curve; exact frequencies UNKNOWN at frame resolution.
        Processor("HighpassFilter", {"cutoff_frequency_hz": 85.0}),
        Processor("PeakFilter", {"cutoff_frequency_hz": 300.0, "gain_db": -3.0, "q": 1.1}),
        # STATED: SSL E Series channel strip EQ next. VISIBLE: UAD SSL E, but
        # its knob values are not legible. Rendered as a gentle presence lift.
        Processor("PeakFilter", {"cutoff_frequency_hz": 2000.0, "gain_db": 1.5, "q": 0.9}),
        # VISIBLE, exact: Waves R-COMP — Thresh -19.7, Ratio 3.79, Gain +2.4.
        # The only compressor in the corpus whose settings are directly readable.
        Processor("Compressor", {"threshold_db": -19.7, "ratio": 3.79,
                                 "attack_ms": 12.0, "release_ms": 160.0}),
        Processor("Gain", {"gain_db": 2.4}),
        # STATED: de-esser next. Values UNKNOWN.
        Processor("DeEsser", {"band_lo_hz": 5000.0, "band_hi_hz": 9500.0,
                              "frame_threshold": 0.2, "max_reduction_db": 5.0}),
    ]

    if _at_least(intensity, Intensity.BALANCED):
        # STATED + VISIBLE: Pultec EQP-1A last, "looks like we did a smiley face".
        # A Pultec smiley is a low boost and a high boost together.
        nodes += [
            Processor("LowShelfFilter", {"cutoff_frequency_hz": 100.0,
                                         "gain_db": 2.5, "q": 0.7}),
            Processor("HighShelfFilter", {"cutoff_frequency_hz": 10000.0,
                                          "gain_db": 3.0, "q": 0.7}),
        ]

    if _at_least(intensity, Intensity.BOLD):
        # VISIBLE in the mixer, never narrated: a parallel duplicate track
        # ("PARA.dup1") carrying a Fairchild 670 and a reverb, summed under the
        # lead. APPROX: Fairchild character as heavy compression + saturation.
        nodes.append(Parallel(
            branch=Serial([
                Processor("Compressor", {"threshold_db": -30.0, "ratio": 8.0,
                                         "attack_ms": 4.0, "release_ms": 200.0}),
                Processor("Saturation", {"drive_db": 5.0, "character": 0.3,
                                         "mix": 0.6, "oversample": 4}),
            ]),
            blend=0.3, label="tra_parallel",
        ))
        nodes.append(Send(
            branch=Processor("Reverb", {"room_size": 0.25, "damping": 0.5,
                                        "wet_level": 1.0, "dry_level": 0.0, "width": 0.85}),
            level=0.12, duck=0.8, label="tra_verb",
        ))

    if intensity is Intensity.EXTREME:
        nodes.append(Processor("Clipping", {"threshold_db": -4.0}))
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
            "dynamic low-mid control",
            "measured resonance suppression (not dereverberation)",
            "sibilance control",
            "phrase-level level riding",
            "parallel density with oversampled saturation",
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
            "phrase-level level riding",
            "serial two-stage compression",
            "dynamic harshness control",
            "parallel density with oversampled saturation",
            "presence and air",
            "ducked slap delay",
            "ducked short room",
            "artificial doubling (detuned copies, not a second take)",
        ),
        build=_modern_rap,
    ),
    # --- DT-108 experimental challengers, one creator each -------------------
    "challenger_angelomota": ModeSpec(
        name="challenger_angelomota",
        title="Challenger — Angelomota (experimental)",
        summary="Video-derived: cuts 2.5-5 kHz, boosts only outside it. Not validated.",
        capabilities=(
            "gate (visible settings)",
            "subtractive EQ at 80 Hz, 350 Hz, 1 kHz, 3.5 kHz",
            "two serial compressors (4:1 then 6:1)",
            "additive EQ at 1.2k, 1.7k, 8k",
            "compressor-plus-saturation stand-in for a Distressor",
            "high shelf stand-in for a spectral exciter (NOT the same process)",
            "low-level doubling stand-in for a stereo widener",
            "ducked delay and room",
        ),
        build=_chain_angelomota,
    ),
    "challenger_leteveon": ModeSpec(
        name="challenger_leteveon",
        title="Challenger — Leteveon (experimental)",
        summary="Video-derived: boosts 3.2k and 6.4k, high-passes at 90 Hz. Not validated.",
        capabilities=(
            "gate first in chain",
            "90 Hz high-pass",
            "light peak-catching compression",
            "wideband de-essing",
            "10-15 kHz cleanup then 10 kHz shelf",
            "3.2 kHz and 6.4 kHz boosts",
            "saturation stand-in for an Aphex exciter",
            "ducked delay and room, doubling stand-in for a widener",
        ),
        build=_chain_leteveon,
    ),
    "challenger_mixedbytra": ModeSpec(
        name="challenger_mixedbytra",
        title="Challenger — Mixedbytra (experimental)",
        summary="Video-derived: restrained chain with the corpus's only visible compressor values.",
        capabilities=(
            "high-pass and low-mid cut",
            "gentle presence lift",
            "compression at directly observed settings (-19.7, 3.79:1, +2.4 dB)",
            "de-essing",
            "Pultec-style low and high shelf pair",
            "parallel density stand-in for a Fairchild duplicate track",
            "ducked room",
        ),
        build=_chain_mixedbytra,
    ),
}


# DT-108 challengers are reachable but are NOT production modes. They are single-
# creator reconstructions from instructional video, unvalidated by listening, and
# they must never be presented as equivalent to the three shipped chains.
EXPERIMENTAL_MODES: frozenset[str] = frozenset({
    "challenger_angelomota", "challenger_leteveon", "challenger_mixedbytra",
})


def list_modes() -> tuple[str, ...]:
    return tuple(MODES)


def production_modes() -> tuple[str, ...]:
    """The shipped chains, excluding experimental challengers."""
    return tuple(m for m in MODES if m not in EXPERIMENTAL_MODES)


def is_experimental(name: str) -> bool:
    return name in EXPERIMENTAL_MODES


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
