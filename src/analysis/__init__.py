"""Preregistered, clustered, tie-aware listening analysis (DT-57, autonomous portion).

Replaces the legacy M24 naive-binomial analyzer. Builds the *method* the contract
marks Automatic: an immutable preregistration + analysis lock, a listener-clustered
tie-aware model that yields indeterminate on degenerate designs (no naive fallback),
a seeded power/sample-size simulation harness, and diagnostics. It creates method
eligibility only — no result, no claim, no chosen sample size, no signed threshold
(Field 21/22). Human sign-off (independent method approval + threshold/design
values) is the only remaining gate.
"""
from src.analysis.diagnostics import Diagnostics, diagnose
from src.analysis.model import (
    AnalysisResult,
    Convergence,
    Decision,
    ListenerSummary,
    analyze,
    evaluate,
    listener_summaries,
)
from src.analysis.power import (
    SimConfig,
    estimate_power,
    power_curve,
    simulate_summaries,
    type_one_error,
)
from src.analysis.prereg import (
    PENDING,
    PREREG_SCHEMA_VERSION,
    Direction,
    EndpointKind,
    ExclusionRule,
    Hypothesis,
    PreregistrationPlan,
    matches_lock,
)

__all__ = [
    "Diagnostics", "diagnose",
    "AnalysisResult", "Convergence", "Decision", "ListenerSummary",
    "analyze", "evaluate", "listener_summaries",
    "SimConfig", "estimate_power", "power_curve", "simulate_summaries", "type_one_error",
    "PENDING", "PREREG_SCHEMA_VERSION", "Direction", "EndpointKind",
    "ExclusionRule", "Hypothesis", "PreregistrationPlan", "matches_lock",
]
