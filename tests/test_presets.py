"""Style-preset tests (M34, ADR 0005): clean vs polished behavior."""

import numpy as np
import soundfile as sf

from fixtures.degradations import STANDARD_GRID, apply_recipe
from src.dsp_engine import execute_plan
from src.orchestration import analyze_and_plan

SR = 44100


def _voice(seconds=6.0):
    n = int(SR * seconds)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, amp in enumerate((1.0, 0.5, 0.33, 0.2), start=1):
        x += amp * np.sin(2 * np.pi * 220.0 * k * t)
    envelope = np.zeros(n)
    # Varying phrase levels: real vocals have crest 15-20 dB (corpus-v1);
    # equal-level Hann phrases give ~12 dB and correctly trip the
    # overcompression abstention. Level variety keeps the signal realistic.
    for (start_s, dur_s), level in zip(
            ((0.10, 0.85), (1.15, 0.60), (2.05, 1.10), (3.40, 0.45),
             (4.20, 0.90), (5.30, 0.50)),
            (1.0, 0.35, 0.7, 0.25, 0.9, 0.4)):
        i, m = int(start_s * SR), int(dur_s * SR)
        envelope[i:i + m] = np.maximum(envelope[i:i + m], level * np.hanning(m))
    x *= envelope * (0.6 + 0.4 * np.sin(2 * np.pi * 2.3 * t) ** 2)
    x *= 0.25 / max(np.max(np.abs(x)), 1e-9)
    return x.astype(np.float32)


def _plan(path, preset):
    return analyze_and_plan(str(path), asset_id="p", preset=preset).plan


def test_clean_preset_plans_no_style_compressor(tmp_path):
    src = tmp_path / "v.wav"
    sf.write(src, _voice(), SR, subtype="PCM_16")
    plan = _plan(src, "clean")
    assert not any(a.processor == "Compressor" for a in plan.actions)
    assert plan.preset_profile == "clean"


def test_polished_preset_adds_style_compressor_and_guard(tmp_path):
    src = tmp_path / "v.wav"
    sf.write(src, _voice(), SR, subtype="PCM_16")
    plan = _plan(src, "polished")
    comp = next(a for a in plan.actions if a.processor == "Compressor")
    assert "style" in comp.reason.lower() and "NOT defect" in comp.reason
    assert any(a.processor == "DeEsser" for a in plan.actions)  # guard rides along
    assert plan.preset_profile == "polished"
    # Relative threshold: engages near the measured level, not a fixed -20.
    assert -40.0 < comp.parameters["threshold_db"] < -5.0


def test_polished_compressor_actually_engages(tmp_path):
    src = tmp_path / "v.wav"
    sf.write(src, _voice(), SR, subtype="PCM_16")
    audio, _ = sf.read(src, dtype="float32")
    clean_out, _ = execute_plan(audio, SR, _plan(src, "clean"))
    pol_out, _ = execute_plan(audio, SR, _plan(src, "polished"))
    clean_out = clean_out[:, 0] if clean_out.ndim == 2 else clean_out
    pol_out = pol_out[:, 0] if pol_out.ndim == 2 else pol_out

    def crest(x):
        return float(np.max(np.abs(x)) / (np.sqrt(np.mean(x ** 2)) + 1e-12))

    assert crest(pol_out) < crest(clean_out) * 0.95, \
        f"style compressor inert: crest {crest(clean_out):.2f} -> {crest(pol_out):.2f}"


def test_polished_abstains_on_crushed_input(tmp_path):
    crushed = apply_recipe(_voice(), SR,
                           next(r for r in STANDARD_GRID if r.id == "overcompression_strong"))
    src = tmp_path / "c.wav"
    sf.write(src, crushed, SR, subtype="PCM_16")
    plan = _plan(src, "polished")
    assert not any(a.processor == "Compressor" for a in plan.actions)
    assert any("style preset abstains" in s for s in plan.skipped_processors)


def test_polished_engages_on_quiet_input_after_gain_restore(tmp_path):
    quiet = apply_recipe(_voice(), SR,
                         next(r for r in STANDARD_GRID if r.id == "low_level_moderate"))
    src = tmp_path / "q.wav"
    sf.write(src, quiet, SR, subtype="PCM_16")
    plan = _plan(src, "polished")
    procs = [a.processor for a in plan.actions]
    assert "Gain" in procs and "Compressor" in procs
    comp = next(a for a in plan.actions if a.processor == "Compressor")
    gain = next(a for a in plan.actions if a.processor == "Gain")
    # Threshold accounts for the planned level restore (post-gain RMS - 4).
    assert comp.parameters["threshold_db"] > -30.0 + gain.parameters["gain_db"] - 10.0
