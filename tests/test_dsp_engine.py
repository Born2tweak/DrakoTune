"""DSP plan executor tests (M09).

Processor smoke tests, parameter clamping, plan execution, skipped logging,
original-preservation, and an end-to-end decision->render harshness-reduction
check.
"""

import numpy as np
import pytest
import soundfile as sf

from fixtures.loader import AUDIO_DIR
from src.dsp_engine import PROCESSORS, clamp_params, execute_plan, render_plan
from src.orchestration import analyze_and_plan
from src.shared_types import ProcessingAction, ProcessingPlan

SR = 44100

_VALID_PARAMS = {
    "Gain": {"gain_db": 0.0},
    "HighpassFilter": {"cutoff_frequency_hz": 80.0},
    "PeakFilter": {"cutoff_frequency_hz": 3000.0, "gain_db": -3.0, "q": 1.4},
    "HighShelfFilter": {"cutoff_frequency_hz": 10000.0, "gain_db": 2.0, "q": 0.7},
    "Compressor": {"threshold_db": -18.0, "ratio": 3.0, "attack_ms": 15.0, "release_ms": 75.0},
    "NoiseGate": {"threshold_db": -42.0, "attack_ms": 1.0, "release_ms": 250.0},
    "Limiter": {"threshold_db": -1.0, "release_ms": 250.0},
}


def _tone(freq: float, amp: float, seconds: float = 1.0) -> np.ndarray:
    t = np.linspace(0, seconds, int(SR * seconds), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


class TestProcessors:
    @pytest.mark.parametrize("name", sorted(PROCESSORS))
    def test_processor_builds_and_processes(self, name):
        plugin = PROCESSORS[name].factory(_VALID_PARAMS[name])
        from pedalboard import Pedalboard

        out = Pedalboard([plugin])(_tone(440, 0.3).reshape(1, -1), SR)
        assert np.all(np.isfinite(out))

    def test_clamp_enforces_safe_range(self):
        params, clamped = clamp_params("PeakFilter", {"gain_db": -50.0, "q": 1.4, "cutoff_frequency_hz": 3000.0})
        assert params["gain_db"] == -12.0
        assert "gain_db" in clamped

    def test_clamp_leaves_in_range_untouched(self):
        params, clamped = clamp_params("PeakFilter", {"gain_db": -3.0, "q": 1.4, "cutoff_frequency_hz": 3000.0})
        assert clamped == []


class TestExecution:
    def test_executes_actions_and_appends_output_safety(self):
        plan = ProcessingPlan(
            id="p", actions=(
                ProcessingAction(id="a1", processor="HighpassFilter",
                                 parameters={"cutoff_frequency_hz": 90.0}, objective_id="obj.rumble"),
                ProcessingAction(id="a2", processor="PeakFilter",
                                 parameters={"cutoff_frequency_hz": 3500.0, "gain_db": -4.0, "q": 1.4},
                                 objective_id="obj.harshness"),
            ),
        )
        processed, result = execute_plan(_tone(200, 0.5), SR, plan)
        assert processed.shape[0] == SR
        assert np.all(np.isfinite(processed)) and np.max(np.abs(processed)) <= 1.0
        assert result.applied[-1].processor == "Limiter"  # output safety always last
        assert result.applied[-1].objective_id == "output_safety"

    def test_empty_plan_only_output_safety(self):
        processed, result = execute_plan(_tone(200, 0.5), SR, ProcessingPlan(id="p"))
        assert len(result.applied) == 1 and result.applied[0].objective_id == "output_safety"
        assert np.all(np.isfinite(processed))

    def test_skipped_and_unknown_logged(self):
        plan = ProcessingPlan(
            id="p",
            actions=(ProcessingAction(id="a", processor="NotAProcessor", parameters={}),),
            skipped_processors=("PeakFilter:harshness (report-only: low confidence)",),
        )
        _, result = execute_plan(_tone(200, 0.5), SR, plan)
        assert any("report-only" in s for s in result.skipped)
        assert any("unknown processor" in s for s in result.skipped)

    def test_out_of_range_params_are_clamped_on_execute(self):
        plan = ProcessingPlan(
            id="p",
            actions=(ProcessingAction(id="a", processor="PeakFilter",
                                      parameters={"cutoff_frequency_hz": 3000.0, "gain_db": -99.0, "q": 1.4}),),
        )
        _, result = execute_plan(_tone(3000, 0.5), SR, plan)
        peak = next(a for a in result.applied if a.processor == "PeakFilter")
        assert peak.parameters["gain_db"] == -12.0
        assert "gain_db" in peak.clamped_keys


class TestRenderAndPreservation:
    def test_render_writes_output_and_preserves_input(self, tmp_path):
        src = AUDIO_DIR / "harsh.wav"
        original_bytes = src.read_bytes()
        out = tmp_path / "out.wav"

        bundle = analyze_and_plan(str(src))
        render_plan(str(src), str(out), bundle.plan)

        assert out.exists()
        assert src.read_bytes() == original_bytes  # original untouched

    def test_decision_render_reduces_harshness(self, tmp_path):
        src = AUDIO_DIR / "harsh.wav"
        out = tmp_path / "out.wav"
        bundle = analyze_and_plan(str(src))
        # harsh fixture should yield a harshness action.
        assert any(a.objective_id == "obj.harshness" for a in bundle.plan.actions)
        render_plan(str(src), str(out), bundle.plan)

        def harsh_energy(path):
            a, sr = sf.read(str(path), dtype="float32")
            fft = np.fft.rfft(a)
            freqs = np.fft.rfftfreq(len(a), 1.0 / sr)
            mask = (freqs >= 2500) & (freqs <= 6000)
            return float(np.sum(np.abs(fft[mask]) ** 2))

        assert harsh_energy(out) < harsh_energy(src)


class TestOrchestration:
    def test_analyze_and_plan_is_audio_free_bundle(self):
        bundle = analyze_and_plan(str(AUDIO_DIR / "muddy.wav"))
        assert bundle.plan.policy_version
        assert any(o.goal == "reduce_muddiness" for o in bundle.plan.objectives)

    def test_clipped_input_blocks_enhancement_actions(self):
        bundle = analyze_and_plan(str(AUDIO_DIR / "clipped.wav"))
        assert bundle.decision.enhancement_allowed is False
        assert bundle.plan.actions == ()  # tonal actions dropped
        assert bundle.plan.skipped_processors  # and logged
