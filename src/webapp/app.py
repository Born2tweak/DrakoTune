"""FastAPI web skeleton for DrakoTune (M12).

Implements the spec's core API concepts (upload, job status, playback, report)
plus a minimal server-rendered UI so a local user can upload a sample and view
the before/after result and report. Audio-first: the result page leads with the
before/after players. No accounts, billing, or AI (out of scope).
"""

from fastapi import FastAPI, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from src.webapp.feedback import record_feedback
from src.webapp.jobs import (
    audio_path,
    delete_job,
    get_job,
    process_upload,
)
from src.webapp.security import signed_url, verify
from src.webapp.templates import page, render_privacy, render_result, render_upload

app = FastAPI(title="DrakoTune", version="0.1.0")


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
async def api_upload(file: UploadFile) -> JSONResponse:
    data = await file.read()
    job = process_upload(file.filename or "vocal", data)
    return JSONResponse(_job_response(job))


@app.post("/upload")
async def form_upload(file: UploadFile) -> RedirectResponse:
    data = await file.read()
    job = process_upload(file.filename or "vocal", data)
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
