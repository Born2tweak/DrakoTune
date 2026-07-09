# DrakoTune Pilot Readiness (M16)

A checklist and runbook for a **controlled** pilot. This is not a public launch.

## Status: ready for controlled pilot

| Requirement | Status |
|---|---|
| Main workflow works end-to-end | ✅ CLI (`--plan`) and web (upload → before/after → report) |
| Deterministic core with regression guard | ✅ 200+ tests + CI audio-regression fingerprints |
| Private storage & signed access | ✅ M13 (see `docs/security.md`) |
| Privacy policy draft | ✅ `docs/PRIVACY.md` (draft) |
| Known limitations visible to users | ✅ every report + result page + landing page |
| Feedback capture | ✅ `POST /feedback` + result-page form |
| Rollback procedure | ✅ below |

## How to run the pilot

```bash
pip install -e ".[web,dev]"
export DRAKOTUNE_SECRET="<random-32-bytes-hex>"        # required in shared deploys
export DRAKOTUNE_FEEDBACK_LOG="./pilot_data/feedback.jsonl"  # optional durable feedback
python -m uvicorn src.webapp.app:app --host 127.0.0.1 --port 8000
```

Keep access limited (localhost, a private link, or an allowlist). Do not expose
publicly during the pilot.

## Guardrails against overclaiming

The single biggest risk is users treating DrakoTune as a professional mix. Every
surface must say what it is not:

- Landing page: "What this is — and isn't".
- Result page: Limitations section + "enhancement limited for safety" notices.
- Footer on every page: "not a professional mix or mastering engineer".
- Reports: standing limitations (uncalibrated thresholds, synthetic fixtures, no
  subjective listening validation, RMS-not-LUFS).

Do not describe the pilot as "secure", "production-ready", or "professional".

## Feedback

- In-memory + optional JSONL (`DRAKOTUNE_FEEDBACK_LOG`).
- Captures helpful yes/no + optional comment, tied to a job id. No audio, no PII.
- Review regularly; feed genuine findings into the research-debt register, not
  into ad-hoc threshold tweaks.

## Rollback procedure

1. **Limit access first:** take down the private link / revoke allowlist so no
   new uploads arrive.
2. **Disable the web layer:** stop the uvicorn process. The deterministic core is
   unaffected and still runs via the CLI
   (`python scripts/run_alpha.py <file> --plan`).
3. **Revert code if needed:** `git revert <commit>` on `main` (each milestone is a
   separate commit) or check out the last known-good tag; CI must be green.
4. **Purge data if required:** delete the work root
   (`<temp>/drakotune_web/`) and any `pilot_data/` feedback log.
5. **Communicate limits honestly** to pilot users; do not claim data was
   protected beyond the `docs/security.md` baseline.

## Not in scope for the pilot

Public launch, user accounts, billing, AI features, third-party audio services,
and any claim of professional-grade results.
