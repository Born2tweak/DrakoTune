"""FastAPI web skeleton for DrakoTune (M12).

Implements the spec's core API concepts (upload, job status, playback, report)
plus a minimal server-rendered UI so a local user can upload a sample and view
the before/after result and report. Audio-first: the result page leads with the
before/after players. No accounts, billing, or AI (out of scope).
"""

import os

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from src.webapp.feedback import record_feedback
from src.webapp.jobs import (
    audio_path,
    delete_job,
    get_job,
    process_upload,
)
from src.webapp import listening
from src.webapp.ratelimit import (
    ServerBusyError,
    client_ip,
    general_limiter,
    job_slot,
    upload_limiter,
)
from src.webapp.security import signed_url, verify
from src.webapp.templates import page, render_privacy, render_result, render_upload

app = FastAPI(title="DrakoTune", version="0.1.0")

# Operational safety for a public deployment (NOT access control): the pipeline
# holds whole files in memory (~180 MB per audio-minute, M36 benchmark), so an
# unbounded upload would OOM the container. Reject oversized bodies up front.
MAX_UPLOAD_MB = int(os.environ.get("DRAKOTUNE_MAX_UPLOAD_MB", "50"))
_MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

# Endpoints that trigger a DSP run (expensive; get the tight rate limit).
_UPLOAD_PATHS = frozenset({"/api/audio/upload", "/upload"})


@app.middleware("http")
async def _cost_guards(request: Request, call_next):
    """Combined size + rate-limit guard. Runs before any handler, including
    the health check (which is exempted so the container orchestrator's
    probe is never itself rate-limited into a false 'unhealthy')."""
    if request.url.path == "/health":
        return await call_next(request)

    if request.method == "POST":
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > _MAX_UPLOAD_BYTES:
            return JSONResponse(
                {"error": "file_too_large", "max_mb": MAX_UPLOAD_MB}, status_code=413)

    ip = client_ip(request.headers, request.client.host if request.client else "unknown")
    limiter = upload_limiter if request.url.path in _UPLOAD_PATHS else general_limiter
    allowed, retry_after = limiter.allow(ip)
    if not allowed:
        return JSONResponse(
            {"error": "rate_limited", "retry_after_seconds": round(retry_after, 1)},
            status_code=429, headers={"Retry-After": str(int(retry_after) + 1)})
    return await call_next(request)


@app.get("/health")
def health() -> JSONResponse:
    """Liveness probe (no DSP) for the container host's health check."""
    return JSONResponse({"status": "ok", "service": "drakotune"})


def _job_response(job) -> dict:
    """Public job payload with signed, time-limited playback URLs."""
    data = job.public_dict()
    urls: dict[str, str] = {}
    if job.before_path is not None:
        urls["before"] = signed_url(job.id, "before")
    if job.after_path is not None:
        urls["after"] = signed_url(job.id, "after")
    data["audio_urls"] = urls
    return data

@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return page("DrakoTune", render_upload())


@app.post("/api/audio/upload")
async def api_upload(file: UploadFile, preset: str = Form("clean")) -> JSONResponse:
    data = await file.read()
    try:
        with job_slot():
            job = process_upload(file.filename or "vocal", data, preset=preset)
    except ServerBusyError as exc:
        return JSONResponse({"error": "server_busy", "detail": str(exc)}, status_code=503)
    return JSONResponse(_job_response(job))


@app.post("/upload")
async def form_upload(file: UploadFile, preset: str = Form("clean")):
    data = await file.read()
    try:
        with job_slot():
            job = process_upload(file.filename or "vocal", data, preset=preset)
    except ServerBusyError as exc:
        return HTMLResponse(
            page("DrakoTune — busy", f"<h1>Busy right now</h1><p>{exc}. Please retry shortly.</p>"),
            status_code=503)
    return RedirectResponse(url=f"/jobs/{job.id}", status_code=303)


@app.get("/api/jobs/{job_id}")
def api_job(job_id: str) -> JSONResponse:
    job = get_job(job_id)
    if job is None:
        return JSONResponse({"error": "job_not_found"}, status_code=404)
    return JSONResponse(_job_response(job))


