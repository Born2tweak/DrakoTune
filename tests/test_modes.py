"""Mode contract and distinctness tests (DT-95).

The gate that matters here is distinctness: the pre-V3 engine shipped two
"modes" whose entire difference was one gentle compressor. A renamed preset must
fail these tests.
"""

import numpy as np
import pytest

from src.dsp_engine.channels import normalize
from src.dsp_engine.graph import Parallel, Send, Serial, render_graph
from src.modes import (
    INTENSITY_ORDER,
    Intensity,
    build_graph,
    describe_mode,
    get_mode,
    list_modes,
)
from src.modes.distinctness import (
    AUDIBLE_DELTA_FLOOR_DB,
    compare_all,
    compare_modes,
    difference_db,
)

SR = 44100
CEILING = 10.0 ** (-0.2 / 20.0)


def _vocalish(seconds=1.5, sr=SR):
    """Broadband, enveloped signal — has content in every band a mode touches."""
    rng = np.random.default_rng(11)
    t = np.arange(int(sr * seconds), dtype=np.float32) / sr
    harmonics = sum(
        (0.4 / k) * np.sin(2 * np.pi * 150.0 * k * t) for k in range(1, 12)
    ).astype(np.float32)
    breath = (rng.normal(0, 0.02, t.shape)).astype(np.float32)
    env = np.clip(np.sin(2 * np.pi * 1.5 * t), 0, 1) ** 1.5
    return ((harmonics + breath) * env * 0.5).astype(np.float32)


def _rms(a):
    return float(np.sqrt(np.mean(np.square(a, dtype=np.float64)))) if a.size else 0.0


def test_expected_modes_exist():
    assert set(list_modes()) == {"natural", "rescue", "modern_rap"}


@pytest.mark.parametrize("mode", list(list_modes()))
@pytest.mark.parametrize("intensity", list(INTENSITY_ORDER))
def test_every_mode_and_intensity_renders_safely(mode, intensity):
    audio = _vocalish()
    out = render_graph(audio, SR, build_graph(mode, intensity))
    assert np.all(np.isfinite(out)), f"{mode}/{intensity.value} produced non-finite samples"
    # Sends add tails; duration may grow but must never shrink.
    assert out.shape[0] >= normalize(audio).shape[0]
    # Never gates the performance away.
    assert _rms(out) > _rms(normalize(audio)) * 0.1


@pytest.mark.parametrize("mode", list(list_modes()))
def test_intensity_changes_topology_not_just_numbers(mode):
    """Subtle and Bold must differ in graph shape, not only parameter values."""
    subtle = describe_mode(mode, Intensity.SUBTLE)
    bold = describe_mode(mode, Intensity.BOLD)
    assert subtle != bold
    assert len(bold) > len(subtle), f"{mode}: Bold added no nodes over Subtle"


def test_bold_adds_parallel_and_send_branches():
    """The topologies that make a vocal sound produced only appear at Bold+."""
    for mode in ("rescue", "modern_rap"):
        subtle_text = describe_mode(mode, Intensity.SUBTLE)
        bold_text = describe_mode(mode, Intensity.BOLD)
        assert "parallel" not in subtle_text and "send" not in subtle_text.lower()
        assert "density" in bold_text  # parallel bus
        assert "duck" in bold_text     # ducked send


def test_natural_stays_conservative_at_bold():
    """Natural is the honest baseline; it must not grow a parallel bus or sends."""
    text = describe_mode("natural", Intensity.BOLD)
    assert "density" not in text
    assert "duck" not in text


@pytest.mark.parametrize("intensity", [Intensity.BALANCED, Intensity.BOLD])
def test_all_mode_pairs_are_distinct(intensity):
    audio = _vocalish()
    for result in compare_all(list(list_modes()), audio, SR, intensity):
        assert result.structural, f"{result.mode_a} and {result.mode_b} share a topology"
        assert result.audible, (
            f"{result.mode_a} vs {result.mode_b} at {intensity.value}: "
            f"{result.delta_db:.2f} dB is below the {AUDIBLE_DELTA_FLOOR_DB} dB floor"
        )


def test_identical_modes_would_fail_the_gate():
    """Sensitivity check: the gate must reject a mode compared against itself."""
    audio = _vocalish()
    result = compare_modes("rescue", "rescue", audio, SR, Intensity.BOLD)
    assert not result.structural
    assert not result.distinct


def test_distinctness_ignores_pure_gain_changes():
    """A louder copy is not a different mode. Level matching must neutralise it."""
    audio = normalize(_vocalish())
    assert difference_db(audio, audio * 0.5) < AUDIBLE_DELTA_FLOOR_DB


def test_distinctness_detects_real_processing():
    audio = _vocalish()
    filtered = render_graph(audio, SR, build_graph("modern_rap", Intensity.BOLD))
    assert difference_db(audio, filtered) > AUDIBLE_DELTA_FLOOR_DB


def test_capabilities_do_not_claim_absent_features():
    """Honest-naming contract: no mode may advertise what the engine cannot do."""
    banned = ("denois", "dereverb", "auto-tune", "autotune", "pitch correction",
              "plate", "professional", "studio-quality", "mastering")
    for mode in list_modes():
        spec = get_mode(mode)
        text = " ".join((spec.title, spec.summary) + spec.capabilities).lower()
        for word in banned:
            if word == "denois" and "not broadband denoising" in text:
                continue  # explicit disclaimer, not a claim
            if word == "dereverb" and "not dereverberation" in text:
                continue
            assert word not in text, f"{mode} claims {word!r}"


def test_no_mode_uses_pitchshift_as_tuning():
    """PitchShift is transposition. Until DT-100 no mode may use it at all."""
    for mode in list_modes():
        for intensity in INTENSITY_ORDER:
            assert "PitchShift" not in describe_mode(mode, intensity)


def test_unknown_mode_raises_with_available_list():
    with pytest.raises(KeyError, match="unknown mode"):
        build_graph("nonexistent")


def test_default_intensity_is_used_when_unspecified():
    assert describe_mode("rescue") == describe_mode("rescue", Intensity.BOLD)
    assert describe_mode("natural") == describe_mode("natural", Intensity.BALANCED)


def test_intensity_accepts_string():
    assert describe_mode("rescue", "bold") == describe_mode("rescue", Intensity.BOLD)


@pytest.mark.parametrize("mode", list(list_modes()))
def test_mode_graphs_are_serial_at_top_level(mode):
    graph = build_graph(mode, Intensity.BOLD)
    assert isinstance(graph, Serial)
    assert graph.nodes, f"{mode} built an empty chain"


def test_bold_chains_contain_expected_node_types():
    graph = build_graph("modern_rap", Intensity.BOLD)
    kinds = {type(n) for n in graph.nodes}
    assert Parallel in kinds, "Modern Rap Bold has no parallel bus"
    assert Send in kinds, "Modern Rap Bold has no send"
