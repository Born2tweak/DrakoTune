# DrakoTune Master Execution Roadmap (M21+)

> Canonical continuation of the DrakoTune Implementation Roadmap. M00–M20 are
> complete (history preserved in `CURRENT_MILESTONE.md` and per-milestone
> commits). This document specifies the next phase, derived from the
> post-research audit (`docs/audit/DRAKOTUNE_POST_DATASET_RESEARCH_AUDIT.md`)
> and the dataset research (`docs/research/PUBLIC_VOCAL_AUDIO_DATASET_RESEARCH.md`).
> `docs/05-implementation-plan.md` remains SUPERSEDED. There is exactly one
> roadmap: `CURRENT_MILESTONE.md` tracks status; this file holds the M21+ specs.

## 0. Strategic frame

The deterministic core (diagnose → decide → execute → evaluate → report) is
built and regression-guarded, but the original product question is still
**unanswered**: no real vocals, no blinded listening, no clean-reference
metrics have ever been used. The next phase therefore builds the **evidence
layer**, not more DSP. New processors, adaptive tuning, UI expansion, genre
presets, reference matching, and ML are all frozen behind evidence gates.

Superseded/kept-as-baseline: the legacy adaptive chain (`--legacy`) and generic
chain (`--generic`) are retained deliberately as A/B baselines through M24 —
do not delete them.

## 1. Milestone specifications

