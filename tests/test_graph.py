"""Graph routing tests (DT-94).

The load-bearing test here is `test_serial_graph_matches_flat_executor`: the flat
M09 path is the shipped behavior, and adding topology must not silently change
what existing users already get.
"""

import numpy as np
import pytest

from src.dsp_engine.channels import channel_count, normalize, to_stereo
from src.dsp_engine.executor import execute_plan
from src.dsp_engine.graph import (
    Parallel,
    Processor,
    Send,
    Serial,
    render_graph,
)
from src.shared_types import ProcessingAction, ProcessingPlan

SR = 44100


def _vocalish(seconds=0.5, sr=SR):
    """A tone with an amplitude envelope — enough structure to exercise ducking."""
    t = np.arange(int(sr * seconds), dtype=np.float32) / sr
    tone = 0.4 * np.sin(2 * np.pi * 180.0 * t) + 0.2 * np.sin(2 * np.pi * 540.0 * t)
    env = np.clip(np.sin(2 * np.pi * 2.0 * t), 0, 1) ** 2
    return (tone * env).astype(np.float32)


def _rms(a):
    return float(np.sqrt(np.mean(np.square(a, dtype=np.float64)))) if a.size else 0.0


def test_serial_graph_matches_flat_executor():
    """A single-branch graph must equal the pre-V3 flat path exactly."""
    audio = _vocalish()
    actions = [
        ProcessingAction(id="a1", objective_id="o1", processor="HighpassFilter",
                         parameters={"cutoff_frequency_hz": 90.0}),
        ProcessingAction(id="a2", objective_id="o2", processor="PeakFilter",
                         parameters={"cutoff_frequency_hz": 300.0, "gain_db": -4.0, "q": 1.2}),
    ]
    plan = ProcessingPlan(id="p1", objectives=(), actions=tuple(actions))
    flat, _ = execute_plan(audio, SR, plan, apply_output_safety=False)

    graph = Serial([Processor(a.processor, a.parameters, a.objective_id) for a in actions])
    graphed = render_graph(audio, SR, graph)

    assert graphed.shape == normalize(flat).shape
    np.testing.assert_allclose(graphed, normalize(flat), atol=1e-6)


def test_array_processor_matches_flat_path_on_mono():
    """DeEsser is a mono kernel; per-channel mapping must not change mono output."""
    audio = _vocalish()
    params = {"band_lo_hz": 5000.0, "band_hi_hz": 9000.0,
              "frame_threshold": 0.2, "max_reduction_db": 6.0}
    plan = ProcessingPlan(
        id="p2",
        objectives=(),
        actions=(ProcessingAction(id="a1", objective_id="o", processor="DeEsser",
                                  parameters=params),),
    )
    flat, _ = execute_plan(audio, SR, plan, apply_output_safety=False)
    graphed = render_graph(audio, SR, Processor("DeEsser", params))
    np.testing.assert_allclose(graphed, normalize(flat), atol=1e-6)


def test_array_processor_preserves_stereo():
    """The old executor dropped the right channel here; the graph must not."""
    stereo = to_stereo(normalize(_vocalish()))
    stereo[:, 1] *= 0.5  # make the channels distinguishable
    out = render_graph(stereo, SR, Processor(
        "DeEsser", {"band_lo_hz": 5000.0, "band_hi_hz": 9000.0,
                    "frame_threshold": 0.2, "max_reduction_db": 6.0}))
    assert channel_count(out) == 2
    assert not np.allclose(out[:, 0], out[:, 1])


def test_unknown_processor_is_passthrough_not_crash():
    audio = _vocalish()
    out = render_graph(audio, SR, Processor("NoSuchProcessor", {}))
    np.testing.assert_allclose(out, normalize(audio), atol=1e-6)


def test_parameters_are_clamped_to_safe_ranges():
    """Graph nodes inherit the registry's bounds; topology is not an escape hatch."""
    audio = _vocalish()
    insane = render_graph(audio, SR, Processor("Distortion", {"drive_db": 500.0}))
    bounded = render_graph(audio, SR, Processor("Distortion", {"drive_db": 24.0}))
    np.testing.assert_allclose(insane, bounded, atol=1e-6)


def test_parallel_blend_endpoints():
    audio = _vocalish()
    branch = Processor("Gain", {"gain_db": -12.0})
    dry_only = render_graph(audio, SR, Parallel(branch=branch, blend=0.0))
    np.testing.assert_allclose(dry_only, normalize(audio), atol=1e-6)

    wet_only = render_graph(audio, SR, Parallel(branch=branch, blend=1.0))
    expected = render_graph(audio, SR, branch)
    np.testing.assert_allclose(wet_only, expected, atol=1e-6)


