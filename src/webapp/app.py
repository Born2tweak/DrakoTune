"""FastAPI web skeleton for DrakoTune (M12).

Implements the spec's core API concepts (upload, job status, playback, report)
plus a minimal server-rendered UI so a local user can upload a sample and view
the before/after result and report. Audio-first: the result page leads with the
before/after players. No accounts, billing, or AI (out of scope).
"""

import html

from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from src.webapp.jobs import (
    STATUS_COMPLETED,
    audio_path,
    get_job,
    process_upload,
)

app = FastAPI(title="DrakoTune", version="0.1.0")

_UPLOAD_PAGE = """<!doctype html>
<title>DrakoTune</title>
<h1>DrakoTune</h1>
<p>Upload a raw vocal (WAV/MP3). DrakoTune will diagnose, process conservatively,
and show a before/after with an explanation. Not a professional mix.</p>
<form action="/upload" method="post" enctype="multipart/form-data">
  <input type="file" name="file" accept="audio/*" required>
  <button type="submit">Analyze</button>
</form>
"""


def _result_html(job) -> str:
    if job.status != STATUS_COMPLETED:
        detail = html.escape(job.message or job.status)
        players = ""
        if job.before_path:
            players = ('<h2>Original</h2>'
                       f'<audio controls src="/api/audio/{job.id}/before"></audio>')
        return (f"<!doctype html><title>DrakoTune — {html.escape(job.name)}</title>"
                f"<h1>{html.escape(job.name)}</h1>"
                f'<p><strong>Status: {html.escape(job.status)}</strong></p>'
                f"<p>{detail}</p>{players}"
                '<p><a href="/">Try another file</a></p>')

    report_html = html.escape(job.report_markdown)
    return (
        f"<!doctype html><title>DrakoTune — {html.escape(job.name)}</title>"
        f"<h1>{html.escape(job.name)}</h1>"
        '<h2>Before / After</h2>'
        f'<p>Original<br><audio controls src="/api/audio/{job.id}/before"></audio></p>'
        f'<p>Processed<br><audio controls src="/api/audio/{job.id}/after"></audio></p>'
        f"<h2>Report</h2><pre>{report_html}</pre>"
        '<p><a href="/">Try another file</a></p>'
    )


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _UPLOAD_PAGE


@app.post("/api/audio/upload")
async def api_upload(file: UploadFile) -> JSONResponse:
    data = await file.read()
    job = process_upload(file.filename or "vocal", data)
    return JSONResponse(job.public_dict())


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
    return JSONResponse(job.public_dict())


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_page(job_id: str):
    job = get_job(job_id)
    if job is None:
        return HTMLResponse("<h1>Job not found</h1>", status_code=404)
    return HTMLResponse(_result_html(job))


@app.get("/api/audio/{job_id}/{which}")
def serve_audio(job_id: str, which: str):
    path = audio_path(job_id, which)
    if path is None:
        return JSONResponse({"error": "audio_not_found"}, status_code=404)
    return FileResponse(str(path), media_type="audio/wav", filename=f"{which}.wav")
