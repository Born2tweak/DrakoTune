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
| M23 — Evaluation harness v2 (loudness-matched A/B, SI-SDR, per-defect benchmark) | ✅ complete |
| M24 — Blinded listening test v1 (**alpha verdict**) | 🟡 tooling complete; **awaiting ≥8 human listeners** (session prepared under `data/derived/listening/`) |
| M25 — Diagnosis calibration v2 (graded severities; advisory diagnoses) | ✅ complete |
| M26 — Evidence-based diagnosis recalibration + do-no-harm CI gates | ✅ complete (spectral 1.2.0) |
| M27 — Report engine v2 + loudness-matched web previews | ✅ complete |
| M28 — First gated processor: HumNotch (objective evidence; perceptual confirmation pending M24) | ✅ complete |
| M29 — Genre coverage & proprietary mini-corpus | 🟡 consent protocol DRAFTED (`docs/data/ARTIST_CONSENT_PROTOCOL.md`) — **blocked on human/legal approval** |

Evidence chain (all committed under `reports/evaluations/corpus-v1/`):
M23 benchmark (480 runs) → M25 confusion matrices → M26 recalibration
(rumble FP 57.5%→2.5%; sibilance recall 0%→50% strong; harshness strong
33%→67%; ΔSI-SDR improved in 15/21 cells, low_level/moderate −19→0 dB) →
M28 HumNotch behind a 0%-clean-FP promotion gate (hum_confirmed:
≥4 harmonics @ ≥100× contrast; advisory "hum" remains spec-less).

**Open human gates:** (1) M24 listeners — the alpha verdict and every
perceptual claim wait on this; (2) M29 consent-protocol legal approval;
(3) optional corpus upgrades (VoiceBank-DEMAND/MUSAN/OpenSLR-28 downloads,
SingVERSE license read, DAMP agreement).
De-esser remains **deferred** until M24 shows a sibilance failure mode
(sibilance detection itself only reaches 50% strong-recall — detector first).

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

## Post-M29 continuation (M30-M43)

| Milestone | Status |
|-----------|--------|
| M30 — Dynamic de-esser + post-compression guard (executor array processors) | ✅ complete |
| M31 — Self-auditing evaluation (residual-issue detection) + session/benchmark refresh | ✅ complete |
| M32 — Plosive detection | ✅ complete (**negative result** — observation-only; RG-6b) |
| M33 — Dynamics policy: CV recalibration (0.40→0.90), level-restore promotion, overcompression abstention | ✅ complete |
| M34 — Style presets: clean (default) / polished (**product-owner decision (b)**, ADR 0005) | ✅ complete |
| M35 — Tonal-balance detection | ✅ complete (**negative result** — profile committed as reference; RG-13) |
| M36 — Long-file performance benchmark (~0.07× realtime; ~180 MB/audio-min, linear) + budget gate | ✅ complete |
| M37 — CLI/batch parity (advisory + JSON manifest; batch --preset) | ✅ complete |
| M38 — Polished-preset objective benchmark + owner A/B export (`Downloads/drakotune_preset_ab/`) | ✅ complete |
| M39 — Webapp result page: preset badge + residual-issues card | ✅ complete |
| M40 — corpus-v2 evidence refresh (37-recipe grid) | ✅ complete |
| M41 — Stereo-input honesty advisory (summed-to-mono warning) | ✅ complete |
| M42 — Codec-artifact detection | ✅ complete (**insufficient evidence** — no detector; RG-14) |
| M43 — In-browser blinded listening runner (`/listen`, one URL per listener) | ✅ complete |

**corpus-v2 evidence freeze (reports/evaluations/corpus-v2/):** calibration —
hum/clipping/low_level/overcompression 100% recall, noise ≥93%, rumble FP
2.5%, overcompressed FP 10%; clean-preset v2 benchmark now shows **positive**
fidelity deltas where the chain acts: harshness/strong +2.0 dB, hum/strong
+9.2 dB (band −0.63), gain_jumps/strong +1.6 dB, low_level/moderate 0.0
(transparent restore), overcompression 0.0 (perfect abstention); output
clipping 0.0000 everywhere. Watch items: proximity detection 0/4 on this
grid assignment (n=4; was 4/4 on corpus-v1 — clip-dependent), reverb
estimator remains weak (known, research-only), sibilance moderate 25%.

**Compression policy: RESOLVED** — product owner chose (b); see ADR 0005 and
the M34/M38 rows. Matched clean-vs-polished pairs of the owner's own files
await their ears in `Downloads/drakotune_preset_ab/`.

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
