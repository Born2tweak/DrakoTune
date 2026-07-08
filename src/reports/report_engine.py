"""Report engine v1 (M11).

Turns a decision bundle + evaluation into a calm, non-marketing report that a
creator or an agent can read. Confidence is shown as bands (high/medium/low),
never fake percentages. Reports are deterministic for a given input: no
timestamps, no random ids.

The structured Report (canonical type) is the stored payload; render_markdown
produces the human-readable document. PDF polish is out of scope (M14+).
"""

from src.evaluation import EVALUATION_VERSION  # noqa: F401 (version anchor)
from src.shared_types import EvaluationResult, Report, band_from_confidence

REPORT_ENGINE_VERSION = "1.0.0"

_STANDING_LIMITATIONS = (
    "Thresholds are heuristic and not yet calibrated on real vocals.",
    "Fixtures are synthetic; no subjective listening validation has been done.",
    "Loudness uses an RMS proxy; gated BS.1770 LUFS is not implemented.",
    "DrakoTune is not a professional mix or mastering engineer.",
)


def build_report(bundle, evaluation: EvaluationResult, asset_name: str = "input") -> Report:
    """Build a structured Report from an orchestration bundle + evaluation."""
    findings: list[str] = []
    for interp in bundle.interpretations:
        band = band_from_confidence(interp.confidence).value
        findings.append(f"{interp.issue}: {band} confidence")
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
    lines += ["", "## Evaluation",
              f"- loudness change: {evaluation.deltas.get('loudness_gain_db', 0.0):+.2f} dB"]
    lines += [f"- pass: {c}" for c in evaluation.passed_checks]
    lines += [f"- fail: {c}" for c in evaluation.failed_checks]
    if not evaluation.passed_checks and not evaluation.failed_checks:
        lines += ["- no objective checks (report-only or no objectives)"]
    lines += ["", "## Limitations"]
    lines += [f"- {limitation}" for limitation in report.limitations]
    lines += [""]
    return "\n".join(lines)