@app.delete("/api/jobs/{job_id}")
def api_delete_job(job_id: str) -> JSONResponse:
    if not delete_job(job_id):
        return JSONResponse({"error": "job_not_found"}, status_code=404)
    return JSONResponse({"deleted": job_id})


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_page(job_id: str):
    job = get_job(job_id)
    if job is None:
        return HTMLResponse(page("Not found", "<h1>Job not found</h1>"), status_code=404)
    # Prefer loudness-matched previews for the comparison players (ADR 0004).
    if getattr(job, "previews_matched", False):
        before_src = signed_url(job.id, "before_preview")
        after_src = signed_url(job.id, "after_preview")
    else:
        before_src = signed_url(job.id, "before") if job.before_path else None
        after_src = signed_url(job.id, "after") if job.after_path else None
    return HTMLResponse(page(f"DrakoTune — {job.name}", render_result(job, before_src, after_src)))


@app.get("/privacy", response_class=HTMLResponse)
def privacy() -> str:
    return page("DrakoTune — Privacy", render_privacy())


@app.post("/api/feedback")
def api_feedback(job_id: str = Form(...), rating: str = Form("up"), comment: str = Form("")) -> JSONResponse:
    entry = record_feedback(job_id, rating, comment)
    return JSONResponse({"ok": True, "rating": entry["rating"]})


@app.post("/feedback")
def form_feedback(job_id: str = Form(...), rating: str = Form("up"), comment: str = Form("")) -> RedirectResponse:
    record_feedback(job_id, rating, comment)
    return RedirectResponse(url=f"/jobs/{job_id}?thanks=1", status_code=303)


@app.get("/api/audio/{job_id}/{which}")
def serve_audio(job_id: str, which: str, exp: int = 0, sig: str = ""):
    # No public audio: a valid, unexpired signature is required.
    if not verify(job_id, which, exp, sig):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    path = audio_path(job_id, which)
    if path is None:
        return JSONResponse({"error": "audio_not_found"}, status_code=404)
    return FileResponse(str(path), media_type="audio/wav", filename=f"{which}.wav")


# --- Blinded listening-session runner (M43) --------------------------------

@app.get("/listen")
def listen(listener_id: str = "", listener_type: str = "listener"):
    session = listening.session_dir()
    if session is None:
        return HTMLResponse(page("DrakoTune — listening test",
                                 "<h1>No session configured</h1>"
                                 '<p class="hint">Set DRAKOTUNE_LISTENING_SESSION to a '
                                 "prepared session directory and restart.</p>"))
    trials = listening.trial_ids(session)
    if not listener_id:
        return HTMLResponse(page("DrakoTune — listening test",
                                 listening.render_start_page(len(trials))))
    remaining = [t for t in trials if t not in listening.answered_trials(session, listener_id)]
    if not remaining:
        return HTMLResponse(page("DrakoTune — listening test",
                                 listening.render_done_page(listener_id)))
    trial = remaining[0]
    a_src = signed_url(f"listen-{trial}", "A")
    b_src = signed_url(f"listen-{trial}", "B")
    return HTMLResponse(page(
        "DrakoTune — listening test",
        listening.render_trial_page(trial, len(remaining), len(trials),
                                    listener_id, listener_type,
                                    f"/listen/audio/{trial}/A?{a_src.split('?', 1)[1]}",
                                    f"/listen/audio/{trial}/B?{b_src.split('?', 1)[1]}")))


@app.post("/listen")
async def listen_submit(request: Request):
    session = listening.session_dir()
    if session is None:
        return JSONResponse({"error": "no_session"}, status_code=404)
    form = await request.form()
    try:
        listening.record_response(
            session,
            listener_id=str(form.get("listener_id", ""))[:40],
            listener_type=str(form.get("listener_type", "listener")),
            trial=str(form.get("trial", "")),
            preference=str(form.get("preference", "")),
            strength=str(form.get("strength", "")),
            artifacts=[str(a) for a in form.getlist("artifacts")],
            notes=str(form.get("notes", "")),
        )
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    from urllib.parse import quote
    return RedirectResponse(
        url=f"/listen?listener_id={quote(str(form.get('listener_id', '')))}"
            f"&listener_type={quote(str(form.get('listener_type', 'listener')))}",
        status_code=303)


@app.get("/listen/audio/{trial}/{side}")
def listen_audio(trial: str, side: str, exp: int = 0, sig: str = ""):
    session = listening.session_dir()
    if session is None or not verify(f"listen-{trial}", side, exp, sig):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    path = listening.stimulus_path(session, trial, side)
    if path is None:
        return JSONResponse({"error": "not_found"}, status_code=404)
    return FileResponse(str(path), media_type="audio/wav", filename=f"{trial}_{side}.wav")
