# DrakoTune — Post-Dataset-Research Repository Audit

> Audit performed 2026-07-10 against the live repository and the public dataset
> research report (`docs/research/PUBLIC_VOCAL_AUDIO_DATASET_RESEARCH.md`).
> Docs-only session: **no code behavior was changed.**

- **Repo:** `Born2tweak/DrakoTune` @ `064be0d` ("M20: batch processing"), branch `main`, synced with `origin/main` (fast-forwarded from `649cc7b`, +20 commits).
- **Git status at audit start:** clean (no local modifications, no untracked work discarded).
- **Test evidence this session:** `python -m pytest -q` → **253 passed, 2 warnings, 39.53s** (exit 0). `python scripts/audio_regression.py` → **6 fixtures match goldens** (exit 0). CLI help verified; v2 decision engine is the default (`--plan` is a no-op, `--legacy`/`--generic` are fallbacks).
- **Local checkout path:** `C:\Users\acetu\Downloads\DrakoTune` (not the previously expected `C:\Users\acetu\DrakoTune`).

## 1. Executive audit summary

The repository is **far ahead of the assumptions in the original PoC description**. Milestones M00–M20 are complete: the product is no longer "FFmpeg + a fixed Pedalboard chain" but a layered deterministic system with an observation/interpretation split, a confidence-gated decision engine, a bounded plan executor, before/after evaluation, a report engine, a FastAPI web skeleton, batch processing, a synthetic calibration harness, and CI audio regression.

What it does **not** have is exactly what the dataset research supplies the ingredients for:

1. **No real-vocal evidence.** All calibration and regression run on synthetic fixtures. The only real vocal ever processed ("headlock") exists as untracked local WAVs with no documented listening results. M17's own completion note flags "real-vocal calibration and a subjective listening study" as open.
2. **No dataset layer at all.** No `data/` directory, no manifests, no licensing ledger, no governance policy.
3. **No clean-reference metrics.** Evaluation compares before/after on internal deltas; there is no concept of a clean reference, so SI-SDR/ViSQOL-class validation is impossible today.
4. **No loudness-matched listening exports.** Evaluation *warns* about loudness bias (good) but the exported before/after pair is not loudness-matched, so any informal listening is biased.
5. **No listening-test protocol or results schema.**

**Conclusion:** the next phase is not more DSP or more diagnosis — it is the evidence layer: dataset governance → evaluation corpus → loudness-matched comparison + reference metrics → blinded listening. The original product question remains **unanswered** and is now answerable.

## 2. Repository structure (audited)

```
src/ingestion/preflight.py      structured blockers (silent / too-short / corrupt / format)
src/diagnostics/safety.py       peak, true-peak (dBTP), headroom, DC offset, clipping ratio, silence %
src/diagnostics/loudness.py     integrated LUFS (BS.1770-4 via pyloudnorm, M18), RMS, crest factor,
                                dynamic range, frame consistency CV
src/diagnostics/spectral.py     v1.1.0 — 7 observations (rumble/mud/harsh/sibilance/air ratios,
                                centroid, noise floor) + interpretations with confidence caps
                                (single-metric 0.6, corroborated 0.9) and the M17 mud centroid gate
src/decision/safety_rules.py    block/allow enhancement decisions
src/decision/planner.py         issue→spec table; confidence bands (HIGH full / MEDIUM 0.6× /
                                LOW report-only); 5 conflict rules; ProcessingPlan output
src/dsp_engine/processors.py    7 bounded Pedalboard processors with safe ranges + clamping
src/dsp_engine/executor.py      plan executor; attenuate-only output ceiling (M19 bug fix)
src/evaluation/evaluate.py      before/after deltas, LUFS delta, per-objective pass/fail,
                                loudness-bias and output-clipping warnings
src/reports/report_engine.py    findings/actions/limitations report (markdown)
src/orchestration.py            analyze_and_plan bundle
src/webapp/                     FastAPI upload → job → before/after playback → report (ADR 0001)
src/batch/runner.py             folder batch with per-file reports + summary (M20)
src/calibration/harness.py      synthetic labeled samples (5 issues, strong+clean) → FP/FN stats
src/dsp/                        LEGACY: Alpha-1/2.x monolith (diagnose.py 698 loc, pipeline.py) —
                                kept as --legacy/--generic fallbacks
fixtures/                       deterministic synthetic fixture library + expected/ + regression/
scripts/                        run_alpha, batch, calibrate, ab_compare, audio_regression
tests/                          21 files, 253 tests
.github/workflows/ci.yml        pytest + audio regression on ubuntu, Python 3.12
```

