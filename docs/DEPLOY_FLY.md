# Deploying DrakoTune to Fly.io

The web service is a FastAPI app with native audio dependencies (FFmpeg,
pedalboard, librosa, soundfile). It does **not** run on Vercel/Netlify/serverless
(≈1 GB of deps vs a 250 MB function limit, a native FFmpeg binary, and an
in-memory job store that needs a persistent process). A single container host
is the correct target; this guide uses **Fly.io**.

Files in this repo that make it deployable: `Dockerfile`, `fly.toml`,
`.dockerignore`, and the `/health` endpoint.

> **Public-exposure note.** Per the product owner's decision this deploys
> **fully public with no login gate**. There is no authentication. Because
> the owner is cost-sensitive, it does carry real **abuse/cost protection**
> (M44, see below): per-IP rate limits, a server-wide concurrency cap, a
> proxy-level request cap, an "experimental pilot" banner, and a 50 MB upload
> cap. `docs/PILOT.md` recommends keeping access private; going public is an
> explicit, owner-approved override, mitigated by the limits below.

## One-time setup

1. **Install flyctl** (the Fly CLI):
   - Windows (PowerShell): `pwsh -c "iwr https://fly.io/install.ps1 -useb | iex"`
   - macOS/Linux: `curl -L https://fly.io/install.sh | sh`
2. **Sign in / create an account:** `fly auth signup` (or `fly auth login`).
   A payment card is required even on the free allowances.

## Deploy

From the repo root (`C:\Users\acetu\Downloads\DrakoTune`):

```bash
# 1. Register the app + pick a unique name and region. --no-deploy so we can
#    review before the first build. Accept "use existing fly.toml / Dockerfile".
fly launch --no-deploy

#    If the name "drakotune" is taken, flyctl will prompt for a new one and
#    rewrite the `app = ...` line in fly.toml. That's expected.

# 2. (Recommended) set a stable signing secret so playback links survive a
#    machine restart. Without it, a fresh random key is generated per process.
fly secrets set DRAKOTUNE_SECRET=$(python -c "import secrets;print(secrets.token_hex(32))")

# 3. Build the image on Fly's builders and release it.
fly deploy

# 4. Pin to exactly ONE machine (the job store is in-memory).
fly scale count 1

# 5. Open it in the browser.
fly open
```

`fly deploy` typically takes 3–6 minutes on the first run (it compiles nothing,
but pulls the manylinux wheels for numpy/scipy/numba/llvmlite/librosa).

## Verify

```bash
fly status                       # 1 machine, "started"
curl https://<your-app>.fly.dev/health   # -> {"status":"ok","service":"drakotune"}
```

Then upload a short WAV/MP3 through the UI and confirm the before/after players
and report render.

## Abuse / cost protection (M44)

Three independent layers, all active with sane defaults out of the box —
nothing to configure to get protection, only to adjust it:

| Layer | Where | Default | Purpose |
|---|---|---|---|
| Proxy request concurrency | `fly.toml` `[http_service.concurrency]` | soft 8 / hard 16 | Fly itself queues (soft) then rejects (hard) before requests reach the app |
| Per-IP rate limit | `src/webapp/ratelimit.py` (middleware) | 5 uploads/min, 60 requests/min per IP | Stops one client (or a simple script) from hammering the endpoint |
| Server-wide job concurrency | `src/webapp/ratelimit.py` (`job_slot`) | 2 concurrent DSP jobs | Caps CPU time in flight regardless of how many different IPs are asking |

The `/health` check is exempt from the per-IP limiter so the container
orchestrator's own probe can never be rate-limited into a false "unhealthy".

Tune via secrets (each takes effect on next request, no redeploy needed):

```bash
fly secrets set DRAKOTUNE_RATE_LIMIT_UPLOADS_PER_MIN=3   # tighter
fly secrets set DRAKOTUNE_RATE_LIMIT_REQUESTS_PER_MIN=30
fly secrets set DRAKOTUNE_MAX_CONCURRENT_JOBS=1           # stricter cost ceiling
```

A client past the per-IP limit gets `429` with a `Retry-After` header; past
the concurrency cap gets `503` ("server busy, try again shortly") — both are
fast, cheap responses, not queued processing.

**Caveat:** limiter state is in-memory and per-process. It resets on every
restart/redeploy/cold-start-from-scale-to-zero, and (by design, single
instance) is not shared across machines — which is fine since you must run
exactly one machine anyway (see below).

**Hard spend ceiling:** Fly has no built-in dollar cap in the CLI. If you
want an absolute stop, set a billing alert/limit in the
[Fly dashboard billing settings](https://fly.io/dashboard/personal/billing)
in addition to the limits above.

## Operating notes

- **Single instance only.** Never `fly scale count 2+` — a second machine can't
  see jobs created on the first, so the result page would 404 intermittently.
- **Cost / idle:** `auto_stop_machines = "stop"` (in `fly.toml`) scales to zero
  when idle; the next request cold-starts it (a few seconds while librosa/numba
  import). Set `min_machines_running = 1` to keep it always warm.
- **Memory:** 2 GB handles a ~5-minute vocal. If you see OOM kills in
  `fly logs`, either lower `DRAKOTUNE_MAX_UPLOAD_MB` or bump `[[vm]] memory`.
- **Upload cap:** change with `fly secrets set DRAKOTUNE_MAX_UPLOAD_MB=25`.
- **Logs:** `fly logs`. **Redeploy after a code change:** `fly deploy`.
- **Tear down:** `fly apps destroy <your-app>`.

## What is NOT deployed

- The blinded listening runner (`/listen`) stays dorment unless you set
  `DRAKOTUNE_LISTENING_SESSION` — keep it unset on a public host (it would serve
  local session audio).
- No datasets, corpora, or evaluation reports are in the image (`.dockerignore`
  excludes `data/`, `reports/`, `docs/`, `tests/`, `scripts/`, `fixtures/`).

## GPL note

pedalboard is GPL-3.0. Running it as a **network service does not trigger
source-disclosure** (that obligation is AGPL-specific). Hosting is fine;
distributing a binary that links pedalboard would be the case to review.
