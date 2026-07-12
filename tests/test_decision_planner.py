"""Decision engine v1 — objective selection / plan tests (M08).

Pins layer separation, confidence-gated strength, low-confidence report-only,
conflict resolution (safety, ordering), and that a plan is built without audio.
"""

from src.decision import STRENGTH_BY_BAND, build_plan
from src.decision.records import DECISION_POLICY_VERSION, SafetyDecision
from src.shared_types import ConfidenceBand, Interpretation, Observation


def _interp(issue: str, confidence: float) -> Interpretation:
    return Interpretation(id=f"interp.{issue}", issue=issue, confidence=confidence,
                          supporting_observation_ids=(f"spectral.{issue}_ratio",))


def _safe(enh=True, gain=True) -> SafetyDecision:
    return SafetyDecision(processing_allowed=True, enhancement_allowed=enh, positive_gain_allowed=gain)


class TestConfidenceGating:
    def test_high_confidence_full_strength(self):
        plan = build_plan([_interp("harshness", 0.85)], _safe())
        act = next(a for a in plan.actions if a.objective_id == "obj.harshness")
        assert act.strength == STRENGTH_BY_BAND[ConfidenceBand.HIGH]
        assert act.parameters["gain_db"] == -4.5  # full move

    def test_medium_confidence_conservative(self):
        plan = build_plan([_interp("harshness", 0.5)], _safe())
        act = next(a for a in plan.actions if a.objective_id == "obj.harshness")
        assert act.strength == STRENGTH_BY_BAND[ConfidenceBand.MEDIUM]
        assert abs(act.parameters["gain_db"]) < 4.5  # smaller move than high

    def test_low_confidence_report_only(self):
        plan = build_plan([_interp("harshness", 0.2)], _safe())
        assert not any(a.objective_id == "obj.harshness" for a in plan.actions)
        assert any("report-only" in s for s in plan.skipped_processors)
        obj = next(o for o in plan.objectives if o.id == "obj.harshness")
        assert "report_only" in obj.constraints


class TestSeparation:
    def test_objectives_and_actions_are_separate_and_linked(self):
        plan = build_plan([_interp("muddiness", 0.8)], _safe())
        assert plan.objectives and plan.actions
        obj_ids = {o.id for o in plan.objectives}
        for a in plan.actions:
            assert a.objective_id in obj_ids

    def test_plan_is_pure_no_audio(self):
        # build_plan takes only records/observations — proven by construction here.
        plan = build_plan([_interp("harshness", 0.8)], _safe())
        assert plan.policy_version == DECISION_POLICY_VERSION


class TestConflictResolution:
    def test_safety_blocks_enhancement_actions(self):
        plan = build_plan([_interp("harshness", 0.85), _interp("muddiness", 0.85)],
                          _safe(enh=False))
        assert plan.actions == ()
        assert all("enhancement blocked" in s for s in plan.skipped_processors)

    def test_cleanup_before_dynamics_ordering(self):
        interps = [_interp("harshness", 0.85)]
        loud = [Observation(id="loudness.consistency_cv", metric="consistency_cv",
                            value=1.1, units="ratio", window="frame", confidence=0.9)]  # M33: >0.90 fires
        plan = build_plan(interps, _safe(), loudness_observations=loud)
        processors = [a.processor for a in plan.actions]
        assert "PeakFilter" in processors and "Compressor" in processors
        assert processors.index("PeakFilter") < processors.index("Compressor")

    def test_dynamics_objective_from_loudness(self):
        loud = [Observation(id="loudness.consistency_cv", metric="consistency_cv",
                            value=1.1, units="ratio", window="frame", confidence=0.9)]  # M33: >0.90 fires
        plan = build_plan([], _safe(), loudness_observations=loud)
        assert any(o.goal == "stabilize_dynamics" for o in plan.objectives)


class TestDeterminism:
    def test_deterministic(self):
        interps = [_interp("harshness", 0.85), _interp("sibilance", 0.5)]
        a = build_plan(interps, _safe()).to_dict()
        b = build_plan(interps, _safe()).to_dict()
        assert a == b
