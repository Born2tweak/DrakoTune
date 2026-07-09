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
(see [`docs/PILOT.md`](docs/PILOT.md)).

## Adaptive post-M16 milestones (from the roadmap's Future list + flagged debts)

| Milestone | Status |
|-----------|--------|
| M17 — Calibration harness (calibrated confidence) | ✅ complete |
| M18 — Real integrated LUFS (BS.1770) | ✅ complete |
| M19 — v2 decision engine is CLI default (A/B guard) | ✅ complete |
| M20 — Batch processing | ✅ complete |

M20: `python scripts/batch.py <input_dir> --output-dir out/` processes a folder
of vocals → per-file `before/after/report.md` + a `summary.json`/`summary.md`
index; blocked/failed files are recorded, never fatal.

M19 note: the A/B work found and fixed a real bug — the output-safety "limiter"
(pedalboard, with makeup gain) was *inflating loudness* (quiet input −10→−5 dB).
Replaced with an attenuate-only ceiling. v2 is now the default CLI engine;
`--legacy` / `--generic` remain as fallbacks.

M17 note: the harness (`python scripts/calibrate.py`) surfaced a 100%
false-positive rate for muddiness on clean harmonic voices; fixed with an
evidence-based centroid gate (spectral analyzer 1.0.0 → 1.1.0), goldens
regenerated. Still open: real-vocal calibration and a subjective listening study.

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
