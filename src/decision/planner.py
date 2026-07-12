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
# M33 recalibration: 0.40 (synthetic-tone era) fired on 100% of clean real
# vocals — natural singing sits at CV 0.54-0.82 (corpus-v1, n=80). At 0.90:
# 3.8% clean FP, 68% recall on strong gain-jump inconsistency (moderate
# inconsistency falls below control — recorded limitation). Compression is
# the highest-artifact-risk processor; it must be rare, not default.
DYNAMICS_CV_MIN = 0.90

# M33 abstention (conflict rule 6): do not compress the already-crushed.
# Corpus gate: crest<14 dB or dynamic range<15 dB -> 3.8% clean FP,
# 81%/52%+ overcompression recall (moderate/strong).
OVERCOMP_CREST_MAX_DB = 14.0
OVERCOMP_DR_MIN_DB = 15.0

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
    # M30: static PeakFilter replaced by the frame-level DeEsser. Evidence:
    # the static cut left the sibilance diagnosis firing on 3/3 user-tested
    # processed files while listeners liked the overall brightness — so only
    # sibilant frames are attenuated. Threshold matches the detector metric;
    # depth scales with confidence strength, hard-capped (lisp guard).
    # Order 45: de-essing runs AFTER compression (order 40) — compression
    # lifts sibilant frames relative to the body (measured on 2/3 user files
    # whose sibilance only emerged post-compression; also the standing chain
    # order in docs/research/vocal_chain_research.md).
    "sibilance": _Spec("reduce_sibilance", "DeEsser", 45, True,
                       lambda s: {"band_lo_hz": 5000.0, "band_hi_hz": 9000.0,
                                  "frame_threshold": 0.18,
                                  "max_reduction_db": round(4.0 + 4.0 * s, 2)}),
    "noise_floor": _Spec("reduce_noise", "NoiseGate", 30, True,
                         lambda s: {"threshold_db": -42.0, "attack_ms": 1.0, "release_ms": 250.0}),
    # M28: only the strictly gated hum_confirmed interpretation maps here
    # (advisory "hum" stays spec-less). base_hz is filled from the advisory
    # observation in build_plan.
    # M33: strictly gated promotion of the recording_level_low advisory
    # (M25 evidence: 100% recall, 2.5% clean FP — the best candidate).
    # gain_db is computed from the measured LUFS in build_plan.
    "level_confirmed": _Spec("restore_level", "Gain", 5, False,
                             lambda s: {"gain_db": 0.0}),
    "hum_confirmed": _Spec("reduce_hum", "HumNotch", 15, True,
                           lambda s: {"gain_db": round(-12.0 * s, 2), "q": 8.0, "harmonics": 3}),
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
    advisory_observations: list[Observation] | None = None,
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
        # Conflict rule 6 (M33): never compress an already-crushed input.
        if interp.issue == "dynamics":
            crest = next((o.value for o in (loudness_observations or [])
                          if o.metric == "crest_factor_db"), 99.0)
            dr = next((o.value for o in (loudness_observations or [])
                       if o.metric == "dynamic_range_db"), 99.0)
            if crest < OVERCOMP_CREST_MAX_DB or dr < OVERCOMP_DR_MIN_DB:
                skipped.append(f"{spec.processor}:dynamics (input already heavily "
                               f"compressed: crest {crest:.1f} dB, DR {dr:.1f} dB)")
                continue

        strength = STRENGTH_BY_BAND[band]
        parameters = spec.build(strength)
        if interp.issue == "level_confirmed":
            # M33: gain restore toward the -23 LUFS working level, bounded by
            # the Gain safe range (+12 dB max: a -45 LUFS input is only
            # partially restored — recorded honestly in the action reason).
            lufs = next(
                (o.value for o in (advisory_observations or [])
                 if o.metric == "advisory_integrated_lufs"), -23.0)
            parameters["gain_db"] = round(min(12.0, max(0.0, -23.0 - lufs)), 2)
        if interp.issue == "hum_confirmed":
            parameters["base_hz"] = next(
                (o.value for o in (advisory_observations or []) if o.metric == "hum_base_hz"),
                60.0,
            )
        actions.append((spec.order, ProcessingAction(
            id=f"act.{interp.issue}",
            processor=spec.processor,
            parameters=parameters,
            strength=strength,
            reason=f"{interp.issue} ({band.value} confidence {interp.confidence:.2f}); "
                   f"{'conservative' if band == ConfidenceBand.MEDIUM else 'standard'} move.",
            objective_id=f"obj.{interp.issue}",
            reversible=True,
        )))

    # Style preset (M34, ADR 0005): 'polished' adds a gentle style compressor
    # regardless of the dynamics diagnosis. Its threshold is relative to the
    # measured input RMS *after* any planned level restore, so it engages at
    # any input level. Explicitly labeled style, not defect correction; the
    # overcompression abstention still applies (never polish the crushed).
    if preset_profile == "polished" and not enhancement_blocked:
        crest = next((o.value for o in (loudness_observations or [])
                      if o.metric == "crest_factor_db"), 99.0)
        dr = next((o.value for o in (loudness_observations or [])
                   if o.metric == "dynamic_range_db"), 99.0)
        already_has_comp = any(a.processor == "Compressor" for _, a in actions)
        if not already_has_comp and crest >= OVERCOMP_CREST_MAX_DB and dr >= OVERCOMP_DR_MIN_DB:
            rms_dbfs = next((o.value for o in (loudness_observations or [])
                             if o.metric == "rms_dbfs"), -20.0)
            planned_gain = next((a.parameters.get("gain_db", 0.0)
                                 for _, a in actions if a.processor == "Gain"), 0.0)
            style_threshold = round(min(0.0, max(-60.0, rms_dbfs + planned_gain - 4.0)), 2)
            objectives.append(ProcessingObjective(
                id="obj.style_polish", goal="style_polish", priority=40,
                confidence=0.9, constraints=("style",)))
            actions.append((40, ProcessingAction(
                id="act.style_polish", processor="Compressor",
                parameters={"threshold_db": style_threshold, "ratio": 2.5,
                            "attack_ms": 15.0, "release_ms": 75.0},
                strength=0.6,
                reason="'polished' style preset: gentle glue compression "
                       "(user-selected style, NOT defect correction; ADR 0005).",
                objective_id="obj.style_polish", reversible=True)))
        elif not already_has_comp:
            skipped.append("Compressor:style_polish (input already heavily "
                           "compressed; style preset abstains)")

    # Post-compression sibilance guard (M30): compression is known (and was
    # measured on real files) to expose sibilance that input diagnosis cannot
    # see. The DeEsser is self-gating at the frame level (transparent below
    # its threshold, proven < -50 dB residual on non-sibilant content), so a
    # conservative guard instance is added after any planned Compressor.
    has_compressor = any(a.processor == "Compressor" for _, a in actions)
    has_deesser = any(a.processor == "DeEsser" for _, a in actions)
    if has_compressor and not has_deesser and not enhancement_blocked:
        objectives.append(ProcessingObjective(
            id="obj.sibilance_guard", goal="reduce_sibilance", priority=45,
            confidence=0.6, constraints=()))
        actions.append((45, ProcessingAction(
            id="act.sibilance_guard",
            processor="DeEsser",
            # Guard threshold 0.25 is STRICTER than the diagnosis threshold
            # (0.18): benchmark 20260712-095014 showed the 0.18 guard paying a
            # fidelity cost by taming the reference's own normal esses on
            # otherwise-clean quiet clips. The user-measured real residuals
            # (0.29-0.40) remain well above 0.25.
            parameters={"band_lo_hz": 5000.0, "band_hi_hz": 9000.0,
                        "frame_threshold": 0.25, "max_reduction_db": 6.0},
            strength=0.6,
            reason="post-compression sibilance guard (self-gating: acts only on "
                   "frames whose 5-9kHz fraction exceeds 0.18; compression "
                   "exposes sibilance — measured on user-tested files).",
            objective_id="obj.sibilance_guard",
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
