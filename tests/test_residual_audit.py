"""Residual self-audit tests (M31): evaluation re-diagnoses its own output."""

from pathlib import Path

import numpy as np

from fixtures.degradations import STANDARD_GRID, apply_recipe
from src.evaluation import evaluate_arrays
from src.shared_types import ProcessingObjective, ProcessingPlan

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


def _noisy():
    recipe = next(r for r in STANDARD_GRID if r.id == "noise_strong_room_tone")
    return apply_recipe(_voice(), SR, recipe)


def test_residuals_listed_when_output_still_defective():
    noisy = _noisy()
    # "Processing" that does nothing: output == input, noise survives.
    result = evaluate_arrays(noisy, noisy.copy(), SR)
    assert any(r.startswith("noise_floor") for r in result.residual_issues), result.residual_issues


def test_targeted_residual_produces_named_warning():
    noisy = _noisy()
    plan = ProcessingPlan(
        id="p", preset_profile="test", actions=(), skipped_processors=(),
        policy_version="test",
        objectives=(ProcessingObjective(id="obj.noise_floor", goal="reduce_noise",
                                        priority=30, confidence=0.8, constraints=()),),
    )
    result = evaluate_arrays(noisy, noisy.copy(), SR, plan=plan)
    assert "residual_after_processing:noise_floor" in result.warnings


def test_clean_output_reports_no_residuals():
    # A real studio clip: the synthetic _voice() is legitimately low-mid
    # dominant (220 Hz fundamental, centroid ~326 Hz) and correctly reads as
    # muddy — so the no-residual contract is pinned on real clean material.
    import soundfile as sf

    clean, _ = sf.read(
        Path(__file__).resolve().parent.parent
        / "fixtures" / "audio_real" / "vocalset_female1_straight.wav",
        dtype="float32")
    result = evaluate_arrays(clean, clean.copy(), SR)
    assert result.residual_issues == (), result.residual_issues


def test_residuals_serialize_roundtrip():
    from src.shared_types import EvaluationResult

    noisy = _noisy()
    result = evaluate_arrays(noisy, noisy.copy(), SR)
    rebuilt = EvaluationResult.from_dict(result.to_dict())
    assert rebuilt.residual_issues == result.residual_issues


def test_report_renders_residuals():
    from src.orchestration import analyze_and_plan  # noqa: F401 (import check only)
    from src.reports import render_markdown, build_report  # noqa: F401
    # Rendering path: residuals appear under the worsened section.
    from src.shared_types import EvaluationResult, Report

    evaluation = EvaluationResult(
        id="e", residual_issues=("sibilance (0.40)",),
        warnings=("residual_after_processing:sibilance",),
    )
    report = Report(id="r", summary="s", findings=(), actions=(),
                    limitations=("x",), export_path=None)
    md = render_markdown(report, evaluation)
    assert "still detected in the output: sibilance (0.40)" in md
