"""A/B guard for defaulting to the v2 engine (M19).

Justifies making v2 the CLI default: for every fixture, v2 output is safe (no
added clipping, no loudness inflation, in-range peaks) and it achieves its
targeted objective where it has one. It does NOT require v2 to out-cut the
legacy chain — only to be safe and effective.
"""

import numpy as np
import pytest

from fixtures import list_fixtures, load_fixture
from fixtures.loader import AUDIO_DIR
from src.diagnostics import measure_loudness, measure_safety
from src.dsp_engine import execute_plan
from src.orchestration import analyze_and_plan

OUTPUT_CLIP_MAX = 0.001


def _mono(a: np.ndarray) -> np.ndarray:
    return a[:, 0] if a.ndim > 1 else a


def _v2_output(name: str) -> tuple[np.ndarray, int]:
    fx = load_fixture(name)
    bundle = analyze_and_plan(str(AUDIO_DIR / f"{name}.wav"))
    out, _ = execute_plan(fx.audio, fx.sample_rate, bundle.plan)
    return _mono(out), fx.sample_rate


def _clip(a: np.ndarray, sr: int) -> float:
    return {o.metric: o.value for o in measure_safety(a, sr)[0]}["clipping_ratio"]


def _rms_dbfs(a: np.ndarray, sr: int) -> float:
    return {o.metric: o.value for o in measure_loudness(a, sr)[0]}["rms_dbfs"]


def _harsh_energy(a: np.ndarray, sr: int) -> float:
    fft = np.fft.rfft(a)
    freqs = np.fft.rfftfreq(len(a), 1.0 / sr)
    mask = (freqs >= 2500) & (freqs <= 6000)
    return float(np.sum(np.abs(fft[mask]) ** 2))


@pytest.mark.parametrize("name", sorted(list_fixtures()))
def test_v2_output_is_safe(name):
    out, sr = _v2_output(name)
    assert np.all(np.isfinite(out))
    assert float(np.max(np.abs(out))) <= 1.0
    assert _clip(out, sr) <= OUTPUT_CLIP_MAX


@pytest.mark.parametrize("name", sorted(list_fixtures()))
def test_v2_does_not_add_clipping(name):
    out, sr = _v2_output(name)
    fx = load_fixture(name)
    assert _clip(out, sr) <= _clip(_mono(fx.audio), sr) + OUTPUT_CLIP_MAX


@pytest.mark.parametrize("name", sorted(list_fixtures()))
def test_v2_does_not_inflate_energy(name):
    # v2 only cuts/gates and attenuates on output — it never adds makeup gain,
    # so RMS energy must not rise (guards the M19 makeup-limiter fix). Peaks may
    # shift from EQ phase; energy is the honest "not louder" measure.
    out, sr = _v2_output(name)
    fx = load_fixture(name)
    assert _rms_dbfs(out, sr) <= _rms_dbfs(_mono(fx.audio), sr) + 0.5


def test_v2_reduces_harshness_on_harsh_fixture():
    out, sr = _v2_output("harsh")
    fx = load_fixture("harsh")
    assert _harsh_energy(out, sr) < _harsh_energy(_mono(fx.audio), sr)


def test_v2_mitigates_clipped_input():
    out, sr = _v2_output("clipped")
    fx = load_fixture("clipped")
    # Severe clipping is heavily mitigated by the output-safety limiter.
    assert _clip(out, sr) < _clip(_mono(fx.audio), sr)
