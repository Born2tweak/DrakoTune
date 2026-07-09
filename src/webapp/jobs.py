"""Job store and processing for the web skeleton (M12).

Wraps the existing deterministic core (preprocess -> preflight -> analyze/plan
-> render -> evaluate -> report) behind a simple in-memory job model. Uploaded
audio is stored privately under a work root and is only reachable through the
app's controlled routes (no public paths, no path traversal). No accounts,
billing, or AI — that is deliberately out of scope for the skeleton.
"""

import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from src.dsp_engine import render_plan
from src.evaluation import evaluate
from src.ingestion import preflight
from src.dsp.preprocess import preprocess
from src.orchestration import analyze_and_plan
from src.reports import build_report, render_markdown

WORKROOT = Path(tempfile.gettempdir()) / "drakotune_web"

STATUS_COMPLETED = "completed"
STATUS_BLOCKED = "blocked"
STATUS_FAILED = "failed"


@dataclass
class Job:
    id: str
    name: str
    status: str
    message: str = ""
    before_path: Path | None = None
    after_path: Path | None = None
    report_markdown: str = ""
    objectives: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def public_dict(self) -> dict:
        urls: dict[str, str] = {}
        if self.before_path:
            urls["before"] = f"/api/audio/{self.id}/before"
        if self.after_path:
            urls["after"] = f"/api/audio/{self.id}/after"
        return {
            "job_id": self.id,
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "audio_urls": urls,
            "objectives": list(self.objectives),
            "warnings": list(self.warnings),
            "has_report": bool(self.report_markdown),
        }


_JOBS: dict[str, Job] = {}


def get_job(job_id: str) -> Job | None:
    return _JOBS.get(job_id)


def audio_path(job_id: str, which: str) -> Path | None:
    """Resolve a job's before/after file by id + name only (no traversal)."""
    job = _JOBS.get(job_id)
    if job is None or which not in ("before", "after"):
        return None
    path = job.before_path if which == "before" else job.after_path
    return path if path and path.exists() else None


def process_upload(filename: str, data: bytes) -> Job:
    """Run the deterministic pipeline on an uploaded file and store the job."""
    job_id = uuid.uuid4().hex
    name = Path(filename or "vocal").stem or "vocal"
    workdir = WORKROOT / job_id
    workdir.mkdir(parents=True, exist_ok=True)

    suffix = Path(filename).suffix or ".wav"
    raw_path = workdir / f"raw{suffix}"
    raw_path.write_bytes(data)

    normalized = workdir / "before.wav"
    try:
        preprocess(raw_path, normalized)
    except Exception as exc:  # noqa: BLE001 - surface decode/preprocess failures
        job = Job(id=job_id, name=name, status=STATUS_FAILED,
                  message=f"Could not decode audio: {type(exc).__name__}")
        _JOBS[job_id] = job
        return job

    report = preflight(normalized)
    if not report.passed:
        job = Job(id=job_id, name=name, status=STATUS_BLOCKED,
                  message="Preflight blocked: " + ", ".join(report.blockers),
                  before_path=normalized, warnings=report.warnings)
        _JOBS[job_id] = job
        return job

    bundle = analyze_and_plan(str(normalized), report, asset_id=name)
    processed = workdir / "after.wav"
    render_plan(str(normalized), str(processed), bundle.plan)
    evaluation = evaluate(str(normalized), str(processed), plan=bundle.plan, eval_id=name)
    report_md = render_markdown(build_report(bundle, evaluation, asset_name=name), evaluation)

    job = Job(
        id=job_id,
        name=name,
        status=STATUS_COMPLETED,
        message="Processed.",
        before_path=normalized,
        after_path=processed,
        report_markdown=report_md,
        objectives=tuple(o.goal for o in bundle.plan.objectives),
        warnings=evaluation.warnings,
    )
    _JOBS[job_id] = job
    return job
