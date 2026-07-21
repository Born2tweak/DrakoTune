"""Multiaxis verdict engine (DT-48).

Adjudicates an ``EvaluationBundle`` across ordered hard gates (safety, target
efficacy, collateral harm, intent, perceptual outcome) into a typed ``Verdict``
with claim eligibility. Refuses the listening exploits in NEGATIVE_RESULTS.md
and never hides collateral harm behind target improvement.
"""

from src.evaluation.verdict.bundle import (
    EvaluationBundle,
    ListeningSummary,
    MetricObservation,
    PanelCounts,
)
from src.evaluation.verdict.engine import VERDICT_RULE_SET_ID, Verdict, adjudicate

__all__ = [
    "EvaluationBundle",
    "MetricObservation",
    "ListeningSummary",
    "PanelCounts",
    "Verdict",
    "adjudicate",
    "VERDICT_RULE_SET_ID",
]
