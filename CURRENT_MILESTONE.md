# Current Milestone Status

**Authoritative roadmap:** DrakoTune Implementation Roadmap (M00→M16), as
reconciled in [`docs/audit/M00_baseline_audit.md`](docs/audit/M00_baseline_audit.md).

| Milestone | Status |
|-----------|--------|
| M00 — Repository baseline & safety inventory | ✅ complete |
| M01 — Canonical versioned records + housekeeping | ✅ complete |
| M02 — Deterministic synthetic fixture library | ✅ complete |
| M03 — Preflight validation | ✅ complete |
| M04 — Technical-safety diagnostics | ✅ complete |
| M05 — Loudness & dynamics diagnostics | ✅ complete |
| M06 — Spectral/noise diagnostics (observation/interpretation split) | ✅ complete |
| M07 — Decision engine v1: safety rules | ✅ complete |
| M08 — Decision engine v1: objective selection | ✅ complete |
| M09 — Modular DSP plan execution (v2 engine) | ✅ complete |
| M10 — Before/after evaluation | ✅ complete |
| M11 — Report engine v1 | ✅ complete |
| M12 — Web app skeleton (FastAPI) | ✅ complete |
| M13 — Private storage & security baseline | ✅ complete |
| M14 — Product experience pass | ✅ complete |
| M15 — CI audio regression | ✅ complete |
| M16 — Pilot readiness | ✅ complete |

**Roadmap M00–M16 complete.** DrakoTune is ready for a *controlled* pilot
(see [`docs/PILOT.md`](docs/PILOT.md)). Next work is post-M16: threshold
calibration on real vocals, subjective listening study, and production hardening
(accounts, rate limits, audit log) — none of which should be claimed done yet.

The deterministic core is complete end-to-end: `--plan` runs diagnostics →
decision → bounded DSP → evaluation → report (written to `<name>_report.md`).

Web skeleton (FastAPI, reuses the core): `pip install -e ".[web,dev]"` then
`python -m uvicorn src.webapp.app:app --port 8000` and open http://localhost:8000
(upload → before/after playback → report). Framework rationale: ADR 0001.

The decision-driven v2 path (`--plan`) runs: diagnostics → decision → plan →
bounded DSP execution. The legacy adaptive chain remains the default until v2 is
A/B-validated on real vocals.

## What runs today

```
python scripts/run_alpha.py <input.wav> --output-dir output/ [--generic] [--force]
python -m pytest -q          # full suite
python fixtures/generate.py  # (re)generate fixtures
```

Pipeline: FFmpeg normalize → **preflight (blocks silent/too-short/corrupt)** →
diagnose (7 categories) → artifact scan → adaptive DSP → export before/after.
`process_audio` emits a versioned `processing_record`. Original audio is never
overwritten.

## Guardrails (every milestone)

- One milestone at a time; do not skip.
- Full test suite stays green; audio must not regress.
- No thresholds tuned just to pass tests.
- Each milestone ends with a completion report (changed / files / tests /
  evidence / not-verified / risks / next).
