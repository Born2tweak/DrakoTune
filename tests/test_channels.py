"""Channel contract tests (DT-94).

The contract exists because the engine was mono by accident: preprocess forced
mono and the executor's array path collapsed to channel 0. Anything that widened
the signal was discarded before export. These tests pin the behavior that makes
width possible and detectable.
"""

import numpy as np
import pytest

from src.dsp_engine.channels import (
    MONO,
    STEREO,
    align_for_mix,
    channel_count,
    is_mono,
    match_channels,
    mono_compatibility,
    normalize,
    pan,
    to_mono,
    to_stereo,
)

SR = 44100


def _tone(freq=220.0, seconds=0.25, sr=SR):
    t = np.arange(int(sr * seconds), dtype=np.float32) / sr
    return (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_normalize_accepts_1d_and_returns_column():
    out = normalize(_tone())
    assert out.ndim == 2 and out.shape[1] == MONO
    assert out.dtype == np.float32


def test_normalize_transposes_pedalboard_layout():
    """pedalboard emits (channels, samples); ours is (samples, channels)."""
    pb_style = np.zeros((2, 1000), dtype=np.float32)
    out = normalize(pb_style)
    assert out.shape == (1000, 2)


def test_normalize_rejects_more_than_stereo():
    with pytest.raises(ValueError, match="unsupported channel count"):
        normalize(np.zeros((1000, 5), dtype=np.float32))


def test_to_stereo_then_to_mono_round_trips():
    mono = normalize(_tone())
    assert np.allclose(to_mono(to_stereo(mono)), mono, atol=1e-6)


def test_to_mono_averages_rather_than_sums():
    """Summing would clip a correlated pair; averaging preserves level."""
    mono = normalize(_tone())
    stereo = to_stereo(mono)
    assert float(np.max(np.abs(to_mono(stereo)))) <= float(np.max(np.abs(mono))) + 1e-6


def test_match_channels_both_directions():
    mono = normalize(_tone())
    assert channel_count(match_channels(mono, STEREO)) == STEREO
    assert channel_count(match_channels(to_stereo(mono), MONO)) == MONO


def test_align_for_mix_pads_to_longest_and_widest():
    """A reverb tail must not be truncated by a shorter dry branch."""
    short_mono = normalize(_tone(seconds=0.1))
    long_stereo = to_stereo(normalize(_tone(seconds=0.3)))
    a, b = align_for_mix(short_mono, long_stereo)
    assert a.shape == b.shape
    assert a.shape[0] == long_stereo.shape[0]
    assert a.shape[1] == STEREO


def test_pan_is_constant_power():
    """Centre must not dip ~3 dB the way linear panning does."""
    mono = normalize(_tone())
    centre = pan(mono, 0.0)
    total = np.sqrt(np.mean(centre[:, 0] ** 2) + np.mean(centre[:, 1] ** 2))
    reference = np.sqrt(np.mean(mono[:, 0] ** 2))
    assert total == pytest.approx(reference, rel=0.02)


def test_pan_extremes_are_hard():
    mono = normalize(_tone())
    left = pan(mono, -1.0)
    assert float(np.max(np.abs(left[:, 1]))) < 1e-6
    right = pan(mono, 1.0)
    assert float(np.max(np.abs(right[:, 0]))) < 1e-6


def test_mono_input_is_trivially_compatible():
    compat = mono_compatibility(normalize(_tone()))
    assert compat.channels == MONO
    assert compat.correlation == 1.0
    assert not compat.collapses


def test_phase_inverted_stereo_is_flagged():
    """The failure this check exists for: a 'wide' vocal that vanishes in mono."""
    mono = _tone()
    inverted = np.stack([mono, -mono], axis=1)
    compat = mono_compatibility(inverted)
    assert compat.correlation < 0
    assert compat.collapses


def test_duplicated_stereo_is_not_flagged():
    compat = mono_compatibility(to_stereo(normalize(_tone())))
    assert compat.correlation == pytest.approx(1.0, abs=1e-6)
    assert not compat.collapses


def test_uncorrelated_stereo_is_allowed():
    """~3 dB loss from averaging two uncorrelated channels is expected, not a failure."""
    rng = np.random.default_rng(7)
    stereo = rng.normal(0, 0.2, size=(SR // 4, 2)).astype(np.float32)
    assert not mono_compatibility(stereo).collapses


def test_is_mono_helper():
    assert is_mono(_tone())
    assert not is_mono(to_stereo(normalize(_tone())))
