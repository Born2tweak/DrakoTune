"""Typed application commands and results (DT-52).

The application exposes four commands — Analyze, Plan, Render, Evaluate — with
typed results carrying a canonical status (DT-45 ``ResultStatus``) and build
identity. These are the seam the CLI, web, and future desktop adapters call;
none of them import DSP-library internals.
"""

from dataclasses import dataclass, field

from src.evaluation.semantics.enums import ResultStatus
from src.shared_types import EvaluationResult, ProcessingPlan


@dataclass(frozen=True)
class BuildIdentity:
    """Which engine/backend produced a result (from DT-50 fingerprint)."""

    backend_name: str = "unknown"
    backend_license: str = "unknown"
    engine_version: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "backend_name": self.backend_name,
            "backend_license": self.backend_license,
            "engine_version": self.engine_version,
        }


@dataclass(frozen=True)
class AnalyzeResult:
    """Diagnostics + plan for an input (no audio rendered)."""

    status: ResultStatus
    plan: ProcessingPlan | None = None
    interpretations: tuple = ()
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class RenderResult:
    """Outcome of rendering a plan through a backend."""

    status: ResultStatus
    output_path: str | None = None
    applied_chain: str = ""
    skipped: tuple[str, ...] = ()
    build: BuildIdentity = field(default_factory=BuildIdentity)
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluateResult:
    """Before/after evaluation outcome."""

    status: ResultStatus
    evaluation: EvaluationResult | None = None
    reasons: tuple[str, ...] = ()
