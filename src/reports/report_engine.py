"""Report engine v2 (M27; v1 = M11).

Turns a decision bundle + evaluation (+ optional advisory diagnoses) into a
calm, non-marketing report answering the questions a creator actually has:
what condition was the input in, what was detected (and how confidently),
what was applied and why, what changed, what may have worsened, what
DrakoTune cannot fix, and what to consider rerecording.

Confidence is shown as bands (high/medium/low), never fake percentages.
Reports are deterministic for a given input: no timestamps, no random ids.
`build_manifest` produces the machine-readable JSON payload.
"""

from src.evaluation import EVALUATION_VERSION  # noqa: F401 (version anchor)
from src.shared_types import EvaluationResult, Report, band_from_confidence

REPORT_ENGINE_VERSION = "2.0.0"

_STANDING_LIMITATIONS = (
    "Detection thresholds are calibrated on synthetic degradations of real "
    "vocals (corpus-v1); blinded human listening validation is still pending.",
    "Objective metrics measure signal change, not musical quality.",
    "DrakoTune is not a professional mix or mastering engineer.",
)

# Plain-language explanations per controllable issue.
_ISSUE_EXPLANATIONS = {
    "rumble": "low-frequency energy below the voice (handling noise, room rumble)",
    "muddiness": "built-up low-mids that can make the voice sound thick or unclear",
    "harshness": "elevated upper-mid energy that can fatigue the ear",
    "sibilance": "sharp 's'/'t' sounds standing out from the voice",
    "noise_floor": "audible background noise in quiet moments",
    "dynamics": "uneven loudness between words or phrases",
}

# Advisory issues: what they mean + what the artist can do (DrakoTune cannot
# currently fix these; honesty over silence).
_ADVISORY_GUIDANCE = {
    "hum": ("mains hum (50/60 Hz electrical tone)",
            "DrakoTune does not remove hum yet. Check cables/ground loops and "
            "rerecord if possible."),
    "reverb": ("room reverberation baked into the recording",
               "DrakoTune cannot remove reverb. Rerecord closer to the mic in a "
               "deader room for a cleaner result."),
    "recording_level_low": ("very quiet recording level",
                            "Level was raised, but quiet recordings carry more noise. "
                            "Record hotter (peaking around -12 to -6 dB) next time."),
    "recording_level_high": ("very hot recording level",
                             "Watch input gain; recordings this hot risk clipping."),
    "plosives": ("low-frequency pops from 'p'/'b' sounds (experimental detector)",
                 "A pop filter or singing slightly off-axis prevents these."),
}

# Evaluation delta -> friendly line ("what changed"), only when meaningful.
_DELTA_LINES = (
    ("harshness_ratio", "upper-mid harshness energy"),
    ("sibilance_frame_p95", "sibilant-frame energy"),
    ("mud_ratio", "low-mid mud energy"),
    ("rumble_fraction", "sub-80 Hz rumble"),
    ("noise_floor_dbfs", "background noise floor (dB)"),
    ("consistency_cv", "loudness unevenness"),
)


def build_report(
    bundle,
    evaluation: EvaluationResult,
    asset_name: str = "input",
    advisory_interpretations: tuple = (),
) -> Report:
    """Build a structured Report from an orchestration bundle + evaluation."""
    findings: list[str] = []
    for interp in bundle.interpretations:
        band = band_from_confidence(interp.confidence).value
        meaning = _ISSUE_EXPLANATIONS.get(interp.issue, interp.issue)
        findings.append(f"{interp.issue}: {band} confidence — {meaning}")
    for interp in advisory_interpretations:
        if interp.issue in _ADVISORY_GUIDANCE:
            meaning, _ = _ADVISORY_GUIDANCE[interp.issue]
            band = band_from_confidence(interp.confidence).value
            findings.append(f"advisory {interp.issue}: {band} confidence — {meaning}")
    for flag in bundle.safety.integrity_flags:
        findings.append(f"safety flag: {flag}")
    safety_metrics = {o.metric: o.value for o in bundle.safety.observations}
    if "peak_dbfs" in safety_metrics:
        findings.append(
            f"peak {safety_metrics['peak_dbfs']:.1f} dBFS, "
            f"clipping {safety_metrics.get('clipping_ratio', 0.0):.2%}"
        )

    actions: list[str] = []
    for a in bundle.plan.actions:
        actions.append(f"applied {a.processor} [{a.objective_id}]: {a.reason}")
    for s in bundle.plan.skipped_processors:
        actions.append(f"skipped {s}")

    limitations = list(_STANDING_LIMITATIONS)
    for w in evaluation.warnings:
        limitations.append(f"evaluation warning: {w}")
    # Unfixable issues surface as explicit limitations with artist guidance.
    for interp in advisory_interpretations:
        guidance = _ADVISORY_GUIDANCE.get(interp.issue)
        if guidance:
            limitations.append(f"cannot fix — {interp.issue}: {guidance[1]}")

    passed, failed = len(evaluation.passed_checks), len(evaluation.failed_checks)
    if not bundle.decision.enhancement_allowed:
        summary = (
            f"{asset_name}: enhancement was blocked for safety "
            f"({', '.join(bundle.decision.blocked_targets)}). "
            "Only mitigation was considered."
        )
    else:
        summary = (
            f"{asset_name}: applied {len(bundle.plan.actions)} action(s) across "
            f"{len(bundle.plan.objectives)} objective(s); {passed} check(s) passed, "
            f"{failed} did not. See limitations before trusting the result."
        )

    return Report(
        id=f"report:{asset_name}",
        summary=summary,
        findings=tuple(findings),
        actions=tuple(actions),
        limitations=tuple(limitations),
        export_path=None,
    )


