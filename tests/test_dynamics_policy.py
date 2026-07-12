"""M33 dynamics-policy tests: level-restore promotion, overcompression
advisory + compressor abstention, recalibrated CV threshold behavior."""

import numpy as np
import soundfile as sf

from fixtures.degradations import STANDARD_GRID, apply_recipe
from src.diagnostics.advisory import (
    interpret_advisory,
    measure_advisory,
    promoted_level_interpretation,
)
from src.dsp_engine import execute_plan
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


def test_level_promotion_gate():
    quiet = apply_recipe(_voice(), SR, _recipe("low_level_strong"))
    obs, _ = measure_advisory(quiet, SR)
    promoted = promoted_level_interpretation(obs)
    assert promoted is not None and promoted.issue == "level_confirmed"
    normal_obs, _ = measure_advisory(_voice(), SR)
    assert promoted_level_interpretation(normal_obs) is None


def test_quiet_input_gets_gain_restore_not_compression(tmp_path):
    import pyloudnorm

    quiet = apply_recipe(_voice(6.0), SR, _recipe("low_level_moderate"))
    src = tmp_path / "quiet.wav"
    sf.write(src, quiet, SR, subtype="PCM_16")
    bundle = analyze_and_plan(str(src), asset_id="quiet")
    processors = [a.processor for a in bundle.plan.actions]
    assert "Gain" in processors, processors
    audio, _ = sf.read(src, dtype="float32")
    out, _ = execute_plan(audio, SR, bundle.plan)
    out = out[:, 0] if out.ndim == 2 else out
    before = pyloudnorm.Meter(SR).integrated_loudness(audio.astype(np.float64))
    after = pyloudnorm.Meter(SR).integrated_loudness(out.astype(np.float64))
    assert after > before + 6.0, f"level not restored: {before:.1f} -> {after:.1f}"


def test_overcompressed_advisory_fires():
    crushed = apply_recipe(_voice(6.0), SR, _recipe("overcompression_strong"))
    obs, _ = measure_advisory(crushed, SR)
    issues = {i.issue for i in interpret_advisory(obs)}
    assert "overcompressed" in issues


def test_compressor_abstains_on_crushed_input():
    """Conflict rule 6: a dynamics interpretation must be skipped, not acted
    on, when the input is already heavily compressed."""
    from src.decision.planner import build_plan
    from src.decision.records import SafetyDecision
    from src.shared_types import Observation

    loud = [
        Observation(id="loudness.consistency_cv", metric="consistency_cv",
                    value=1.2, units="ratio", confidence=0.9),
        Observation(id="loudness.crest_factor_db", metric="crest_factor_db",
                    value=9.0, units="dB", confidence=0.9),
        Observation(id="loudness.dynamic_range_db", metric="dynamic_range_db",
                    value=8.0, units="dB", confidence=0.9),
    ]
    plan = build_plan([], SafetyDecision(processing_allowed=True,
                                         enhancement_allowed=True,
                                         positive_gain_allowed=True),
                      loudness_observations=loud)
    assert not any(a.processor == "Compressor" for a in plan.actions)
    assert any("already heavily" in s for s in plan.skipped_processors)


def test_natural_singing_dynamics_do_not_trigger_compressor(tmp_path):
    """CV 0.54-0.82 is natural singing (corpus-v1): no compressor planned."""
    src = tmp_path / "voice.wav"
    sf.write(src, _voice(6.0), SR, subtype="PCM_16")
    bundle = analyze_and_plan(str(src), asset_id="v")
    assert not any(a.processor == "Compressor" for a in bundle.plan.actions), \
        [a.processor for a in bundle.plan.actions]
