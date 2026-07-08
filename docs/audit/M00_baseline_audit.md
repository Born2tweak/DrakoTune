# M00 — Repository Baseline and Safety Inventory

> Audit performed against the DrakoTune source-of-truth documents (Bible,
> Technical Design Spec, Implementation Roadmap, Agent Context, Autonomous
> Engineering Constitution/OS, Product Experience Bible, Research Gaps).
> Docs-only milestone: **no code behavior was changed.**

- **Repo:** `Born2tweak/DrakoTune` @ `649cc7b` ("feat: DrakoTune Alpha 2.1 — adaptive DSP pipeline with artifact scanning")
- **History:** single squashed commit on `main`; no branches, no tags.
- **Toolchain verified this session:** Python 3.14.0, pip 25.3, ffmpeg 8.1.1. All runtime deps (`numpy`, `soundfile`, `librosa`, `pedalboard`, `scipy`, `pytest`) import cleanly.
- **Test evidence this session:** `python -m pytest -q` → **41 passed, 1 warning, 30.35s** (exit 0). Full CLI (`scripts/run_alpha.py`) ran end-to-end on a synthetic vocal and produced before/after WAVs.

---

## 1. Current repository state

```
src/dsp/preprocess.py   91 loc   FFmpeg normalize → 44.1kHz / 16-bit / mono (with Windows fallback paths)
src/dsp/diagnose.py    698 loc   7-category diagnostic engine + 1s-window artifact scanner
src/dsp/pipeline.py    363 loc   generic chain + adaptive chain + "alpha22" localized refinement
src/dsp/export.py       49 loc   copy normalized + processed WAV to output dir as before/after pair
scripts/run_alpha.py   147 loc   CLI: preprocess → diagnose → artifact scan → DSP → export
tests/test_diagnose.py 366 loc   synthetic-signal diagnostic tests
tests/test_pipeline.py 221 loc   preprocess/pipeline/export tests
```

Supporting docs exist under `docs/` (product brief, PRD, architecture, ai-rules,
implementation plan, alpha-diagnosis plan, context protocols, research notes) plus
`.claude/agents/*` orchestration definitions.

## 2. Existing audio pipeline behavior

`run_alpha.py` executes: **FFmpeg preprocess → diagnose (7 categories) → artifact
scan (pre) → adaptive DSP → artifact scan (post) → export before/after**. A
`--generic` flag bypasses diagnosis and uses the fixed Alpha-1 chain. Original
input is never overwritten (output is a separate before/after pair). Processing
of a 3s clip completes in ~4.4s.

## 3. Existing DSP behavior

- **Diagnostics (`diagnose.py`):** harshness, sibilance, muddiness, clipping, noise floor, dynamic inconsistency, dullness. Each returns a `DiagnosisResult(category, severity, confidence, detected_frequency_hz, measured_value, threshold, recommendation)`. A `_cross_reference` step emits conflict warnings. A 0–100 quality score is derived from severity penalties. `scan_artifacts` flags per-second clipping bursts / HF spikes.
- **Generic chain (`build_cleanup_chain`):** HPF → 2× PeakFilter → Compressor → NoiseGate → Gain (fixed `CleanupParams`).
- **Adaptive chain (`build_adaptive_chain`):** reads the `VocalProfile` and conditionally adds gain-staging, HPF, mud/harsh/sibilance cuts, gate, compression, air boost, and a final limiter, gated by **severity**.
- **`apply_alpha22_refinement`:** STFT-based localized plosive/de-ess/peak control + output-trim safety.

## 4. Existing tests and verification commands

- Install: `pip install -e ".[dev]"` (or ensure `numpy soundfile librosa pedalboard pytest` + FFmpeg on PATH).
- Test: `python -m pytest -q` — **41 tests, all passing this session.**
- Run: `python scripts/run_alpha.py <input.wav> --output-dir output/ [--generic]`.

## 5. Gaps versus the desired DrakoTune architecture

The Technical Design Spec mandates a **strict separation**: Diagnostics *measure* →
Decision Engine *interprets & plans* → DSP Engine *executes a plan it did not
author* → Evaluation *compares* → Report *explains*. The current code is
functional but **collapses several of these layers**.

