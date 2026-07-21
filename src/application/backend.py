"""DSP backend contract and the current Pedalboard adapter (DT-52).

The application layer talks to a ``DspBackend`` — a typed, license-aware,
capability-declaring interface — never to a concrete DSP library. This is the
seam that lets a future desktop build swap the backend without the UI/service
importing library internals, and it makes the current GPL dependency explicit.

The adapter here preserves current behavior exactly: it delegates to
``src.dsp_engine.execute_plan`` and changes no sound.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np

from src.dsp_engine import PROCESSOR_ENGINE_VERSION, PROCESSORS, clamp_params, execute_plan
from src.dsp_engine.executor import ExecutionResult
from src.shared_types import ProcessingPlan


class BackendUnavailable(RuntimeError):
    """Raised/returned when a backend cannot service a render."""


@dataclass(frozen=True)
class BackendCapabilities:
    """What a backend can do, declared up front."""

    processors: tuple[str, ...]
    safe_ranges: dict[str, dict[str, tuple[float, float]]]
    stateful: bool
    latency_samples: int
    engine_version: str


@runtime_checkable
class DspBackend(Protocol):
    """Typed DSP backend. Implementations declare identity, license, capability."""

    name: str
    license_id: str

    def capabilities(self) -> BackendCapabilities: ...

    def supports(self, processor: str, params: dict) -> tuple[bool, tuple[str, ...]]: ...

    def render(
        self, audio: np.ndarray, sample_rate: int, plan: ProcessingPlan
    ) -> tuple[np.ndarray, ExecutionResult]: ...


class PedalboardBackend:
    """Adapter over the current Pedalboard/array DSP engine. Behavior-preserving.

    Declares its GPL license identity explicitly (DT-50 captured FFmpeg + this
    backend as GPL; the distribution decision is the human-only DT-51 gate).
    """

    name = "pedalboard_array_v1"
    # pedalboard is GPL-3.0; this adapter inherits that obligation. Recorded,
    # not resolved.
    license_id = "GPL-3.0-only"

    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            processors=tuple(sorted(PROCESSORS)),
            safe_ranges={name: dict(spec.safe_ranges) for name, spec in PROCESSORS.items()},
            stateful=False,
            latency_samples=0,
            engine_version=PROCESSOR_ENGINE_VERSION,
        )

    def supports(self, processor: str, params: dict) -> tuple[bool, tuple[str, ...]]:
        spec = PROCESSORS.get(processor)
        if spec is None:
            return False, (f"unsupported_processor:{processor}",)
        _, warnings = clamp_params(processor, params)
        unknown = tuple(p for p in params if p not in spec.safe_ranges)
        reasons = tuple(f"unknown_param:{p}" for p in unknown) + tuple(warnings)
        return (len(unknown) == 0), reasons

    def render(
        self, audio: np.ndarray, sample_rate: int, plan: ProcessingPlan
    ) -> tuple[np.ndarray, ExecutionResult]:
        return execute_plan(audio, sample_rate, plan)


class UnavailableBackend:
    """A backend that is present in type but cannot service renders.

    Models the "backend unavailable" adversarial case without a crash.
    """

    name = "unavailable"
    license_id = "unknown"

    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities((), {}, False, 0, "0.0.0")

    def supports(self, processor: str, params: dict) -> tuple[bool, tuple[str, ...]]:
        return False, ("backend_unavailable",)

    def render(self, audio, sample_rate, plan):
        raise BackendUnavailable("backend is unavailable")


def default_backend() -> DspBackend:
    return PedalboardBackend()
