"""HumNotch processor + strictly gated promotion tests (M28)."""

import numpy as np
import pytest
import soundfile as sf

from fixtures.degradations import STANDARD_GRID, apply_recipe
from src.diagnostics.advisory import measure_advisory, promoted_hum_interpretation
from src.dsp_engine import execute_plan
from src.dsp_engine.processors import PROCESSORS, clamp_params
from src.orchestration import analyze_and_plan

SR = 44100


def _voice(seconds=4.0):
    n = int(SR * seconds)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, amp in enumerate((1.0, 0.5, 0.33, 0.2), start=1):
        x += amp * np.sin(2 * np.pi * 220.0 * k * t)
    envelope = np.zeros(n)
    for start_s, dur_s in ((0.10, 0.85), (1.15, 0.60), (2.05, 1.10), (3.40, 0.45)):
        i, m = int(start_s * SR), int(dur_s * SR)
        envelope[i:i + m] = np.maximum(envelope[i:i + m], np.hanning(m))
    x *= envelope * (0.6 + 0.4 * np.sin(2 * np.pi * 2.3 * t) ** 2)
    x *= 0.25 / max(np.max(np.abs(x)), 1e-9)
    return x.astype(np.float32)


def _recipe(rid):
    return next(r for r in STANDARD_GRID if r.id == rid)


def _band_energy(x, lo, hi):
    spectrum = np.abs(np.fft.rfft(x.astype(np.float64))) ** 2
    freqs = np.fft.rfftfreq(len(x), 1.0 / SR)
    return float(np.sum(spectrum[(freqs >= lo) & (freqs <= hi)]))


def test_promotion_gate_fires_on_strong_hum_not_on_clean():
    clean_obs, _ = measure_advisory(_voice(), SR)
    assert promoted_hum_interpretation(clean_obs) is None
    hummed = apply_recipe(_voice(), SR, _recipe("hum_strong"))
    hum_obs, _ = measure_advisory(hummed, SR)
    promoted = promoted_hum_interpretation(hum_obs)
    assert promoted is not None and promoted.issue == "hum_confirmed"


def test_hum_notch_spec_clamps():
    params, clamped = clamp_params("HumNotch", {"base_hz": 60.0, "gain_db": -40.0,
                                                "q": 100.0, "harmonics": 9})
    assert params["gain_db"] == -15.0 and params["q"] == 12.0 and params["harmonics"] == 3
    assert set(clamped) == {"gain_db", "q", "harmonics"}


def test_end_to_end_hum_reduction(tmp_path):
    hummed = apply_recipe(_voice(), SR, _recipe("hum_strong"))
    src = tmp_path / "hummed.wav"
    sf.write(src, hummed, SR, subtype="PCM_16")

    bundle = analyze_and_plan(str(src), asset_id="hum")
    assert any(a.processor == "HumNotch" for a in bundle.plan.actions), \
        [a.processor for a in bundle.plan.actions]
    notch = next(a for a in bundle.plan.actions if a.processor == "HumNotch")
    assert notch.parameters["base_hz"] == pytest.approx(60.0)

    audio, _ = sf.read(src, dtype="float32")
    out, _ = execute_plan(audio, SR, bundle.plan)
    out = out[:, 0] if out.ndim == 2 else out
    n = min(len(out), len(hummed))
    reduction_db = 10 * np.log10(
        (_band_energy(out[:n], 55, 65) + 1e-12) / (_band_energy(hummed[:n], 55, 65) + 1e-12))
    assert reduction_db < -6.0, f"60Hz band only moved {reduction_db:.1f} dB"


def test_clean_input_never_gets_hum_notch(tmp_path):
    src = tmp_path / "clean.wav"
    sf.write(src, _voice(), SR, subtype="PCM_16")
    bundle = analyze_and_plan(str(src), asset_id="clean")
    assert not any(a.processor == "HumNotch" for a in bundle.plan.actions)


def test_hum_notch_registered():
    spec = PROCESSORS["HumNotch"]
    assert spec.objective == "reduce_hum" and spec.reversible
    plugin = spec.factory({"base_hz": 60.0, "gain_db": -12.0, "q": 8.0, "harmonics": 3})
    assert plugin is not None
