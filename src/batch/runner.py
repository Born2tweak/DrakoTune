"""Batch processing (M20).

Run the deterministic v2 pipeline over a directory of vocals, writing a
per-file report + processed audio and a summary index (JSON + Markdown). Reuses
the same core as the CLI and web app; blocked/failed files are recorded, not
fatal, so one bad file never stops the batch.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.dsp.preprocess import preprocess
from src.dsp_engine import render_plan
from src.evaluation import evaluate
from src.ingestion import preflight
from src.orchestration import analyze_and_plan
from src.reports import build_manifest, build_report, render_markdown

AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aif", ".aiff"}

STATUS_COMPLETED = "completed"
STATUS_BLOCKED = "blocked"
STATUS_FAILED = "failed"


@dataclass
class BatchItem:
    name: str
    status: str
    message: str = ""
    objectives: tuple[str, ...] = ()
    passed: int = 0
    failed: int = 0
    warnings: tuple[str, ...] = ()
    report_path: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "objectives": list(self.objectives),
            "passed": self.passed,
            "failed": self.failed,
            "warnings": list(self.warnings),
            "report_path": self.report_path,
        }


@dataclass
class BatchSummary:
    items: list[BatchItem] = field(default_factory=list)

    def counts(self) -> dict:
        c = {STATUS_COMPLETED: 0, STATUS_BLOCKED: 0, STATUS_FAILED: 0}
        for it in self.items:
            c[it.status] = c.get(it.status, 0) + 1
        return c

    def to_dict(self) -> dict:
        return {"counts": self.counts(), "items": [it.to_dict() for it in self.items]}

    def to_markdown(self) -> str:
        c = self.counts()
        lines = [
            "# DrakoTune Batch Summary",
            "",
            f"{len(self.items)} file(s): {c[STATUS_COMPLETED]} completed, "
            f"{c[STATUS_BLOCKED]} blocked, {c[STATUS_FAILED]} failed.",
            "",
            "| file | status | objectives | checks | notes |",
            "|------|--------|-----------|--------|-------|",
        ]
        for it in self.items:
            checks = f"{it.passed}✓ / {it.failed}✗" if it.status == STATUS_COMPLETED else "—"
            notes = it.message or ", ".join(it.warnings)
            objectives = ", ".join(it.objectives) or "—"
            lines.append(f"| {it.name} | {it.status} | {objectives} | {checks} | {notes} |")
        lines.append("")
        lines.append("_DrakoTune is not a professional mix; see each report's limitations._")
        return "\n".join(lines)


def _find_audio(input_dir: Path) -> list[Path]:
    return sorted(p for p in input_dir.iterdir()
                  if p.is_file() and p.suffix.lower() in AUDIO_EXTS)


def _process_one(src: Path, out_root: Path, preset: str = "clean") -> BatchItem:
    name = src.stem
    workdir = out_root / name
    workdir.mkdir(parents=True, exist_ok=True)

    normalized = workdir / "before.wav"
    try:
        preprocess(src, normalized)
    except Exception as exc:  # noqa: BLE001
        return BatchItem(name=name, status=STATUS_FAILED,
                         message=f"decode failed: {type(exc).__name__}")

    pf = preflight(normalized)
    if not pf.passed:
        return BatchItem(name=name, status=STATUS_BLOCKED,
                         message="preflight: " + ", ".join(pf.blockers),
                         warnings=pf.warnings)

    bundle = analyze_and_plan(str(normalized), pf, asset_id=name, preset=preset)
    processed = workdir / "after.wav"
    render_plan(str(normalized), str(processed), bundle.plan)
    evaluation = evaluate(str(normalized), str(processed), plan=bundle.plan, eval_id=name)
    report = build_report(bundle, evaluation, asset_name=name,
                          advisory_interpretations=getattr(bundle, "advisory_interpretations", ()))
    report_md = render_markdown(report, evaluation)
    report_path = workdir / "report.md"
    report_path.write_text(report_md, encoding="utf-8")
    (workdir / "report.json").write_text(
        json.dumps(build_manifest(bundle, evaluation, report), indent=2), encoding="utf-8")

    return BatchItem(
        name=name,
        status=STATUS_COMPLETED,
        message="",
        objectives=tuple(o.goal for o in bundle.plan.objectives),
        passed=len(evaluation.passed_checks),
        failed=len(evaluation.failed_checks),
        warnings=evaluation.warnings,
        report_path=str(report_path),
    )


def run_batch(input_dir: str | Path, output_dir: str | Path, write_summary: bool = True,
              preset: str = "clean") -> BatchSummary:
    """Process every audio file in input_dir; write per-file outputs + a summary."""
    input_dir = Path(input_dir)
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    summary = BatchSummary(items=[_process_one(src, out_root, preset=preset) for src in _find_audio(input_dir)])

    if write_summary:
        (out_root / "summary.json").write_text(
            json.dumps(summary.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (out_root / "summary.md").write_text(summary.to_markdown(), encoding="utf-8")

    return summary
