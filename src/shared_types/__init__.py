"""Canonical, versioned records for DrakoTune.

This package is the shared vocabulary every layer speaks: diagnostics emit
Observations, the decision engine produces Objectives/Actions/Plans,
evaluation produces EvaluationResults, and the report engine produces Reports.
Everything is a frozen dataclass with explicit to_dict/from_dict and a version
field, so runs can be serialized, compared, and pinned by fixtures.
"""

from src.shared_types.asset import AudioAsset, DiagnosticResult
from src.shared_types.decision import (
    ProcessingAction,
    ProcessingObjective,
    ProcessingPlan,
)
from src.shared_types.evaluation import EvaluationResult
from src.shared_types.interpretation import Interpretation
from src.shared_types.observation import Observation
from src.shared_types.record import ProcessingRecord
from src.shared_types.report import Report
from src.shared_types.serialization import to_serializable
from src.shared_types.versions import (
    ANALYZER_VERSION,
    CONFIDENCE_HIGH_MIN,
    CONFIDENCE_MEDIUM_MIN,
    POLICY_VERSION,
    SCHEMA_VERSION,
    ConfidenceBand,
    band_from_confidence,
)

__all__ = [
    "AudioAsset",
    "DiagnosticResult",
    "Observation",
    "Interpretation",
    "ProcessingObjective",
    "ProcessingAction",
    "ProcessingPlan",
    "EvaluationResult",
    "Report",
    "ProcessingRecord",
    "to_serializable",
    "ConfidenceBand",
    "band_from_confidence",
    "SCHEMA_VERSION",
    "ANALYZER_VERSION",
    "POLICY_VERSION",
    "CONFIDENCE_HIGH_MIN",
    "CONFIDENCE_MEDIUM_MIN",
]