### M21 — Dataset governance & evidence scaffolding
- **Problem:** no legal/technical foundation exists for bringing any audio corpus near the repo; one accidental commit of restricted audio is an unrecoverable license breach (git history).
- **Value / why now:** unblocks every evaluation milestone; near-zero risk; mostly docs + schema + guards. **Why not later:** M22 cannot start safely without it. **Why not earlier:** the dataset research (which defines the tiers) did not exist.
- **Risk retired:** license contamination, git-history pollution, unreviewable data provenance. **Unlocks:** M22.
- **Prerequisites:** none (this session's docs are its research input).
- **In scope:** `data/` structure + `.gitignore` rules; manifest JSON schema + validator (`src/data_governance/` or `fixtures/`-adjacent, small); manifests for the 8 planned datasets (metadata only, `checksum: null`); `data/licenses/ATTRIBUTIONS.md`; a CI-safe test that fails if any file > 1 MB or any WAV/MP3 appears outside `fixtures/` in the git index.
- **Out of scope:** downloading anything; corpus building; new metrics.
- **Files:** `data/manifests/*.json`, `data/licenses/`, `.gitignore`, `tests/test_data_governance.py`, small validator module.
- **Contracts affected:** none (additive).
- **Dataset inputs:** none (metadata only). **Licensing:** defines the gates (ADR 0003).
- **Testing:** manifest schema validation tests; git-index guard test.
- **Evidence gate / completion:** tests green; `python -m pytest -q` full suite green; governance doc cross-linked from CURRENT_MILESTONE.
- **Rollback:** delete `data/`, revert commit. **Invalidated by:** discovery of an existing equivalent governance layer (none found in audit).

### M22 — Alpha evaluation corpus v1 + synthetic degradation library
- **Problem:** nothing real or realistically degraded to test on; calibration is binary-synthetic.
- **Value:** the substrate for every claim DrakoTune will ever make. **Why now:** governance exists (M21); research names exact sources. **Why not later:** M23–M25 all consume it.
- **Risk retired:** "works on sine waves only." **Unlocks:** M23, M24, M25.
- **Prerequisites:** M21. **Manual checkpoints:** DAMP email agreement; Zenodo requests; SingVERSE license read at download (human).
- **In scope:** `scripts/build_corpus.py` (verify checksums of *already-manually-downloaded* archives; slice/convert to 10–20 s mono 44.1 kHz clips; write corpus manifest); degradation recipe library per validation plan §2 (seeded; pedalboard/ffmpeg/numpy only — no new runtime deps); regeneration determinism test; a ≤ 25 MB Tier-A-derived CI fixture set (with attribution) added to `fixtures/`.
- **Out of scope:** metrics, listening tests, any threshold changes.
- **Files:** `scripts/build_corpus.py`, `fixtures/degradations/`, `data/manifests/corpus-v1.json`, tests.
- **Testing:** recipe determinism (same seed → same sha256); corpus manifest completeness; CI fixtures load.
- **Evidence gate:** corpus-v1 frozen and documented; all clips tier-labeled; suite green. **Claims limitation:** none yet — corpus existence proves nothing.
- **Rollback:** `data/derived/` is regenerable; delete and revert. **Invalidated by:** SingVERSE license prohibiting even internal evaluation (fallback: synthetic + DAMP + VoiceBank-DEMAND only) — record in manifest either way.

### M23 — Evaluation harness v2: loudness-matched comparison + reference metrics + per-defect benchmark
- **Problem:** current evaluation can't compare fairly (no loudness matching of exports) and can't use clean references (no SI-SDR); no per-defect aggregation.
- **Value:** turns the corpus into numbers; makes every future informal listen unbiased. **Why now:** consumes M22; required by M24 (listening pairs must be matched). **Why not earlier:** nothing to benchmark against.
- **Risk retired:** loudness bias; metric-blind DSP changes. **Unlocks:** M24, M25, M26.
- **In scope:** loudness-matched pair export (−23 LUFS / ≤ −1.5 dBTP, attenuate-preferred, refuse > 0.5 LU mismatch); SI-SDR + segmental SNR in `src/evaluation/`; `scripts/benchmark.py` running {generic, legacy, v2} engines over corpus-v1 → `reports/evaluations/.../benchmark.json` + `summary.md` (evaluation-matrix fields per validation plan §8); optional `[eval]` extra (DNSMOS/NISQA/ViSQOL) clearly labeled developer-only.
- **Out of scope:** changing any DSP/threshold in response to results (that is M26 — record findings only); UI.
- **Testing:** SI-SDR known-answer tests; loudness-match tolerance test; benchmark smoke test on CI fixtures.
- **Evidence gate:** benchmark report for corpus-v1 committed; per-defect table shows where v2 helps/harms objectively. **Claims limitation:** objective-only; no perceptual claims.
- **Rollback:** additive module; revert commit. **Invalidated by:** nothing foreseeable.

### M24 — Blinded listening test v1 (the alpha verdict)
- **Problem:** the product question is perceptual and has never been asked properly.
- **Value:** the single highest-credibility milestone; decides what DrakoTune may claim and what M26 must fix. **Why now:** corpus + matched exports exist. **Why not later:** every further DSP investment is speculative without it.
- **Risk retired:** shipping a product that doesn't audibly help. **Unlocks:** M26 tuning targets, claims policy activation, M28 processor decisions.
- **Prerequisites:** M22, M23. **Human gate:** ≥ 8 external listeners recruited.
- **In scope:** session builder (`scripts/listening_prepare.py`: randomized, blinded, catch trials, session config JSON); response CSV schema; `scripts/listening_analyze.py` (binomial tests, CIs, Krippendorff's α, per-defect verdicts vs the **pre-registered** criteria in the validation plan §6); results committed under `reports/evaluations/`.
- **Out of scope:** new UI (file-based sessions suffice); fixing anything found (log it).
- **Evidence gate:** listening report with pass/fail per defect family against pre-registered criteria; artifact log complete.
- **Claims limitation:** exactly the validation plan §7 lists — nothing more, and genre-scoped.
- **Rollback:** n/a (evidence, not behavior). **Invalidated by:** loudness-matching defect discovered post hoc (void, fix, rerun).

### M25 — Diagnosis calibration v2 (graded severities + real-vocal confusion matrices)
- **Problem:** thresholds calibrated only on strong synthetic positives; mild/moderate behavior unknown; real-vocal FP/FN rates unknown; several needed diagnoses (hum, low level, reverb estimate, plosives) missing.
- **Why now:** corpus with known ground truth (M22) makes graded calibration possible; can run **in parallel with M24** after M23. **Why not earlier:** no graded ground truth existed.
- **Risk retired:** wrong diagnosis silently driving DSP (the muddiness incident, systematized). **Unlocks:** M26 adaptive-policy changes; advisory-diagnosis promotion.
- **In scope:** extend calibration harness to mild/moderate/strong per issue + real-corpus runs; per-issue precision/recall/threshold report committed; add **advisory-only** diagnoses: hum (50/60 Hz peaks), recording level (LUFS vs policy), reverb estimate (decay/SRMR-class, speech-tuned caveat), plosive events (LF transients); explicit decision table: which issues may control DSP (currently: the calibrated five within existing bounds) vs advisory-only.
- **Out of scope:** letting any new diagnosis control DSP; changing planner mappings (M26).
- **Evidence gate:** confusion-matrix report; documented control/advisory decision per issue.
- **Invalidated by:** corpus too small for stable estimates → extend corpus first.

### M26 — Evidence-driven DSP tuning + do-no-harm gates
- **Problem:** M24/M25 will produce a concrete failure list (expected candidates: gate breath/word-tail truncation, sibilance-cut dulling, compressor settings, HPF vs low registers); none may be fixed without evidence, all must be fixed with it.
- **Why now:** first milestone allowed to change audio behavior post-evidence. **Why not earlier:** guardrail — no threshold tuned without evidence.
- **In scope:** fix only benchmark/listening-backed failure modes; add permanent CI gates: clean-input do-no-harm (band deltas ≈ 0, no artifacts on clean fixtures), true-peak ≤ −1 dBTP on all regression outputs, per-defect objective non-regression vs frozen M23 baseline; register-aware HPF policy if (and only if) evidence showed fundamental damage; goldens regenerated with version bumps per M17 precedent.
- **Evidence gate:** re-run benchmark + targeted mini-listening on changed families; deltas improve, no new artifacts.
- **Rollback:** each fix a separate commit; goldens pin behavior.

### M27 — Report & product-experience upgrade (validation-aligned)
- **Problem:** reports don't yet answer "what improved / what may have worsened / what can't be fixed / what to rerecord"; web preview isn't loudness-matched.
- **Why now:** language and thresholds finally have evidence behind them; parallelizable with M26.
- **In scope:** report v2 (per-defect before/after deltas with plain-language interpretation, confidence display, unfixable-issue + rerecord guidance, artist vs engineer detail levels, JSON manifest export); webapp result page uses loudness-matched previews; input guidance (dry vocals requested; full-mix advisory warning).
- **Out of scope:** new frontend framework, accounts, cloud (standing prohibition).
- **Evidence gate:** UX acceptance: 3–5 pilot users can answer the ten report questions (audit Track H) unaided.

### M28 — Expanded processors (individually gated; order by M24 evidence)
Candidates, each its own mini-milestone with a validated failure mode + artifact gate + listening check: **de-esser** (leading; replaces static sibilance cut; lisp gate), **hum notch** (deterministic, low risk), **plosive reduction**, **breath-level control**, **optional broadband denoise** (DeepFilterNet, MIT/Apache — never gate escalation). Explicitly deferred: dereverberation (detect-and-disclose only), declipping (referral), saturation/air (enhancement phase), pitch/timing correction (out of scope), source separation (preprocessing option, future ADR).

### M29 — Genre coverage & proprietary mini-corpus
- **Problem:** target genre (underground rap/bedroom) absent from all public data; claims are genre-scoped until owned data exists.
- **Prerequisites:** consent protocol approved (governance §6) — **legal/human gate**; M24 methodology reusable as-is.
- **In scope:** 5–10 consenting artists, ≥ 2 simultaneous mics (budget + condenser), untreated rooms, dry exports, metadata per governance; rerun M23/M24 on this corpus; genre-scoped claims updated.
- **Unlocks:** dry/wet self-generated pair set (research map #15), preference dataset growth, eventual ML gate.

### Future (explicitly gated, not scheduled)
- **Reference matching** — after M28 cleanup is validated; study-only until then.
- **ML anything** — prohibited until: deterministic limits documented per defect (M24/M26/M28 reports), data rights cleared (Tier P or Tier A training data), and an ADR approves it.
- **Distribution packaging** — legal review of pedalboard GPL-3.0 + FFmpeg build first.

## 2. Dependency graph

```
M21 governance ──► M22 corpus+degradations ──► M23 metrics+matched A/B ──► M24 listening (EG-1: alpha verdict)
                                        │                          │
                                        └──► M25 calibration v2 ◄──┘   (M25 ∥ M24, both need M23 exports)
M24 + M25 ──► M26 DSP tuning + do-no-harm gates (EG-2)
M24 ──► M27 report/UX (∥ M26)
M26 ──► M28 processors (each: EG per processor)
M24 methodology + consent protocol (legal gate) ──► M29 proprietary corpus
M28 + M29 ──► future: reference matching, ML (ADR gate)
```
**Critical path:** M21 → M22 → M23 → M24. Everything else hangs off M24's verdict.
**Parallelizable:** M25 with M24; M27 with M26; manifest writing (M21) with corpus download approvals (M22 checkpoints).
**Human/legal gates:** DAMP + Zenodo agreements (M22); listener recruitment (M24); consent protocol + GPL distribution review (M29 / packaging).

## 3. Resolved sequencing questions

| Question | Resolution |
|---|---|
| Must governance precede all evaluation? | Yes for any downloaded data; owned local vocals may be smoke-tested anytime. |
| Metrics before listening tests? | Loudness matching must; other metrics ideally (same milestone, M23). |
| Listening before DSP tuning? | Yes — M26 is gated on M24/M25 evidence (guardrail: no threshold tuned to pass). |
| Calibrate diagnosis before new processors? | Yes — M25 before M28; M28 additionally needs M24 failure evidence. |
| Freeze adaptive processing until benchmarked? | Yes — v2 stays default but unmodified until M26; legacy/generic kept as baselines. |
| UI in parallel with validation? | Only M27's validation-aligned UX; no new frontend. Justified frontend = none currently (webapp exists). |
| Which diagnoses may control DSP now? | rumble, muddiness, harshness, sibilance, noise_floor, dynamics — within existing bounds. All new diagnoses advisory until M25 passes them. |
| Synthetic vs real vs reference vs human validation? | Synthetic: threshold calibration, regression. Reference-based (SingVERSE/degraded pairs): fidelity. Human: all perceptual claims. Engineer judgment: artifact taxonomy, M29 annotations. |
| Datasets now vs later? | Now: VocalSet, Vocadito, VoiceBank-DEMAND, SingVERSE, DAMP, MUSAN/RIRs. Reference-only for now: MUSDB18-HQ, MedleyDB, MoisesDB, Mix Evaluation, SAFE-DB, GTSinger. Never: Tier D. |
| Proprietary collection start? | Logging of listening responses: M24. Artist audio: M29 after consent protocol. |
| Reference matching before/after expanded cleanup? | After (M28+). |
| ML threshold? | Documented deterministic limits + cleared data rights + ADR. |
| Highest immediate audible value? | M26 (evidence-driven fixes) — but it requires M22–M24 first. |
| Highest scientific credibility? | M24. |
| Highest usability? | M27. |
