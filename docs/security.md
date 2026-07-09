# Security & Privacy Notes (M13 baseline)

User audio is private creative material and is treated as sensitive by default.
This document records the baseline established in M13. It is a baseline, not a
completed production posture — open items are listed at the end.

## Storage

- Uploaded and processed audio is written under a private work root
  (`<temp>/drakotune_web/<job_id>/`), never inside the repo or a public directory.
- Files are reachable **only** through the app's controlled routes. There are no
  public audio URLs and no directory listing.

## Access control

- Every playback URL is an **HMAC-signed, time-limited capability**
  (`?exp=<unix>&sig=<hmac>`), minted per request with a default TTL of 1 hour.
- The audio route verifies the signature (constant-time compare) and expiry
  before serving; unsigned, tampered, expired, or wrong-resource requests get
  **403** — checked before existence, so a missing job is indistinguishable from
  a real one without a valid token.
- Signing secret comes from `DRAKOTUNE_SECRET`. If unset (dev only), a random
  per-process secret is used (`security.IS_EPHEMERAL == True`) and tokens do not
  survive a restart. **Set `DRAKOTUNE_SECRET` in any shared/production deployment.**

## Retention & cleanup

- `DELETE /api/jobs/{id}` removes the job and its working files.
- `cleanup_expired()` deletes jobs older than the retention window
  (`RETENTION_SECONDS`, default 1 hour).
- The entire work root is removed on process exit (`atexit`).

## Data handling

- No third-party service receives user audio (Bible rule). All processing is local.
- Reports avoid embedding secrets or PII; audio is not logged.

## Rollback

- The deterministic core runs fully offline via the CLI
  (`python scripts/run_alpha.py <file> --plan`); the web layer can be disabled
  without affecting local processing.

## Open items (not yet done)

- No user accounts / authentication or per-user authorization (jobs are not owned).
- No rate limiting or upload size/type hard limits at the edge.
- No persistent audit log.
- `cleanup_expired()` is not yet scheduled by a background task.
- Signed-URL secret rotation is manual.

These are tracked for production hardening (post-M16) and must not be assumed
complete. Do not describe DrakoTune as "secure" or "production-ready" on this
baseline alone.