| Spec layer | Current status | Gap |
|---|---|---|
| Canonical data types (Observation, Interpretation, Objective, Action, ProcessingPlan, EvaluationResult, Report) with version fields | **Missing.** Only `DiagnosisResult`/`VocalProfile`/`ArtifactWindow` exist. No `analyzerVersion`/`policyVersion`. | **M01** — foundational. |
| Fixture library (`fixtures/audio`, `fixtures/expected`) | **Missing.** Tests generate signals inline; no golden fixtures. | **M02** |
| Preflight validation (format, duration, silence, decode, channels) | **Partial.** Only `FileNotFoundError`; no structured blocker. | **M03** |
| Technical-safety diagnostics stored with analyzer settings/version | **Partial.** Clipping exists; no true-peak/headroom/DC; thresholds not versioned. | **M04** |
| Loudness/dynamics (RMS, LUFS, crest factor) | **Partial.** Dynamic-inconsistency CV only; no LUFS/crest/headroom. | **M05** |
| Spectral/noise diagnostics separating observation from interpretation | **Present but conflated** — `recommendation` (an action) is embedded in each `DiagnosisResult`. | **M06** refactor |
| Decision Engine (safety rules, objective selection, conflict resolution, decision records) | **Missing as a layer.** Decision logic is hard-coded inside `build_adaptive_chain` in the DSP module. | **M07/M08** — highest-leverage refactor. |
| DSP as plan-executor with processor metadata (objectives, safe ranges, blocked_by, artifact_risk) | **Missing.** Chain is imperatively assembled, not driven by a declared plan. | **M09** |
| Before/after Evaluation (loudness-matched deltas, artifact checks, objective success/fail) | **Missing.** Only pre/post artifact counts printed. | **M10** |
| Report Engine (findings, confidence, applied/skipped actions, limitations, export metadata) | **Missing.** Only stdout printing. | **M11** |
| Web app / storage / CI audio regression | **Missing** — correctly deferred until the core is stable. | **M12–M15** |
| **Confidence controls automation** (Bible/Agent Context law) | **Not honored.** Automation is gated by **severity**, and `confidence` is recorded but unused in decisioning. | Address in M07/M08. |

**Architectural headline:** the repo built the *adaptive DSP output* (roughly
M06+M09 capability) **before** the structured decision records that are supposed
to produce it (M01/M07/M08). It is ahead on audible capability and behind on
inspectable architecture — the exact "stacked speculation" the Constitution warns
against. The corrective path is to introduce the canonical records and lift the
decision logic out of `pipeline.py` **without regressing the working audio**.

## 6. Risks, missing files, unclear assumptions, technical debt

- **`JULES_REPORT.md` is a foreign template** — it references `robinbakshi007/ollama-direct-custom-agent`, VS Code Marketplace publishing, and TypeScript. None apply to DrakoTune. **Recommend deletion** (M00/M01 housekeeping).
- **`scipy` is used by `tests/test_diagnose.py` but not declared** in `pyproject.toml` (works only because `librosa` pulls it transitively). Declare it under `dev`.
- **Roadmap conflict in-repo:** `docs/05-implementation-plan.md` describes a *different* build order (Phase 0–7: frontend/backend/storage/waveform/conversational-AI early) that contradicts the source-of-truth `Implementation Roadmap` (deterministic core M00→M11 first). This must be reconciled so agents don't follow the wrong sequence.
- **Threshold fragility / calibration debt:** on a pure synthetic tone the CLI reported `noise_floor: SEVERE (-8 dBFS)` — a likely false positive from continuous-tone input. Thresholds are hand-set and uncalibrated (a known Research-Gaps item). No fixtures pin this behavior yet.
- **Diagnostics emit recommendations (decision-layer output)**, violating measurement/interpretation/action separation.
- **No versioning** of analyzer settings, thresholds, or policies anywhere (Bible requires it).
- **No CI**, no lint/type config, no fixture policy doc.
- **Windows-specific FFmpeg fallback paths** are hard-coded in `preprocess.py`; fine for now, worth noting for portability.

## 7. Recommended first implementation milestone

**M01 — Canonical Audio Types and Processing Artifacts** (additive, non-breaking).

Rationale: it is the keystone that unlocks the decision-engine refactor (M07/M08),
evaluation (M10), and reports (M11) without touching audio behavior. Introduce
versioned `Observation`, `Interpretation`, `ProcessingObjective`, `ProcessingAction`,
`ProcessingPlan`, `EvaluationResult`, and `Report` types in a `shared-types`
module; make the existing pipeline able to *emit* a minimal versioned processing
record while continuing to produce identical audio. Bundle the low-risk M00
housekeeping (delete `JULES_REPORT.md`, declare `scipy`, add a doc note
reconciling the roadmap conflict).

Guardrail for every subsequent milestone: the 41 passing tests must stay green,
audio output must not regress, and each change ships with tests + a completion
report per the Agent Context template.
