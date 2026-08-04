"""Job store and processing for the web skeleton (M12).

Wraps the existing deterministic core (preprocess -> preflight -> analyze/plan
-> render -> evaluate -> report) behind a simple in-memory job model. Uploaded
audio is stored privately under a work root and is only reachable through the
app's controlled routes (no public paths, no path traversal). No accounts,
billing, or AI — that is deliberately out of scope for the skeleton.
"""

import atexit
import os
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import soundfile as sf

from src.diagnostics.advisory import diagnose_advisory
from src.dsp_engine import render_plan
from src.dsp_engine.executor import render_mode
from src.dsp_engine.gain_staging import GainStage
from src.evaluation import evaluate
from src.evaluation.ab_export import export_matched_pair
from src.evaluation.delivery_metrics import measure_delivery
from src.ingestion import preflight
from src.modes import apply_macros, build_graph, list_modes, parse_macros
from src.dsp.preprocess import preprocess, probe_channels
from src.orchestration import analyze_and_plan
from src.reports import build_report, render_markdown

WORKROOT = Path(tempfile.gettempdir()) / "drakotune_web"

STATUS_COMPLETED = "completed"
STATUS_BLOCKED = "blocked"
STATUS_FAILED = "failed"

# Upper bound on input length. Chosen from the 2026-08-04 OOM: a 3.3-minute
# vocal survived locally, a longer one killed a 2 GB container. With 4 GB and
# this cap the pipeline has clear headroom. Override per-deployment.
MAX_AUDIO_SECONDS = float(os.environ.get("DRAKOTUNE_MAX_AUDIO_SECONDS", "360"))


RETENTION_SECONDS = 3600  # working audio is cleaned up after this age


class UnknownModeError(ValueError):
    """An explicit mode selection that does not name a real mode.

    Carries the available list so the API can answer the question the caller
    actually has ("then what may I ask for?") instead of only refusing.
    """

    def __init__(self, requested: str, available: tuple[str, ...] | list[str]):
        self.requested = requested
        self.available = list(available)
        super().__init__(
            f"unknown mode {requested!r}; available: {', '.join(self.available)}")


@dataclass
class Job:
    id: str
    name: str
    status: str
    message: str = ""
    before_path: Path | None = None
    after_path: Path | None = None
    preset: str = "clean"  # processing preset used (M39; ADR 0005)
    # V3 selection (DT-96/97). When `mode` is set the render used a mode graph.
    mode: str | None = None
    intensity: str | None = None
    channels: int = 1  # channel count of the delivered file
    macros: dict = field(default_factory=lambda: {"changed": [], "inert": []})
    # What the EXPORT gain stage did, and what the delivered file measures.
    # Both are descriptive: `delivery` is telemetry, never a quality verdict.
    gain_staging: dict | None = None
    delivery: dict | None = None
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
            "preset": self.preset,
            "mode": self.mode,
            "intensity": self.intensity,
            "channels": self.channels,
            "macros": dict(self.macros),
            "gain_staging": self.gain_staging,
            "delivery": self.delivery,
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


def process_upload(filename: str, data: bytes, preset: str = "clean",
                   mode: str | None = None, intensity: str | None = None,
                   macros: str | dict | None = None) -> Job:
    """Run the deterministic pipeline on an uploaded file and store the job."""
    job_id = uuid.uuid4().hex
    name = Path(filename or "vocal").stem or "vocal"
    workdir = WORKROOT / job_id
    workdir.mkdir(parents=True, exist_ok=True)

    suffix = Path(filename).suffix or ".wav"
    raw_path = workdir / f"raw{suffix}"
    raw_path.write_bytes(data)

    # Duration guard. A byte-size cap is not enough: a compressed 6-minute MP3
    # is small on the wire but expands to a very large float array, and the whole
    # pipeline holds it in memory. On 2026-08-04 a real full-length vocal
    # OOM-killed the container mid-render, which also destroyed the in-memory job
    # and left the browser waiting forever on a request that could not return.
    # Refusing up front turns that into an immediate, explainable error.
    try:
        info = sf.info(str(raw_path))
        duration_s = float(info.frames) / float(info.samplerate or 1)
    except Exception:  # noqa: BLE001 - unreadable here means preprocess will report it
        duration_s = 0.0
    if duration_s > MAX_AUDIO_SECONDS:
        job = Job(
            id=job_id, name=name, status=STATUS_FAILED,
            message=(
                f"That file is {duration_s / 60:.1f} minutes long. This service "
                f"currently processes up to {MAX_AUDIO_SECONDS / 60:.0f} minutes per "
                "upload. Trim it, or render a section at a time."
            ),
        )
        _JOBS[job_id] = job
        return job

    input_channels = probe_channels(raw_path)
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

    if preset not in ("clean", "polished"):
        preset = "clean"

    # V3 mode dispatch. Diagnosis runs identically either way — a mode changes
    # what is applied, not what was measured — so the report and the Advanced
    # Inspector stay meaningful for both paths.
    #
    # An explicit selection is never reinterpreted. DT-97 shipped this as a
    # silent coercion to None, which meant a typo ("modrn_rap") rendered the V2
    # chain and reported mode=null — the user asked for one thing and received
    # another with no signal that it had happened. Omitting `mode` is still a
    # valid request for the V2 path; only an explicit unknown value is refused.
    if mode is not None and mode not in list_modes():
        raise UnknownModeError(mode, list_modes())
    try:
        bundle = analyze_and_plan(str(normalized), report, asset_id=name,
                                  preset=preset, mode=mode, intensity=intensity)
    except (KeyError, ValueError) as exc:
        job = Job(id=job_id, name=name, status=STATUS_FAILED,
                  message=f"Invalid mode selection: {exc}", workdir=workdir)
        _JOBS[job_id] = job
        return job

    _, advisory = diagnose_advisory(str(normalized), asset_id=name)
    processed = workdir / "after.wav"
    macro_summary: dict = {"changed": [], "inert": []}
    gain_staging: dict | None = None
    if bundle.is_v3:
        # EXPORT staging: the delivered file lands at an intended level rather
        # than wherever the chain happened to leave it.
        macro_values = macros if isinstance(macros, dict) else parse_macros(macros)
        execution = render_mode(str(normalized), str(processed), bundle.mode,
                                bundle.intensity, stage=GainStage.EXPORT,
                                macros=macro_values)
        # Surface what the stage did. A clamped makeup means the chain left the
        # signal more than MAX_MAKEUP_DB below target, which is a fact about the
        # render worth seeing rather than inferring from the output level.
        gain_staging = next(
            (dict(a.parameters) for a in execution.applied
             if a.objective_id == "output_safety"), None)
        _, macro_report = apply_macros(build_graph(bundle.mode, bundle.intensity),
                                       macro_values)
        macro_summary = macro_report.to_dict()
    else:
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
        preset=preset,
        mode=bundle.mode,
        intensity=bundle.intensity,
        channels=probe_channels(processed) or 1,
        macros=macro_summary,
        gain_staging=gain_staging,
        delivery=measure_delivery(str(processed)).to_dict(),
        before_preview_path=before_preview if previews_matched else None,
        after_preview_path=after_preview if previews_matched else None,
        previews_matched=previews_matched,
        report_markdown=report_md,
        objectives=tuple(o.goal for o in bundle.plan.objectives),
        warnings=evaluation.warnings + (
            ("stereo_input_summed_to_mono",) if (input_channels or 1) > 1 else ()),
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
