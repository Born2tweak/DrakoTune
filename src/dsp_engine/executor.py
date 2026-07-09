"""DSP plan executor (M09).

Executes a ProcessingPlan through bounded processor modules. The executor makes
no decisions — it realizes exactly the actions the decision engine authored,
clamps their parameters to safe ranges, always applies an output-safety limiter,
logs applied and skipped processors, and never overwrites the original audio.
"""

from dataclasses import dataclass, field

import numpy as np
import soundfile as sf
from pedalboard import Pedalboard

from src.dsp_engine.processors import PROCESSOR_ENGINE_VERSION, PROCESSORS, clamp_params
from src.shared_types import ProcessingPlan

# Output-safety ceiling: attenuate-only headroom protection. This is deliberately
# NOT a makeup limiter — a limiter with auto-gain would boost quiet material and
# inflate loudness, violating "never assume louder is better". We only scale down
# when the peak exceeds the ceiling; we never boost.
CEILING_DBFS = -0.2
_CEILING_LINEAR = 10.0 ** (CEILING_DBFS / 20.0)


def _apply_ceiling(audio: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > _CEILING_LINEAR:
        audio = audio * np.float32(_CEILING_LINEAR / peak)
    return audio.astype(np.float32)


@dataclass(frozen=True)
class AppliedAction:
    processor: str
    parameters: dict
    clamped_keys: tuple[str, ...]
    objective_id: str | None

    def to_dict(self) -> dict:
        return {
            "processor": self.processor,
            "parameters": dict(self.parameters),
            "clamped_keys": list(self.clamped_keys),
            "objective_id": self.objective_id,
        }


@dataclass(frozen=True)
class ExecutionResult:
    applied: tuple[AppliedAction, ...] = ()
    skipped: tuple[str, ...] = ()
    engine_version: str = PROCESSOR_ENGINE_VERSION

    def chain_description(self) -> str:
        return " -> ".join(a.processor for a in self.applied) or "no-op (output safety only)"

    def to_dict(self) -> dict:
        return {
            "applied": [a.to_dict() for a in self.applied],
            "skipped": list(self.skipped),
            "engine_version": self.engine_version,
            "chain": self.chain_description(),
        }


def execute_plan(
    audio: np.ndarray, sample_rate: int, plan: ProcessingPlan, apply_output_safety: bool = True
) -> tuple[np.ndarray, ExecutionResult]:
    """Render a plan over `audio`. Returns (processed_audio, ExecutionResult)."""
    work = audio.reshape(-1, 1) if audio.ndim == 1 else audio.astype(np.float32)

    plugins = []
    applied: list[AppliedAction] = []
    skipped: list[str] = list(plan.skipped_processors)

    for action in plan.actions:
        spec = PROCESSORS.get(action.processor)
        if spec is None:
            skipped.append(f"{action.processor} (unknown processor)")
            continue
        params, clamped = clamp_params(action.processor, action.parameters)
        plugins.append(spec.factory(params))
        applied.append(AppliedAction(
            processor=action.processor,
            parameters=params,
            clamped_keys=tuple(clamped),
            objective_id=action.objective_id,
        ))

    if plugins:
        board = Pedalboard(plugins)
        processed = board(work.T.astype(np.float32), sample_rate).T
    else:
        processed = work.astype(np.float32)

    if apply_output_safety:
        processed = _apply_ceiling(processed)
        applied.append(AppliedAction("output_ceiling", {"ceiling_dbfs": CEILING_DBFS}, (), "output_safety"))

    processed = np.clip(processed, -1.0, 1.0).astype(np.float32)
    return processed, ExecutionResult(applied=tuple(applied), skipped=tuple(skipped))


def render_plan(
    input_path: str, output_path: str, plan: ProcessingPlan
) -> ExecutionResult:
    """Read input, execute the plan, write output. Original is never modified."""
    audio, sample_rate = sf.read(input_path, dtype="float32")
    processed, result = execute_plan(audio, int(sample_rate), plan)
    sf.write(output_path, processed, int(sample_rate), subtype="PCM_16")
    return result
