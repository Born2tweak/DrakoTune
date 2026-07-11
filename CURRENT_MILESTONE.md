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

## Next phase: evidence layer (M21+)

**Canonical M21+ roadmap:**
[`docs/implementation/DRAKOTUNE_MASTER_EXECUTION_ROADMAP.md`](docs/implementation/DRAKOTUNE_MASTER_EXECUTION_ROADMAP.md)
(derived from the post-research audit
[`docs/audit/DRAKOTUNE_POST_DATASET_RESEARCH_AUDIT.md`](docs/audit/DRAKOTUNE_POST_DATASET_RESEARCH_AUDIT.md)
and the dataset research
[`docs/research/PUBLIC_VOCAL_AUDIO_DATASET_RESEARCH.md`](docs/research/PUBLIC_VOCAL_AUDIO_DATASET_RESEARCH.md)).

| Milestone | Status |
|-----------|--------|
| M21 — Dataset governance & evidence scaffolding | ✅ complete |
| M22 — Evaluation corpus v1 + synthetic degradation library | ✅ complete |
| M23 — Evaluation harness v2 (loudness-matched A/B, SI-SDR, per-defect benchmark) | 🔜 next |
| M24 — Blinded listening test v1 (**alpha verdict**) | planned |
| M25 — Diagnosis calibration v2 (graded severities; new diagnoses advisory-only) | planned (∥ M24) |
| M26 — Evidence-driven DSP tuning + do-no-harm CI gates | gated on M24+M25 |
| M27 — Report & product-experience upgrade | gated on M24 |
| M28 — Expanded processors (de-esser first; each individually gated) | gated on M26 |
| M29 — Genre coverage & proprietary mini-corpus (consent protocol first) | gated |

M21 note: manifest schema v1.0.0 + validator (`src/data_governance/`), 8 dataset
manifests (5×Tier A, 2×Tier B, 1×Tier C — metadata only, nothing downloaded),
attribution ledger, gitignore rules for `data/{local,restricted,derived}/`, and
git-index guards (no audio outside `fixtures/`, no tracked file > 1 MB).
Evidence: 261 tests pass (8 new), audio regression 6/6 — no behavior change.
Manual checkpoints before M22 downloads: DAMP email agreement, Zenodo requests,
SingVERSE HF license read (governance §4).

M22 part 1 note: seeded degradation recipe library (`fixtures/degradations.py`,
v1.0.0) implementing the validation-plan grid — 9 families (noise×3 kinds, hum,
clipping, reverb via synthetic seeded IRs, harshness, sibilance, proximity,
low_level, codec), 24 recipes, bit-exact regeneration guaranteed for all
non-codec families. Evidence: 271 tests pass (10 new), audio regression 6/6.
M22 part 2 note (corpus-v1 built): human downloaded VocalSet + vocadito
(sha256 recorded in manifests; extracted to `data/local/`). The grid is **27
recipes** (part-1 commit message said 24 — corrected here).
`python scripts/build_corpus.py --ci-fixtures` → **80 clean clips** (40
VocalSet across all 20 singers × 2 techniques + 40 vocadito), normalized to
−23 LUFS, **160 degraded pairs** (round-robin; every recipe covered; `--full-grid`
available), frozen in `data/corpus/corpus-v1.json` (digests committed; audio
regenerable, gitignored). 3 Tier A CI fixtures in `fixtures/audio_real/` (≤1 MB
each, attributed). Evidence: 278 tests pass (7 new), audio regression 6/6.

Still-open manual checkpoints (optional extensions, not blockers):
- VoiceBank-DEMAND + MUSAN + OpenSLR-28: not yet downloaded (paired-speech
  control + real noise beds/IRs would upgrade the synthetic families).
- SingVERSE: read HF license, record in manifest, then download (real
  degraded/clean singing pairs — the strongest external validation set).
- DAMP: email agreement (real amateur recordings).
- LibriSpeech (~62 GB) was downloaded to `Downloads/` but is **not used**: it
  has no clean/noisy pairs and corpus-v1 needs none of it; it may be deleted
  or kept for future work. A 67 GB `Unconfirmed 736357.crdownload` in
  `Downloads/` is an incomplete browser download (unidentified).

Standing constraints: no new processors, no threshold tuning, no frontend
rebuild, no ML, no data collection before their gates (ADR 0002–0004,
`docs/RISK_REGISTER.md`, `docs/data/DATASET_GOVERNANCE.md`,
`docs/validation/DRAKOTUNE_ALPHA_VALIDATION_PLAN.md`).

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
