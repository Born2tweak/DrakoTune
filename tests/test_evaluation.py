"""Before/after evaluation tests (M10).

Covers before/after deltas, loudness context, per-objective pass/fail, risk
warnings, serialization, and determinism. No subjective quality claims.
"""

import json

import numpy as np

from fixtures.loader import AUDIO_DIR, load_fixture
from src.dsp_engine import execute_plan
from src.evaluation import evaluate_arrays
from src.orchestration import analyze_and_plan
from src.shared_types import ProcessingObjective, ProcessingPlan

SR = 44100


def _tone(components: dict[float, float], seconds: float = 1.0) -> np.ndarray:
    t = np.linspace(0, seconds, int(SR * seconds), endpoint=False)
    sig = np.zeros_like(t)
    for f, a in components.items():
        sig += a * np.sin(2 * np.pi * f * t)
    return sig.astype(np.float32)


class TestDeltasAndContext:
    def test_reports_deltas_and_loudness_context(self):
        before = load_fixture("harsh").audio
        after = before * 0.9  # simple attenuation
        result = evaluate_arrays(before, after, SR)
        assert "harshness_ratio" in result.deltas
        assert "loudness_gain_db" in result.deltas  # loudness context always present
        assert result.before_metrics and result.after_metrics

    def test_loudness_increase_warns(self):
        before = _tone({220: 0.2})
        after = _tone({220: 0.5})  # much louder
        result = evaluate_arrays(before, after, SR)
        assert "loudness_increase_may_bias_comparison" in result.warnings


class TestObjectiveChecks:
    def test_harshness_reduction_passes(self):
        src = AUDIO_DIR / "harsh.wav"
        bundle = analyze_and_plan(str(src))
        before = load_fixture("harsh").audio
        after, _ = execute_plan(before, SR, bundle.plan)
        after = after[:, 0] if after.ndim > 1 else after
        result = evaluate_arrays(before, after, SR, plan=bundle.plan)
        assert any("reduce_harshness" in c for c in result.passed_checks)
        assert not any("reduce_harshness" in c for c in result.failed_checks)

    def test_objective_failure_recorded(self):
        # "after" is harsher than "before" but plan claims to reduce harshness.
        before = _tone({200: 0.5})
        after = _tone({200: 0.2, 4000: 0.6})
        plan = ProcessingPlan(
            id="p",
            objectives=(ProcessingObjective(id="obj.harshness", goal="reduce_harshness", confidence=0.8),),
        )
        result = evaluate_arrays(before, after, SR, plan=plan)
        assert any("reduce_harshness" in c for c in result.failed_checks)

    def test_report_only_objectives_are_not_checked(self):
        before = _tone({200: 0.5})
        after = before.copy()
        plan = ProcessingPlan(
            id="p",
            objectives=(ProcessingObjective(id="obj.harshness", goal="reduce_harshness",
                                            confidence=0.2, constraints=("report_only",)),),
        )
        result = evaluate_arrays(before, after, SR, plan=plan)
        assert result.passed_checks == () and result.failed_checks == ()


class TestContract:
    def test_no_output_clipping_no_warning(self):
        before = _tone({300: 0.4})
        after = before * 0.8
        result = evaluate_arrays(before, after, SR)
        assert "output_clipping" not in result.warnings

    def test_serializable(self):
        before = _tone({300: 0.4})
        result = evaluate_arrays(before, before * 0.9, SR)
        json.dumps(result.to_dict())

    def test_deterministic(self):
        before = _tone({300: 0.4})
        after = before * 0.9
        a = evaluate_arrays(before, after, SR).to_dict()
        b = evaluate_arrays(before, after, SR).to_dict()
        assert a == b
