"""Before/after evaluation (M10).

Compares the original and processed vocal on targeted, mostly loudness-invariant
metrics. It must not confuse louder with better: band ratios are normalized, an
explicit loudness delta is always reported, and an unexplained loudness increase
raises a warning.

For each objective in the plan, evaluation checks whether the targeted metric
moved in the intended direction and records a pass or fail. Output-safety risks
(clipping, loudness inflation) become warnings. Produces a canonical
EvaluationResult; it renders no audio and makes no subjective quality claim.
"""

import soundfile as sf

from src.diagnostics.loudness import measure_loudness
from src.diagnostics.safety import measure_safety
from src.diagnostics.spectral import measure_spectral
from src.shared_types import EvaluationResult, ProcessingPlan

EVALUATION_VERSION = "1.0.0"

# Objective -> (metric, desired_direction). -1 = should decrease, +1 = increase.
_OBJECTIVE_METRIC = {
    "reduce_harshness": ("harshness_ratio", -1),
    "reduce_muddiness": ("mud_ratio", -1),
    "reduce_sibilance": ("sibilance_frame_p95", -1),
    "reduce_rumble": ("rumble_fraction", -1),
    "reduce_noise": ("noise_floor_dbfs", -1),
    "stabilize_dynamics": ("consistency_cv", -1),
    "boost_air": ("air_ratio", +1),
}

OUTPUT_CLIP_WARN = 0.001   # any output clipping is a risk
LOUDNESS_WARN_DB = 1.0     # after louder than before by more than this -> warn
IMPROVE_EPS = 1e-3         # minimum move to count an objective as improved


def _collect_metrics(audio, sample_rate: int) -> dict:
    metrics: dict = {}
    for o in measure_safety(audio, sample_rate)[0]:
        metrics[o.metric] = o.value
    for o in measure_loudness(audio, sample_rate)[0]:
        metrics[o.metric] = o.value
    for o in measure_spectral(audio, sample_rate)[0]:
        metrics[o.metric] = o.value
    return metrics


def evaluate_arrays(
    before, after, sample_rate: int, plan: ProcessingPlan | None = None, eval_id: str = "eval"
) -> EvaluationResult:
    """Evaluate before vs after arrays. Renders no audio."""
    before_metrics = _collect_metrics(before, sample_rate)
    after_metrics = _collect_metrics(after, sample_rate)

    deltas = {
        k: round(after_metrics[k] - before_metrics[k], 6)
        for k in before_metrics
        if k in after_metrics
    }
    loudness_gain_db = round(
        after_metrics.get("rms_dbfs", -120.0) - before_metrics.get("rms_dbfs", -120.0), 3
    )
    deltas["loudness_gain_db"] = loudness_gain_db

    # Prefer BS.1770 LUFS for the loudness comparison when it is measurable.
    lufs_before = before_metrics.get("integrated_lufs", -120.0)
    lufs_after = after_metrics.get("integrated_lufs", -120.0)
    lufs_available = lufs_before > -120.0 and lufs_after > -120.0
    if lufs_available:
        deltas["loudness_lufs_delta"] = round(lufs_after - lufs_before, 3)
    loudness_change = deltas["loudness_lufs_delta"] if lufs_available else loudness_gain_db

    warnings: list[str] = []
    if after_metrics.get("clipping_ratio", 0.0) > OUTPUT_CLIP_WARN:
        warnings.append("output_clipping")
    if loudness_change > LOUDNESS_WARN_DB:
        warnings.append("loudness_increase_may_bias_comparison")
    if after_metrics.get("harshness_ratio", 0.0) > before_metrics.get("harshness_ratio", 0.0) + IMPROVE_EPS:
        warnings.append("harshness_increased")

    passed: list[str] = []
    failed: list[str] = []
    if plan is not None:
        for obj in plan.objectives:
            if "report_only" in obj.constraints:
                continue
            spec = _OBJECTIVE_METRIC.get(obj.goal)
            if spec is None:
                continue
            metric, direction = spec
            if metric not in deltas:
                continue
            moved = deltas[metric] * direction
            label = f"{obj.goal}:{metric} d={deltas[metric]:+.4f}"
            (passed if moved > IMPROVE_EPS else failed).append(label)

    return EvaluationResult(
        id=eval_id,
        before_metrics=before_metrics,
        after_metrics=after_metrics,
        deltas=deltas,
        warnings=tuple(warnings),
        passed_checks=tuple(passed),
        failed_checks=tuple(failed),
    )


def evaluate(
    before_path: str, after_path: str, plan: ProcessingPlan | None = None, eval_id: str = "eval"
) -> EvaluationResult:
    """Read before/after WAVs and evaluate them."""
    before, sr_b = sf.read(before_path, dtype="float32")
    after, sr_a = sf.read(after_path, dtype="float32")
    return evaluate_arrays(before, after, int(sr_b if sr_b == sr_a else sr_b), plan, eval_id)