def test_parallel_compression_reduces_crest_factor():
    """The measurable point of parallel compression: narrow the peak-to-average gap.

    Overall RMS is NOT the property to assert — blending in an attenuated branch
    can lower it. What parallel compression actually does is bring quiet detail up
    relative to peaks, which shows up as a lower crest factor.
    """
    audio = _vocalish()
    crushed = Serial([
        Processor("Compressor", {"threshold_db": -35.0, "ratio": 10.0,
                                 "attack_ms": 2.0, "release_ms": 100.0}),
        Processor("Gain", {"gain_db": 6.0}),
    ])
    out = render_graph(audio, SR, Parallel(branch=crushed, blend=0.5))
    dry = normalize(audio)

    def crest(a):
        return float(np.max(np.abs(a))) / max(_rms(a), 1e-12)

    assert crest(out) < crest(dry)
    assert not np.allclose(out, dry, atol=1e-4)


def test_send_preserves_dry_at_zero_level():
    audio = _vocalish()
    send = Send(branch=Processor("Reverb", {"wet_level": 1.0, "dry_level": 0.0}), level=0.0)
    out = render_graph(audio, SR, send)
    dry = normalize(audio)
    np.testing.assert_allclose(out[: dry.shape[0]], dry, atol=1e-6)


def test_send_adds_energy_on_top_of_dry():
    """A send adds to the dry signal; it does not replace it (that is Parallel)."""
    audio = _vocalish()
    send = Send(branch=Processor("Reverb", {"room_size": 0.7, "wet_level": 1.0,
                                            "dry_level": 0.0}), level=0.4)
    out = render_graph(audio, SR, send)
    assert _rms(out) > _rms(normalize(audio))


def test_ducking_reduces_wet_relative_to_undercked():
    """Ducking must measurably pull the effect down under the dry signal."""
    audio = _vocalish()
    branch = Processor("Reverb", {"room_size": 0.7, "wet_level": 1.0, "dry_level": 0.0})
    plain = render_graph(audio, SR, Send(branch=branch, level=0.5, duck=0.0))
    ducked = render_graph(audio, SR, Send(branch=branch, level=0.5, duck=0.9))
    dry = normalize(audio)
    n = min(plain.shape[0], ducked.shape[0], dry.shape[0])
    assert _rms(ducked[:n] - dry[:n]) < _rms(plain[:n] - dry[:n])


def test_ducking_gain_is_smooth():
    """A stepped gain would click. Bound the per-sample change."""
    from src.dsp_engine.graph import _ducking_gain
    audio = normalize(_vocalish())
    gain = _ducking_gain(audio, SR, 0.9)
    assert gain.shape[0] == audio.shape[0]
    assert float(np.max(np.abs(np.diff(gain)))) < 0.05


def test_nested_topology_renders():
    """Sends wrapping parallel branches — the shape a real mode chain takes."""
    audio = _vocalish()
    graph = Serial([
        Processor("HighpassFilter", {"cutoff_frequency_hz": 80.0}),
        Parallel(branch=Processor("Compressor", {"threshold_db": -30.0, "ratio": 8.0,
                                                 "attack_ms": 3.0, "release_ms": 120.0}),
                 blend=0.35),
        Send(branch=Processor("Delay", {"delay_seconds": 0.15, "feedback": 0.25, "mix": 1.0}),
             level=0.2, duck=0.6),
    ])
    out = render_graph(audio, SR, graph)
    assert np.all(np.isfinite(out))
    assert out.shape[0] >= normalize(audio).shape[0]


def test_describe_reports_topology():
    graph = Serial([
        Processor("HighpassFilter", {"cutoff_frequency_hz": 80.0}),
        Send(branch=Processor("Reverb", {}), level=0.3, duck=0.5, label="verb"),
    ])
    text = graph.describe()
    assert "HighpassFilter" in text and "verb" in text and "duck" in text


def test_empty_serial_is_passthrough():
    audio = _vocalish()
    np.testing.assert_allclose(render_graph(audio, SR, Serial([])), normalize(audio), atol=1e-6)


@pytest.mark.parametrize("name", [
    "LowShelfFilter", "LowpassFilter", "Reverb", "Delay",
    "Distortion", "Clipping", "Chorus", "PitchShift",
])
def test_every_new_primitive_renders_and_changes_signal(name):
    """Wired-up-but-inert is the failure mode this catches."""
    demo = {
        "LowShelfFilter": {"cutoff_frequency_hz": 200.0, "gain_db": 6.0, "q": 0.7},
        "LowpassFilter": {"cutoff_frequency_hz": 3000.0},
        "Reverb": {"room_size": 0.6, "wet_level": 0.5, "dry_level": 0.5},
        "Delay": {"delay_seconds": 0.2, "feedback": 0.3, "mix": 0.5},
        "Distortion": {"drive_db": 15.0},
        "Clipping": {"threshold_db": -15.0},
        "Chorus": {"rate_hz": 1.2, "depth": 0.5, "centre_delay_ms": 10.0, "mix": 0.5},
        "PitchShift": {"semitones": -4.0},
    }[name]
    audio = _vocalish()
    out = render_graph(audio, SR, Processor(name, demo))
    assert np.all(np.isfinite(out))
    dry = normalize(audio)
    n = min(out.shape[0], dry.shape[0])
    assert _rms(out[:n] - dry[:n]) > 1e-4, f"{name} rendered but changed nothing"


