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
