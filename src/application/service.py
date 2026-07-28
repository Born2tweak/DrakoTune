"""Application service: typed Analyze/Plan/Render/Evaluate seam (DT-52).

Delegates to the existing orchestration, DSP engine, and evaluation without
changing behavior. The service depends only on the abstract ``DspBackend``
contract, so the DSP library is swappable and no adapter imports its internals.

Cancellation, unsupported processors/parameters, backend unavailability,
partial output, and build mismatch are surfaced as typed statuses rather than
crashes.
"""

from collections.abc import Callable

import numpy as np
import soundfile as sf

from src.application.backend import (
    BackendUnavailable,
    DspBackend,
    default_backend,
)
from src.application.commands import (
    AnalyzeResult,
    BuildIdentity,
    EvaluateResult,
    RenderResult,
)
from src.dsp_engine.executor import execute_graph
from src.dsp_engine.gain_staging import GainStage
from src.evaluation import evaluate
from src.evaluation.semantics.enums import ResultStatus
from src.modes import build_graph
from src.orchestration import PlanBundle, analyze_and_plan
from src.shared_types import ProcessingPlan


class ApplicationService:
    """Behavior-preserving typed facade over the v2 pipeline."""

    def __init__(self, backend: DspBackend | None = None) -> None:
        self._backend = backend or default_backend()

    @property
    def backend(self) -> DspBackend:
        return self._backend

    def _build_identity(self) -> BuildIdentity:
        caps = self._backend.capabilities()
        return BuildIdentity(
            backend_name=self._backend.name,
            backend_license=self._backend.license_id,
            engine_version=caps.engine_version,
        )

    # -- Analyze / Plan (no audio) -----------------------------------------
    def analyze(self, audio_path: str, *, preset: str = "clean",
                mode: str | None = None, intensity: str | None = None) -> AnalyzeResult:
        try:
            bundle: PlanBundle = analyze_and_plan(
                audio_path, preset=preset, mode=mode, intensity=intensity
            )
        except Exception as exc:  # decode/analysis failure -> typed error
            return AnalyzeResult(ResultStatus.ERROR, reasons=(f"analyze_failed:{type(exc).__name__}",))
        return AnalyzeResult(
            ResultStatus.PASSED,
            plan=bundle.plan,
            interpretations=bundle.interpretations,
        )

    def validate_plan(self, plan: ProcessingPlan) -> tuple[bool, tuple[str, ...]]:
        """Check every action against the backend capability contract."""
        reasons: list[str] = []
        ok = True
        for action in plan.actions:
            supported, why = self._backend.supports(action.processor, dict(action.parameters))
            if not supported:
                ok = False
                reasons.extend(why)
        return ok, tuple(reasons)

    # -- Render (audio) ----------------------------------------------------
    def render_array(
        self, audio: np.ndarray, sample_rate: int, plan: ProcessingPlan
    ) -> tuple[np.ndarray, RenderResult]:
        """Render in memory. Identical output to the underlying engine."""
        try:
            processed, result = self._backend.render(audio, sample_rate, plan)
        except BackendUnavailable:
            return audio, RenderResult(
                ResultStatus.ERROR, build=self._build_identity(), reasons=("backend_unavailable",)
            )
        return processed, RenderResult(
            ResultStatus.PASSED,
            applied_chain=result.chain_description(),
            skipped=result.skipped,
            build=self._build_identity(),
        )

    def render(
        self,
        input_path: str,
        output_path: str,
        plan: ProcessingPlan,
        *,
        cancel: Callable[[], bool] | None = None,
        expected_engine_version: str | None = None,
    ) -> RenderResult:
        """Render input->output. Behavior-identical to dsp_engine.render_plan."""
        build = self._build_identity()

        if expected_engine_version is not None and expected_engine_version != build.engine_version:
            return RenderResult(
                ResultStatus.ERROR, build=build,
                reasons=(f"build_mismatch:expected_{expected_engine_version}_got_{build.engine_version}",),
            )
        if cancel is not None and cancel():
            return RenderResult(ResultStatus.CANCELLED, build=build, reasons=("cancelled_before_render",))

        try:
            audio, sample_rate = sf.read(input_path, dtype="float32")
        except Exception as exc:
            return RenderResult(ResultStatus.ERROR, build=build, reasons=(f"decode_failed:{type(exc).__name__}",))

        try:
            processed, result = self._backend.render(audio, int(sample_rate), plan)
        except BackendUnavailable:
            return RenderResult(ResultStatus.ERROR, build=build, reasons=("backend_unavailable",))
        except Exception as exc:  # partial/failed render -> typed error, no partial file
            return RenderResult(ResultStatus.ERROR, build=build, reasons=(f"render_failed:{type(exc).__name__}",))

        if cancel is not None and cancel():
            # Post-render cancellation: do not write output.
            return RenderResult(ResultStatus.CANCELLED, build=build, reasons=("cancelled_after_render",))

        sf.write(output_path, processed, int(sample_rate), subtype="PCM_16")
        return RenderResult(
            ResultStatus.PASSED,
            output_path=output_path,
            applied_chain=result.chain_description(),
            skipped=result.skipped,
            build=build,
        )

    # -- Render a V3 mode (DT-96 integration) ------------------------------
    def render_mode(
        self,
        input_path: str,
        output_path: str,
        mode: str,
        intensity: str | None = None,
        *,
        stage: GainStage | str = GainStage.EXPORT,
        cancel: Callable[[], bool] | None = None,
    ) -> RenderResult:
        """Render a named V3 mode through the same guarantees as `render`.

        This is the product path: CLI, batch and the web job layer all reach V3
        through here, so mode renders get the same typed errors, cancellation
        points, output safety and build identity as a V2 plan render.
        """
        build = self._build_identity()
        if cancel is not None and cancel():
            return RenderResult(ResultStatus.CANCELLED, build=build,
                                reasons=("cancelled_before_render",))
        try:
            node = build_graph(mode, intensity)
        except (KeyError, ValueError) as exc:
            return RenderResult(ResultStatus.ERROR, build=build,
                                reasons=(f"unknown_mode:{exc}",))
        try:
            audio, sample_rate = sf.read(input_path, dtype="float32")
        except Exception as exc:
            return RenderResult(ResultStatus.ERROR, build=build,
                                reasons=(f"decode_failed:{type(exc).__name__}",))
        try:
            processed, result = execute_graph(audio, int(sample_rate), node, stage=stage)
        except Exception as exc:
            return RenderResult(ResultStatus.ERROR, build=build,
                                reasons=(f"render_failed:{type(exc).__name__}",))
        if cancel is not None and cancel():
            return RenderResult(ResultStatus.CANCELLED, build=build,
                                reasons=("cancelled_after_render",))

        sf.write(output_path, processed, int(sample_rate), subtype="PCM_16")
        return RenderResult(
            ResultStatus.PASSED,
            output_path=output_path,
            applied_chain=result.chain_description(),
            skipped=result.skipped,
            build=build,
        )

    # -- Evaluate ----------------------------------------------------------
    def evaluate(
        self, before_path: str, after_path: str, plan: ProcessingPlan | None = None
    ) -> EvaluateResult:
        try:
            ev = evaluate(before_path, after_path, plan)
        except Exception as exc:
            return EvaluateResult(ResultStatus.ERROR, reasons=(f"evaluate_failed:{type(exc).__name__}",))
        return EvaluateResult(ResultStatus.PASSED, evaluation=ev)