# ---------------------------------------------------------------------------
# DT-98 — artificial doubling
# ---------------------------------------------------------------------------

def _voiced(sr=44100, seconds=1.5, f0=170.0):
    """A crude voiced signal: harmonics with vibrato and an amplitude envelope."""
    t = np.arange(int(sr * seconds)) / sr
    vib = 1.0 + 0.004 * np.sin(2 * np.pi * 5.0 * t)
    sig = sum(a * np.sin(2 * np.pi * f0 * k * t * vib)
              for k, a in ((1, 0.6), (2, 0.3), (3, 0.15), (4, 0.08)))
    env = 0.5 * (1 + np.sin(2 * np.pi * 2.0 * t - np.pi / 2))
    return (0.3 * sig * env).astype(np.float32)


def test_doubler_widens_mono_to_stereo():
    from src.dsp_engine.graph import DoubleVoice, Doubler
    sr = 44100
    node = Doubler(voices=(DoubleVoice(-9.0, 17.0, -0.7), DoubleVoice(11.0, 25.0, 0.7)),
                   level=0.4)
    out = render_graph(_voiced(sr), sr, node)
    assert out.shape[1] == 2, "doubling must produce a stereo image"
    assert not np.allclose(out[:, 0], out[:, 1]), "channels are identical — no width"


def test_doubler_stays_mono_compatible():
    """A double that cancels when summed to mono is a bug, not a feature."""
    from src.dsp_engine.channels import mono_compatibility
    from src.dsp_engine.graph import DoubleVoice, Doubler
    sr = 44100
    node = Doubler(voices=(DoubleVoice(-9.0, 17.0, -0.7), DoubleVoice(11.0, 25.0, 0.7)),
                   level=0.4)
    compat = mono_compatibility(render_graph(_voiced(sr), sr, node))
    assert not compat.collapses, compat.to_dict()
    assert compat.correlation > 0.0


def test_doubler_with_no_voices_is_a_passthrough():
    from src.dsp_engine.graph import Doubler
    sr = 44100
    x = _voiced(sr)
    out = render_graph(x, sr, Doubler(voices=(), level=0.5))
    assert np.array_equal(out, normalize(x))


def test_doubler_level_zero_is_a_passthrough():
    from src.dsp_engine.graph import DoubleVoice, Doubler
    sr = 44100
    x = _voiced(sr)
    node = Doubler(voices=(DoubleVoice(-9.0, 17.0, -0.7),), level=0.0)
    assert np.array_equal(render_graph(x, sr, node), normalize(x))


def test_doubler_pulls_a_comb_filtering_delay_up_to_the_floor():
    """An authored 2 ms 'double' would thin the dry signal, so it is raised."""
    from src.dsp_engine.graph import _DOUBLE_MIN_DELAY_MS, DoubleVoice, Doubler
    sr = 44100
    x = _voiced(sr)
    tiny = render_graph(x, sr, Doubler(voices=(DoubleVoice(0.0, 2.0, 0.0),), level=0.5))
    floored = render_graph(
        x, sr, Doubler(voices=(DoubleVoice(0.0, _DOUBLE_MIN_DELAY_MS, 0.0),), level=0.5))
    assert np.allclose(tiny, floored)


def test_doubler_adding_a_voice_does_not_raise_the_double_level():
    """Voices are averaged, so a third double widens rather than getting louder."""
    from src.dsp_engine.graph import DoubleVoice, Doubler
    sr = 44100
    x = _voiced(sr)
    two = render_graph(x, sr, Doubler(
        voices=(DoubleVoice(-9.0, 17.0, -0.7), DoubleVoice(11.0, 25.0, 0.7)), level=0.4))
    three = render_graph(x, sr, Doubler(
        voices=(DoubleVoice(-9.0, 17.0, -0.7), DoubleVoice(11.0, 25.0, 0.7),
                DoubleVoice(5.0, 31.0, 0.0)), level=0.4))
    peak_two = float(np.max(np.abs(two)))
    peak_three = float(np.max(np.abs(three)))
    assert peak_three <= peak_two * 1.25, (peak_two, peak_three)


def test_doubler_describe_names_detune_not_tuning():
    """DT-98 ships transposition only; the description must not imply correction."""
    from src.dsp_engine.graph import DoubleVoice, Doubler
    text = Doubler(voices=(DoubleVoice(-9.0, 17.0, -0.7),), level=0.4).describe().lower()
    assert "-9c" in text
    for forbidden in ("tune", "tuning", "correct", "pitch correction"):
        assert forbidden not in text


def test_modern_rap_bold_includes_doubling_and_declares_it_honestly():
    from src.modes.contracts import MODES, build_graph
    description = build_graph("modern_rap", "bold").describe()
    assert "rap_double" in description
    assert "rap_double" not in build_graph("modern_rap", "subtle").describe()
    caps = " ".join(MODES["modern_rap"].capabilities).lower()
    assert "doubling" in caps
    assert "not a second take" in caps       # the honest qualifier must survive
    assert "auto-tune" not in caps and "pitch correction" not in caps
