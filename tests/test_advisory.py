"""Advisory diagnostics tests (M25). Advisory issues must never reach DSP."""

import numpy as np

from fixtures.degradations import STANDARD_GRID, apply_recipe
from src.decision.planner import build_plan
from src.decision.records import SafetyDecision
from src.diagnostics.advisory import (
    ADVISORY_ISSUES,
    interpret_advisory,
    measure_advisory,
)

SR = 44100


def _voice(seconds=4.0):
    """Harmonic 'voice' with smooth, APERIODIC phrases. A machine-periodic
    square envelope would put genuine comb spikes at exactly 50/60 Hz and
    (correctly) trigger the hum detector — real voices are not periodic."""
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


def _issues(audio):
    obs, _ = measure_advisory(audio, SR)
    return {i.issue for i in interpret_advisory(obs)}, obs


def _recipe(rid):
    return next(r for r in STANDARD_GRID if r.id == rid)


def test_clean_voice_raises_no_hum_or_level_flags():
    issues, _ = _issues(_voice())
    assert "hum" not in issues
    assert "recording_level_low" not in issues and "recording_level_high" not in issues


def test_hum_detected_on_hum_recipe():
    degraded = apply_recipe(_voice(), SR, _recipe("hum_strong"))
    issues, obs = _issues(degraded)
    assert "hum" in issues
    count = next(o for o in obs if o.metric == "hum_harmonic_count")
    assert count.value >= 2


def test_low_level_detected():
    degraded = apply_recipe(_voice(), SR, _recipe("low_level_strong"))
    issues, _ = _issues(degraded)
    assert "recording_level_low" in issues


def test_reverb_estimator_fires_on_strong_reverb():
    degraded = apply_recipe(_voice(), SR, _recipe("reverb_strong"))
    issues, _ = _issues(degraded)
    assert "reverb" in issues


def test_plosive_bursts_detected():
    voice = _voice()
    rng = np.random.default_rng(7)
    t_burst = np.arange(int(SR * 0.06)) / SR
    thump = (np.sin(2 * np.pi * 70 * t_burst) * np.exp(-t_burst / 0.02)).astype(np.float32)
    for pos_s in (0.5, 1.2, 2.1, 2.9, 3.5):
        i = int(pos_s * SR)
        voice[i:i + len(thump)] += 0.9 * thump * float(rng.uniform(0.8, 1.0))
    issues, _ = _issues(voice)
    assert "plosives" in issues


def test_advisory_issues_produce_no_dsp_actions():
    """The planner must have no spec for any advisory issue: report-only by construction."""
    degraded = apply_recipe(_voice(), SR, _recipe("hum_strong"))
    obs, _ = measure_advisory(degraded, SR)
    interps = interpret_advisory(obs)
    assert interps, "test needs at least one advisory interpretation"
    assert {i.issue for i in interps} <= set(ADVISORY_ISSUES)
    plan = build_plan(list(interps), SafetyDecision(
        processing_allowed=True, enhancement_allowed=True, positive_gain_allowed=True))
    assert plan.actions == (), "advisory issues must never generate processing actions"