def render_markdown(report: Report, evaluation: EvaluationResult) -> str:
    """Render a Report (+ evaluation deltas) as deterministic Markdown."""
    lines: list[str] = ["# DrakoTune Report", "", f"_{report.summary}_", "", "## Findings"]
    lines += [f"- {f}" for f in report.findings] or ["- none"]
    lines += ["", "## Actions"]
    lines += [f"- {a}" for a in report.actions] or ["- none"]

    lines += ["", "## What changed"]
    loudness = evaluation.deltas.get("loudness_lufs_delta",
                                     evaluation.deltas.get("loudness_gain_db", 0.0))
    lines += [f"- loudness change: {loudness:+.2f} "
              f"{'LU' if 'loudness_lufs_delta' in evaluation.deltas else 'dB'} "
              "(compare loudness-matched previews — louder is not better)"]
    for metric, label in _DELTA_LINES:
        delta = evaluation.deltas.get(metric)
        if delta is not None and abs(delta) > 1e-3:
            direction = "reduced" if delta < 0 else "increased"
            lines.append(f"- {label}: {direction} ({delta:+.4f})")
    lines += [f"- pass: {c}" for c in evaluation.passed_checks]

    worsened = [f"- {c}" for c in evaluation.failed_checks]
    worsened += [f"- warning: {w}" for w in evaluation.warnings]
    residuals = getattr(evaluation, "residual_issues", ())
    if residuals:
        worsened += [f"- still detected in the output: {r}" for r in residuals]
    if worsened:
        lines += ["", "## What may have worsened or did not improve"] + worsened

    cannot_fix = [limitation for limitation in report.limitations
                  if limitation.startswith("cannot fix")]
    if cannot_fix:
        lines += ["", "## What DrakoTune cannot fix (consider rerecording)"]
        lines += [f"- {c.removeprefix('cannot fix — ')}" for c in cannot_fix]

    lines += ["", "## Limitations"]
    lines += [f"- {limitation}" for limitation in report.limitations
              if not limitation.startswith("cannot fix")]
    lines += [""]
    return "\n".join(lines)


def build_manifest(bundle, evaluation: EvaluationResult, report: Report) -> dict:
    """Machine-readable processing manifest (auditable record of the run)."""
    return {
        "report_engine_version": REPORT_ENGINE_VERSION,
        "summary": report.summary,
        "plan": bundle.plan.to_dict() if hasattr(bundle.plan, "to_dict") else {
            "policy_version": bundle.plan.policy_version,
            "objectives": [o.goal for o in bundle.plan.objectives],
            "actions": [{"processor": a.processor, "parameters": dict(a.parameters),
                         "reason": a.reason} for a in bundle.plan.actions],
            "skipped": list(bundle.plan.skipped_processors),
        },
        "decision": bundle.decision.to_dict(),
        "analyzers": {
            "safety": bundle.safety.analyzer_version,
            "loudness": bundle.loudness.analyzer_version,
            "spectral": bundle.spectral.analyzer_version,
        },
        "evaluation": {
            "deltas": dict(evaluation.deltas),
            "warnings": list(evaluation.warnings),
            "passed": list(evaluation.passed_checks),
            "failed": list(evaluation.failed_checks),
        },
        "findings": list(report.findings),
        "limitations": list(report.limitations),
    }
