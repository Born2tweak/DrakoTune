"""Decision engine: confidence-aware reasoning between diagnostics and DSP.

v1 (M07) implements deterministic safety gates. Objective selection and
conflict resolution arrive in M08; plan execution in M09.
"""

from src.decision.records import (
    DECISION_POLICY_VERSION,
    DecisionRecord,
    SafetyDecision,
)
from src.decision.planner import (
    DYNAMICS_CV_MIN,
    STRENGTH_BY_BAND,
    build_plan,
)
from src.decision.safety_rules import (
    HEADROOM_MIN_DB,
    MILD_CLIP_RATIO,
    SEVERE_CLIP_RATIO,
    evaluate_safety,
)

__all__ = [
    "DecisionRecord",
    "SafetyDecision",
    "DECISION_POLICY_VERSION",
    "evaluate_safety",
    "SEVERE_CLIP_RATIO",
    "MILD_CLIP_RATIO",
    "HEADROOM_MIN_DB",
    "build_plan",
    "STRENGTH_BY_BAND",
    "DYNAMICS_CV_MIN",
]