## 3. Findings classification

**Implemented & validated (synthetically):** preflight; safety/loudness/spectral diagnostics; decision engine confidence gating; bounded execution; output ceiling; evaluation warnings; report; CI regression on 6 goldens; batch; web skeleton.

**Implemented but unvalidated on real audio:** every diagnosis threshold (calibrated only on *strong* synthetic positives + clean controls — no graded severities, no real vocals); the adaptive plan's audible benefit vs legacy vs generic (A/B guard checks safety/objectives, explicitly *not* subjective quality); the noise gate's behavior on breath/word tails; harshness/sibilance cut amounts.

**Experiment-only / legacy:** `src/dsp/` monolith (diagnose 7-category engine, alpha22 STFT refinement) — superseded as default but still the `--legacy` path; `output/headlock_*.wav` (untracked, undocumented informal test).

**Missing:** dataset layer (governance, manifests, corpus); clean-reference metrics; loudness-matched listening exports; listening-test protocol/results; reverb, hum, plosive, breath, recording-level, tonal-imbalance diagnoses; severity-graded calibration; genre/register awareness (fixed 80–100 Hz HPF regardless of register — a low bass at E2≈82 Hz is at risk in principle, though the current cutoff bound of 80+20·s Hz keeps exposure small).

**Stale / housekeeping:** `docs/DRAKOTUNE_CONTEXT_EXPORT.md` (dated 2026-05-20, describes Alpha PoC + Next.js/Redis/Supabase stack that was never built; contradicted by ADR 0001); `.claude/agents/*` and cross-agent AutoClaw protocol files reference an orchestrator (`.autoclaw/`) that is now gitignored — local residue, not current process; `docs/05-implementation-plan.md` already correctly marked SUPERSEDED.

**Unsafe (claims-wise), currently mitigated:** the pilot docs (M16) already gate overclaiming well; nothing in-product claims "professional quality." Keep it that way — see the validation plan's permitted-claims list.

## 4. Track findings (A–L condensed)

- **A — Real-vocal validation:** Not performed. No blinded listening, no loudness matching, no multi-singer/genre/mic coverage, no legally documented test audio. The product question is open. → M22–M24.
- **B — Dataset governance:** Nothing exists. Required before any corpus lands locally: tier policy, manifests, gitignore rules, manual-approval checkpoints (DAMP email agreement; Zenodo click-through; Cambridge-MT education terms). → M21 (see `docs/data/DATASET_GOVERNANCE.md`).
- **C — Diagnosis reliability:** Architecture is right (observation/interpretation split, versioned analyzers, confidence caps, corroboration). Calibration is binary (strong/clean) and synthetic-only; M17 already caught one 100% FP (mud). Reverb, hum, plosive, level diagnoses absent. Verdict: current five spectral/loudness issues may keep controlling DSP **within existing bounded strengths**; any new diagnosis enters as **advisory-only** until it passes graded-severity calibration. → M25.
- **D — Adaptive DSP:** Generic, legacy-adaptive, and v2 paths all preserved (good baselines). Params bounded and clamped; output ceiling attenuate-only. Unknowns: gate release on breath/word tails, compressor pumping on real dynamics, cumulative EQ dulling, double-processing already-mixed vocals (no detector). Freeze new processors until the per-defect benchmark exists. → M26+.
- **E — Metrics:** Have: LUFS, RMS, crest, DR, consistency CV, true peak, dBTP headroom, DC, clipping ratio, silence %, 5 band ratios, centroid, noise floor. Missing: SI-SDR (trivial), SNR vs reference, ViSQOL/DNSMOS/NISQA (optional heavy deps), SRMR. Rule adopted: speech-trained no-reference metrics are developer-only proxies, never product-facing, never proof of singing quality. → M23.
- **F — Listening tests:** None. Smallest credible design: blinded, loudness-matched pairwise A/B with catch trials, ≥8 listeners, ~100–150 clips, pre-registered criteria (validation plan §29-equivalent). File-based exports + a results CSV schema suffice; **no new UI is required** to start. → M24.
- **G — Product/UX:** CLI + web + batch already exist and are honest about limitations. A frontend rebuild is NOT justified; the only near-term UX work that serves validation is loudness-matched preview export and per-defect report language. → M27.
- **H — Reports/visualization:** report engine v1 answers "what was detected/applied/limited"; lacks per-defect before/after deltas vs corpus norms, unfixable-issue and rerecord guidance. → M27.
- **I — Expanded processors:** de-esser is the leading candidate (sibilance is currently a static PeakFilter cut — real risk of lisping/dulling); hum notch and plosive control next; broadband denoise later via permissively licensed DeepFilterNet (MIT/Apache) rather than gate escalation; dereverberation deferred (no deterministic solution; detect-and-disclose instead). Every processor requires a validated failure mode from M24 evidence first. → M28+.
- **J — Rap/bedroom coverage:** the research confirms no public dataset covers the product's own target genre (docs/research/underground_vocal_engineering_reference.md targets underground rap). Claims must be genre-scoped until a consented in-house mini-corpus exists. → M29 + proprietary strategy.
- **K — Licensing:** runtime deps: pedalboard **GPL-3.0** (fine for local/server use; blocks distributing a closed-source desktop binary — legal checkpoint before any packaged distribution), numpy/BSD, soundfile/BSD (libsndfile LGPL), librosa/ISC, pyloudnorm/MIT, fastapi/MIT, ffmpeg (system; LGPL/GPL build-dependent — document the build used before distribution). Dataset licenses: per governance tiers. No pretrained models in use today (keeps provenance clean).
- **L — Proprietary data:** begin **logging** evaluation/listening data now (it is free and becomes the preference dataset); begin **collecting artist audio** only at M29 with the consent protocol in the governance doc.

