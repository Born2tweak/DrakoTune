# DRAKOTUNE CONTEXT EXPORT
> Living project brain. Read before work. Update before ending.
> Updated: 2026-05-20 | By: Antigravity (QA Audit)

## 1. Snapshot

| Field | Value |
|---|---|
| Product | AI-assisted vocal engineering for underground artists |
| Phase | Milestone Alpha — Proof-of-Concept Audio Pipeline |
| Status | ✅ COMPLETE — PENDING REAL VOCAL VALIDATION (9/9 tests pass, 3.14s) |

## 2. Vision

Translates artistic language ("smoother", "less harsh") into professional DSP using Pedalboard, FFmpeg, Librosa, Essentia, TorchAudio, Demucs. LLM maps intent to structured DSP params — never processes audio directly. Success = "sounds alive/expensive/listenable", not "technically clean."

## 3. Docs

| Doc | Path |
|---|---|
| Product Brief | `docs/01-product-brief.md` |
| PRD | `docs/02-prd.md` |
| Architecture | `docs/03-architecture.md` |
| AI Rules (21) | `docs/04-ai-rules.md` |
| Impl Plan | `docs/05-implementation-plan.md` |
| This file | `docs/DRAKOTUNE_CONTEXT_EXPORT.md` |
| Update Protocol | `docs/CONTEXT_UPDATE_PROTOCOL.md` |
| DSP Research | `docs/research/vocal_chain_research.md` |

## 4. Stack

**Frontend:** Next.js, TS, TailwindCSS, Zustand, Wavesurfer.js
**Backend:** Python FastAPI, Redis queue, FFmpeg
**DSP:** Spotify Pedalboard (primary), DSP plugins, custom chains
**Analysis:** Librosa, Essentia, TorchAudio, Demucs
**LLM:** Claude/OpenAI (taste layer only — NOT audio engine)
**Infra:** Vercel, Railway/Render/Fly.io, Supabase/Postgres, Cloudflare R2
**DB:** Users, Projects, AudioFiles, ProcessingStages, Conversations

## 5. Agents

| Agent | Role |
|---|---|
| Orchestrator | DAG planning, sprint assignment, context owner |
| MAteam | Researcher→Coder→Reviewer→Verifier pipeline |
| KDream | Background daemon, memory, TODO watcher |
| AutoBuild | Build/test pipeline automation |

## 6. Current Milestone — Alpha PoC

**Question:** Can DrakoTune make bad vocals noticeably smoother and more listenable?

**Status:** ✅ COMPLETE — Pending real vocal test

**Scope:** Accept WAV → FFmpeg preprocess (44100Hz/16-bit/mono) → Pedalboard cleanup chain → before/after previews → export WAV

**DSP Chain:** Highpass ~80Hz, 2× PeakFilter EQ cut (3.5kHz, 6.5kHz), Compressor, NoiseGate, Gain normalization

**Deliverables:** All 5 delivered and verified:
- [x] `src/dsp/pipeline.py` — Pedalboard cleanup chain (6 real plugins)
- [x] `src/dsp/preprocess.py` — FFmpeg subprocess normalization
- [x] `src/dsp/export.py` — before/after WAV copy utility
- [x] `tests/test_pipeline.py` — 9 tests, all passing
- [x] `scripts/run_alpha.py` — full CLI entry point

**Acceptance (all met):**
- [x] Pipeline accepts WAV, produces processed WAV
- [x] FFmpeg normalizes to 44100Hz/16-bit/mono
- [x] Pedalboard applies real chain: HighpassFilter, 2× PeakFilter, Compressor, NoiseGate, Gain
- [x] Before/after files generated in output/
- [x] Spectral test confirms reduced energy in 2–8kHz harsh band
- [x] 3s audio processes in 3.14s total test suite — well under 30s limit
- [x] 9/9 tests pass (Python 3.14, pytest 9.0.3)
- [x] No fake DSP — only real Pedalboard plugin classes

**Remaining:** Real vocal file test (`python scripts/run_alpha.py <vocal.wav>`) to confirm audible improvement.

**Blockers:** None. Waiting for real vocal input file.

## 7. Repo State

**Folders:**
| Folder | Purpose |
|---|---|
| `docs/` | All source-of-truth documents |
| `src/dsp/` | Alpha pipeline — preprocess.py, pipeline.py, export.py |
| `tests/` | test_pipeline.py (9 tests, all passing) |
| `scripts/` | run_alpha.py CLI entry point |
| `.agent/rules/` | Agent system rules |
| `.autoclaw/` | Orchestrator runtime state |
| `output/` | Before/after WAV outputs (empty until real vocal run) |

