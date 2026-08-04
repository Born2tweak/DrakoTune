# DrakoTune web service — container image for Fly.io (or any Docker host).
#
# Python 3.12 is the validated target (CI runs 3.12; numba/llvmlite/scipy all
# ship manylinux wheels for it). FFmpeg (preprocessing) and libsndfile
# (soundfile) are the two native dependencies.
#
# The project has no packaging config in pyproject.toml (it runs from source
# via PYTHONPATH, both locally and in CI). We reproduce that exactly here:
# install the declared dependencies explicitly, then run uvicorn from /app
# with src/ on the path. No reliance on setuptools package auto-discovery.

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Runtime dependencies. Version floors mirror pyproject.toml [project] +
# [project.optional-dependencies].web (source of truth). scipy/numba/llvmlite
# arrive transitively via librosa.
RUN pip install --no-cache-dir \
    "pedalboard>=0.9.0" \
    "numpy>=1.24.0" \
    "soundfile>=0.12.0" \
    "librosa>=0.10.0" \
    "pyloudnorm>=0.1.1" \
    "fastapi>=0.110.0" \
    "uvicorn>=0.29.0" \
    "python-multipart>=0.0.9"

COPY src ./src

# Operational defaults (overridable via `fly secrets` / env):
#   DRAKOTUNE_MAX_UPLOAD_MB — reject uploads larger than this (memory guard).
#   DRAKOTUNE_SECRET        — HMAC key for signed audio URLs (set in prod so
#                             playback links survive a restart).
#
# KEEP IN STEP with app.MAX_UPLOAD_MB and MAX_UPLOAD_MB in static/app.js. This
# value silently won over the Python default on 2026-08-04: the code default was
# raised to 160 but production kept rejecting a 66.8 MB take at 413, because the
# image still pinned 50 here. Three places is two too many, but until the client
# learns the limit from /api/modes, all three must be changed together.
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    DRAKOTUNE_MAX_UPLOAD_MB=160

EXPOSE 8080

# Single worker on purpose: the job store is in-memory, so every request for a
# job must reach the same process. Scale by keeping ONE machine, not many.
CMD ["uvicorn", "src.webapp.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