## 5. Aurelian installation status and integration decision

- No `AGENTS.md`, no `.aurelian/` in the repo.
- Equivalent systems already exist and are healthy: constitution-equivalent (`docs/04-ai-rules.md` + milestone guardrails in `CURRENT_MILESTONE.md`), canonical roadmap (CURRENT_MILESTONE + `docs/audit/M00_baseline_audit.md` reconciliation), decision records (`docs/decisions/` ADRs), evidence discipline (per-milestone completion reports, CI regression), research traceability (docs/research/).
- Aurelian's own install guide instructs merging into existing instruction systems rather than duplicating.

**Decision: reference-only integration (no scaffold install).** Aurelian remains the *operator-level* OS (loaded globally); DrakoTune keeps its existing constitution/roadmap/ADR system as the *project-level* source of truth. The gaps Aurelian's template would have filled are adopted as native DrakoTune docs created in this session: risk register, research-to-execution map, dataset governance, validation plan, research gaps. Recorded as ADR 0002. Do **not** add a second constitution, second roadmap, or `.aurelian/` state directory — that is exactly the drift the task prohibits.

## 6. Protected contracts (do not break in the next phase)

- `ProcessingPlan` / `Observation` / `Interpretation` / `EvaluationResult` versioned shapes (`src/shared_types/`).
- Bounded processor safe ranges + clamping (`src/dsp_engine/processors.py`).
- Confidence-controls-automation law (LOW → report-only).
- Attenuate-only output ceiling (no makeup gain — M19 regression).
- CI golden fixtures (regenerate only with an evidence-backed analyzer version bump, as M17 did).
- Original audio never overwritten; `output/*.wav` never committed.

## 7. Likely edit surfaces for the next milestones

`data/` (new), `fixtures/degradations/` (new), `src/evaluation/` (SI-SDR, loudness-matched export), `scripts/` (corpus build, benchmark run, listening-session prep/analysis), `docs/validation/`, `docs/data/`, `tests/` (new suites), `pyproject.toml` (optional `eval` extra), `.gitignore` (data rules).

## 8. Stale assumptions corrected by this audit

| Assumed (prompt / old docs) | Reality |
|---|---|
| PoC-only pipeline (fixed chain) | M00–M20 layered system, v2 decision engine default |
| `src/shared_types.py` single file | `src/shared_types/` package, 8 modules |
| No web layer | FastAPI app + security baseline + pilot runbook exist |
| RMS-only loudness | Real BS.1770-4 integrated LUFS since M18 |
| No CI | GitHub Actions: pytest + audio regression |
| Roadmap conflict unresolved | 05-implementation-plan already marked SUPERSEDED |
| Repo at `C:\Users\acetu\DrakoTune` | Repo at `C:\Users\acetu\Downloads\DrakoTune` |
