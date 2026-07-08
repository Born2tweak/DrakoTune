"""DSP engine: executes decision-authored plans through bounded processors."""

from src.dsp_engine.executor import (
    AppliedAction,
    ExecutionResult,
    execute_plan,
    render_plan,
)
from src.dsp_engine.processors import (
    PROCESSOR_ENGINE_VERSION,
    PROCESSORS,
    ProcessorSpec,
    clamp_params,
)

__all__ = [
    "execute_plan",
    "render_plan",
    "ExecutionResult",
    "AppliedAction",
    "PROCESSORS",
    "ProcessorSpec",
    "clamp_params",
    "PROCESSOR_ENGINE_VERSION",
]
