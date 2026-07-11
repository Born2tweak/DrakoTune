"""Job store and processing for the web skeleton (M12).

Wraps the existing deterministic core (preprocess -> preflight -> analyze/plan
-> render -> evaluate -> report) behind a simple in-memory job model. Uploaded
audio is stored privately under a work root and is only reachable through the
app's controlled routes (no public paths, no path traversal). No accounts,
billing, or AI — that is deliberately out of scope for the skeleton.
"""

import atexit
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from src.diagnostics.advisory import diagnose_advisory
from src.dsp_engine import render_plan
from src.evaluation import evaluate
from src.evaluation.ab_export import export_matched_pair
from src.ingestion import preflight
from src.dsp.preprocess import preprocess
from src.orchestration import analyze_and_plan
from src.reports import build_report, render_markdown

WORKROOT = Path(tempfile.gettempdir()) / "drakotune_web"

STATUS_COMPLETED = "completed"
STATUS_BLOCKED = "blocked"
STATUS_FAILED = "failed"


RETENTION_SECONDS = 3600  # working audio is cleaned up after this age


@dataclass
class Job:
    id: str
    name: str
    status: str
    message: str = ""
    before_path: Path | None = None
    after_path: Path | None = None
    # Loudness-matched preview pair (M27): fair comparison, ADR 0004.
    before_preview_path: Path | None = None
    after_preview_path: Path | None = None
    previews_matched: bool = False
    report_markdown: str = ""
    objectives: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    workdir: Path | None = None
    created_at: float = field(default_factory=time.time)
    # Structured payloads for the UI (M14); not serialized in public_dict.
    report: object | None = None  # shared_types.Report
    evaluation: object | None = None  # shared_types.EvaluationResult
    blocked_targets: tuple[str, ...] = ()

    def public_dict(self) -> dict:
        # Playback URLs are omitted here on purpose: they are minted as signed,
        # time-limited capabilities by the app layer. There are no public URLs.
        return {
            "job_id": self.id,
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "has_before": self.before_path is not None,
            "has_after": self.after_path is not None,
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
    if job is None or which not in ("before", "after", "before_preview", "after_preview"):
        return None
    path = {
        "before": job.before_path,
        "after": job.after_path,
        "before_preview": job.before_preview_path,
        "after_preview": job.after_preview_path,
    }[which]
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
                  message=f"Could not decode audio: {type(exc).__name__}", workdir=workdir)
        _JOBS[job_id] = job
        return job

    report = preflight(normalized)
    if not report.passed:
        job = Job(id=job_id, name=name, status=STATUS_BLOCKED,
                  message="Preflight blocked: " + ", ".join(report.blockers),
                  before_path=normalized, warnings=report.warnings, workdir=workdir)
        _JOBS[job_id] = job
        return job

    bundle = analyze_and_plan(str(normalized), report, asset_id=name)
    _, advisory = diagnose_advisory(str(normalized), asset_id=name)
    processed = workdir / "after.wav"
    render_plan(str(normalized), str(processed), bundle.plan)
    evaluation = evaluate(str(normalized), str(processed), plan=bundle.plan, eval_id=name)
    report_obj = build_report(bundle, evaluation, asset_name=name,
                              advisory_interpretations=advisory)
    report_md = render_markdown(report_obj, evaluation)

    # Loudness-matched previews (ADR 0004): the comparison players must not
    # carry a loudness bias. On matcher refusal, fall back to the raw pair.
    before_preview = workdir / "before_preview.wav"
    after_preview = workdir / "after_preview.wav"
    previews_matched = True
    try:
        export_matched_pair(str(normalized), str(processed),
                            str(before_preview), str(after_preview))
    except Exception:  # incl. LoudnessMatchError: refusal is by design
        previews_matched = False

    job = Job(
        id=job_id,
        name=name,
        status=STATUS_COMPLETED,
        message="Processed.",
        before_path=normalized,
        after_path=processed,
        before_preview_path=before_preview if previews_matched else None,
        after_preview_path=after_preview if previews_matched else None,
        previews_matched=previews_matched,
        report_markdown=report_md,
        objectives=tuple(o.goal for o in bundle.plan.objectives),
        warnings=evaluation.warnings,
        workdir=workdir,
        report=report_obj,
        evaluation=evaluation,
        blocked_targets=tuple(bundle.decision.blocked_targets),
    )
    _JOBS[job_id] = job
    return job


def delete_job(job_id: str) -> bool:
    """Remove a job and its private working files. Returns True if it existed."""
    job = _JOBS.pop(job_id, None)
    if job is None:
        return False
    if job.workdir is not None:
        shutil.rmtree(job.workdir, ignore_errors=True)
    return True


def cleanup_expired(max_age_seconds: float = RETENTION_SECONDS) -> int:
    """Delete jobs older than the retention window. Returns count removed."""
    now = time.time()
    stale = [jid for jid, j in _JOBS.items() if now - j.created_at > max_age_seconds]
    for jid in stale:
        delete_job(jid)
    return len(stale)


def _cleanup_all() -> None:
    shutil.rmtree(WORKROOT, ignore_errors=True)


atexit.register(_cleanup_all)
