# Deploying DrakoTune to Fly.io

The web service is a FastAPI app with native audio dependencies (FFmpeg,
pedalboard, librosa, soundfile). It does **not** run on Vercel/Netlify/serverless
(≈1 GB of deps vs a 250 MB function limit, a native FFmpeg binary, and an
in-memory job store that needs a persistent process). A single container host
is the correct target; this guide uses **Fly.io**.

Files in this repo that make it deployable: `Dockerfile`, `fly.toml`,
`.dockerignore`, and the `/health` endpoint.

> **Public-exposure note.** Per the product owner's decision this deploys
> **fully public with no access gate**. The app has no authentication or
> rate limiting. It carries an "experimental pilot" banner and a 50 MB upload
> cap (memory guard, not access control). `docs/PILOT.md` recommends keeping
> access private; going public is an explicit, owner-approved override.

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