**Implemented:**
- FFmpeg preprocessing (subprocess, Windows fallback paths included)
- Pedalboard cleanup chain: HighpassFilter + 2× PeakFilter + Compressor + NoiseGate + Gain
- `CleanupParams` dataclass with bounded, documented parameter ranges
- WAV export (before/after copy utility)
- Full CLI run script with timing and human-readable output
- 9 automated tests covering format, harshness reduction, timing, custom params, error handling

**Not yet built (all future milestones):**
- Presence, Blend, Emotion, Final Polish stages
- Librosa / Essentia / TorchAudio / Demucs integration
- FastAPI backend, Redis queue
- Next.js frontend, Wavesurfer.js
- Conversational AI layer
- Database, storage, deployment

**Known Issues:**
- `pyproject.toml` lists `pytest` as a runtime dependency — should move to `[project.optional-dependencies]` dev group in Beta
- `ffmpeg-python` package is NOT listed in dependencies (preprocess.py uses `subprocess` directly — this is correct, but ffmpeg binary itself must be installed separately; this is undocumented)
- FFmpeg binary requirement has no README or setup docs yet
- `run_alpha.py` uses `sys.path.insert` hack instead of proper package install — acceptable for Alpha CLI, should be replaced with `pip install -e .` workflow in Beta
- No `src/__init__.py` or `src/dsp/__init__.py` package markers verified as sufficient (they exist per dir listing)
- `output/` dir is empty — no real vocal test has been run yet

## 8. Recent Decisions

- 2026-05-20: QA audit confirmed Alpha pipeline uses only real Pedalboard plugin classes (HighpassFilter, PeakFilter, Compressor, NoiseGate, Gain) — no fake DSP. Alpha ACCEPTED pending real vocal test.
- 2026-05-20: `pytest` will be moved to `[project.optional-dependencies]` dev group in Beta — not a blocker for Alpha.
- 2026-05-20: `ffmpeg-python` package not needed — preprocess.py uses subprocess directly. FFmpeg binary is an external system dependency, not a Python package. Needs setup docs in Beta.
- 2026-05-20: Milestone Alpha defined — PoC audio pipeline before any frontend/infra
- 2026-05-20: Living context system established (this file + protocol)
- 2026-05-20: 5-layer architecture, mandatory use of Pedalboard/FFmpeg/Librosa/Essentia/TorchAudio/Demucs

## 9. Recent Changes

- 2026-05-20 | Claude Code (DSP Research) | Created `docs/research/vocal_chain_research.md` — comprehensive DSP research covering: professional chain ordering, EQ frequency map, harshness zones, compression/saturation strategies, noise reduction, cheap vs expensive indicators, AI enhancer pitfalls, full Pedalboard API reference, and recommended Alpha chain with parameter ranges. Informs all future DSP work.
- 2026-05-20 | Antigravity (QA) | Audited Milestone Alpha. 9/9 tests confirmed passing (3.14s). No fake DSP found. Scope respected. Context export updated. Files: `docs/DRAKOTUNE_CONTEXT_EXPORT.md`
- 2026-05-20 | Claude Code | Built Milestone Alpha pipeline: `src/dsp/preprocess.py`, `src/dsp/pipeline.py`, `src/dsp/export.py`, `tests/test_pipeline.py`, `scripts/run_alpha.py`, `pyproject.toml`, `CURRENT_MILESTONE.md`
- 2026-05-20 | Claude Code | Wrote all 5 core docs as md files in `docs/`
- 2026-05-20 | Antigravity | Created context system, agent rules, updated AI rules with Rule 21

## 10. Next Actions

1. **Run real vocal test** — `python scripts/run_alpha.py path/to/raw_vocal.wav --output-dir output/` — listen to before vs after, confirm audible improvement. This is the only remaining Alpha gate.
2. **Write `docs/SETUP.md`** — Document FFmpeg binary install requirement (Windows/Mac/Linux), Python 3.10+, and `pip install -e .` workflow so the next agent doesn't hit environment issues.
3. **Move `pytest` to dev deps** — Update `pyproject.toml` to use `[project.optional-dependencies]` with a `dev` group. Minor hygiene fix, do in Beta setup.
4. **Plan Milestone Beta** — After vocal test passes: define Beta scope (Presence stage + Librosa harshness analysis + FastAPI skeleton). Write `CURRENT_MILESTONE.md` for Beta before touching any code.
5. **Do NOT start Beta until real vocal test is confirmed.** Alpha is gated on human ears, not just tests.
