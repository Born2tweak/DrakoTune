"""End-to-end decision-driven orchestration (M09).

Ties the layered pipeline together without any layer reaching into another's
responsibilities:

  diagnostics (measure) -> interpretations -> decision (gate + plan) -> DSP (render)

`analyze_and_plan` produces a ProcessingPlan and SafetyDecision from a decoded
WAV, rendering no audio. `render_plan` (dsp_engine) then executes it. This is the
canonical v2 path; the legacy adaptive chain in src/dsp/pipeline.py remains as a
fallback until this path is A/B-validated on real vocals.
"""

from dataclasses import dataclass

from src.decision import build_plan, evaluate_safety
from src.decision.records import SafetyDecision
from src.diagnostics import diagnose_loudness, diagnose_safety, diagnose_spectral
from src.shared_types import DiagnosticResult, Interpretation, ProcessingPlan


@dataclass(frozen=True)
class PlanBundle:
    """Everything the decision path produced for one input (no audio)."""

    plan: ProcessingPlan
    decision: SafetyDecision
    safety: DiagnosticResult
    loudness: DiagnosticResult
    spectral: DiagnosticResult
    interpretations: tuple[Interpretation, ...]


def analyze_and_plan(audio_path: str, preflight_report=None, asset_id: str = "input") -> PlanBundle:
    """Run diagnostics + decision to produce a ProcessingPlan. Renders no audio."""
    safety = diagnose_safety(audio_path, asset_id=asset_id)
    loudness = diagnose_loudness(audio_path, asset_id=asset_id)
    spectral, interpretations = diagnose_spectral(audio_path, asset_id=asset_id)

    decision = evaluate_safety(preflight_report, safety)
    plan = build_plan(
        list(interpretations),
        decision,
        loudness_observations=list(loudness.observations),
        spectral_observations=list(spectral.observations),
    )
    return PlanBundle(
        plan=plan,
        decision=decision,
        safety=safety,
        loudness=loudness,
        spectral=spectral,
        interpretations=interpretations,
    )
