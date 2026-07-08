"""Decision engine v1 — objective selection and plan building (M08).

Converts interpretations (M06) into conservative objectives and actions,
honoring the safety decision (M07). This keeps the four layers separate:

  Observation  -> Interpretation -> ProcessingObjective -> ProcessingAction

Confidence controls automation (Bible law):
  HIGH   -> full (still bounded) action strength.
  MEDIUM -> conservative strength (smaller move).
  LOW    -> report-only: no action; recorded as a skipped/report recommendation.

Conflict rules applied here:
  1. Safety over enhancement — if enhancement is blocked, drop tonal actions.
  2. Cleanup before dynamics — actions are ordered EQ/gate before compression.
  3. Smaller moves when confidence is medium.
  4. Report-only when confidence is low.
  5. Do not boost air when noise floor is elevated (avoid amplifying noise).

This module builds a ProcessingPlan only. It renders NO audio (that is M09).
"""

from dataclasses import dataclass

from src.decision.records import DECISION_POLICY_VERSION, SafetyDecision
from src.shared_types import (
    ConfidenceBand,
    Interpretation,
    Observation,
    ProcessingAction,
    ProcessingObjective,
    ProcessingPlan,
    band_from_confidence,
)

# Strength applied per confidence band (LOW -> report-only, no action).
STRENGTH_BY_BAND = {ConfidenceBand.HIGH: 1.0, ConfidenceBand.MEDIUM: 0.6}

# Dynamics objective fires when frame-level consistency CV exceeds this.
DYNAMICS_CV_MIN = 0.40

# Noise-floor observation above this (dBFS) suppresses air boosts.
NOISE_SUPPRESS_AIR_DBFS = -50.0


@dataclass(frozen=True)
class _Spec:
    goal: str
    processor: str
    order: int
    is_enhancement: bool
    build: callable  # (strength) -> parameters dict


# issue -> processing specification. Parameters are bounded defaults scaled by
# strength; frequency refinement can be added later without changing the shape.
_ISSUE_SPECS: dict[str, _Spec] = {
    "rumble": _Spec("reduce_rumble", "HighpassFilter", 10, True,
                    lambda s: {"cutoff_frequency_hz": 80.0 + 20.0 * s}),
    "muddiness": _Spec("reduce_muddiness", "PeakFilter", 20, True,
                       lambda s: {"cutoff_frequency_hz": 300.0, "gain_db": round(-4.0 * s, 2), "q": 0.8}),
    "harshness": _Spec("reduce_harshness", "PeakFilter", 21, True,
                       lambda s: {"cutoff_frequency_hz": 3500.0, "gain_db": round(-4.5 * s, 2), "q": 1.4}),
    "sibilance": _Spec("reduce_sibilance", "PeakFilter", 22, True,
                       lambda s: {"cutoff_frequency_hz": 6500.0, "gain_db": round(-3.5 * s, 2), "q": 3.5}),
    "noise_floor": _Spec("reduce_noise", "NoiseGate", 30, True,
                         lambda s: {"threshold_db": -42.0, "attack_ms": 1.0, "release_ms": 250.0}),
    "dynamics": _Spec("stabilize_dynamics", "Compressor", 40, False,
                      lambda s: {"threshold_db": round(-18.0 - 2.0 * s, 2),
                                 "ratio": round(2.5 + 1.0 * s, 2), "attack_ms": 15.0, "release_ms": 75.0}),
}


def _dynamics_from_loudness(observations: list[Observation]) -> Interpretation | None:
    cv = next((o for o in observations if o.metric == "consistency_cv"), None)
    if cv is None or cv.value <= DYNAMICS_CV_MIN:
        return None
    return Interpretation(
        id="interp.dynamics",
        issue="dynamics",
        supporting_observation_ids=("loudness.consistency_cv",),
        confidence=cv.confidence,
        rationale=f"Frame loudness inconsistent (cv={cv.value:.2f}).",
    )


def build_plan(
    interpretations: list[Interpretation],
    safety_decision: SafetyDecision,
    loudness_observations: list[Observation] | None = None,
    spectral_observations: list[Observation] | None = None,
    preset_profile: str = "adaptive",
) -> ProcessingPlan:
    """Build a confidence-gated, conflict-resolved ProcessingPlan. Renders no audio."""
    issues = list(interpretations)
    dyn = _dynamics_from_loudness(loudness_observations or [])
    if dyn is not None:
        issues.append(dyn)

    # Context for conflict rules.
    noise_dbfs = next(
        (o.value for o in (spectral_observations or []) if o.metric == "noise_floor_dbfs"),
        -120.0,
    )
    enhancement_blocked = not safety_decision.enhancement_allowed

    objectives: list[ProcessingObjective] = []
    actions: list[tuple[int, ProcessingAction]] = []
    skipped: list[str] = []

    for interp in issues:
        spec = _ISSUE_SPECS.get(interp.issue)
        if spec is None:
            continue

        band = band_from_confidence(interp.confidence)
        objectives.append(ProcessingObjective(
            id=f"obj.{interp.issue}",
            goal=spec.goal,
            priority=spec.order,
            confidence=interp.confidence,
            constraints=("report_only",) if band == ConfidenceBand.LOW else (),
        ))

        # Conflict rule 1: safety over enhancement.
        if enhancement_blocked and spec.is_enhancement:
            skipped.append(f"{spec.processor}:{interp.issue} (enhancement blocked by safety)")
            continue
        # Conflict rule 5: no air boost when noisy (no air specs here, guard is future-proof).
        if spec.goal == "boost_air" and noise_dbfs > NOISE_SUPPRESS_AIR_DBFS:
            skipped.append(f"{spec.processor}:{interp.issue} (noise floor too high for air boost)")
            continue
        # Conflict rule 4: report-only when confidence is low.
        if band == ConfidenceBand.LOW:
            skipped.append(f"{spec.processor}:{interp.issue} (report-only: low confidence)")
            continue

        strength = STRENGTH_BY_BAND[band]
        actions.append((spec.order, ProcessingAction(
            id=f"act.{interp.issue}",
            processor=spec.processor,
            parameters=spec.build(strength),
            strength=strength,
            reason=f"{interp.issue} ({band.value} confidence {interp.confidence:.2f}); "
                   f"{'conservative' if band == ConfidenceBand.MEDIUM else 'standard'} move.",
            objective_id=f"obj.{interp.issue}",
            reversible=True,
        )))

    # Conflict rule 2: cleanup before dynamics — deterministic order.
    ordered_actions = tuple(a for _, a in sorted(actions, key=lambda t: t[0]))

    return ProcessingPlan(
        id="plan.v1",
        preset_profile=preset_profile,
        objectives=tuple(sorted(objectives, key=lambda o: o.priority)),
        actions=ordered_actions,
        skipped_processors=tuple(skipped),
        policy_version=DECISION_POLICY_VERSION,
    )
