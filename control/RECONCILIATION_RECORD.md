# Remediation Control-Plane Reconciliation Record (AR-00 / AR-01 / AR-02)

**Reconciled:** 2026-07-21 · **Verified commit:** `75cc057` · **Executor:** claude-code (autonomous)

> **2026-07-23 addendum (§6–§8):** a second reconciliation run verified the repo
> against an external analysis that suspected cross-project contamination and
> roadmap drift. Findings below. Verified baseline this run: HEAD `61fc94f`,
> **536 tests collected/pass**, `main` CI-green (run `29887064268`).

This record replaces the packaged greenfield templates with verified repository
facts, per the program rule *"repository evidence overrides the initial templates."*

## 1. Verified repository facts (evidence, not transcript)

| Fact | Value | How verified |
|---|---|---|
| Remote | `Born2tweak/DrakoTune` (https) | `git remote -v` |
| Default branch | `main` | `git symbolic-ref refs/remotes/origin/HEAD` |
| HEAD | `75cc057` "docs: consolidated human decision packet…" | `git rev-parse HEAD` |
| Working tree | clean; `main` == `origin/main` | `git status`, `git rev-list --count` |
| CI (latest on main) | run `29887064268` **success** (2m3s) | `gh run list` |
| Open PRs | none | `gh pr list` |
| Test baseline | **478 passed, 4 warnings** | `python -m pytest -q` (this session) |
| Env | Python 3.14.0 Windows; `pip check` clean | `python --version`, `pip check` |

## 2. Milestone reclassification (authority: `AURELIAN/05_ROADMAP/MILESTONE_REGISTRY.yaml`)

- **Complete + CI-green (merged to main):** DT-45, DT-46, DT-47, DT-48, DT-50, DT-52.
- **Ready but human-gated for their *decision*:** DT-49 (rights), DT-53 (product scope).
- **Blocked:** DT-51 (needs DT-49 + human distribution decision) and DT-54…DT-92.

## 3. Correction of a false stopping state (the key reconciliation finding)

The prior autonomous run reached the **first human-gate boundary** and wrote
`AURELIAN/00_CONTROL/HUMAN_DECISION_PACKET.md`. That packet itself lists
**autonomous preparation that was never done** and ends by *asking permission*
to do it ("If you want, I will proceed with the autonomous prep…").

Under both `control/execution-policy.yaml` (`finish_safe_preparation_first: true`,
phase boundaries are not approval checkpoints) and the program contract §6, that
safe preparation is **required work, not an approval checkpoint**. The prior run
therefore stopped early. The reconciled frontier contains genuine safe work:

| Ready item | Autonomous (do now, no gate) | Human-only (gate) |
|---|---|---|
| **DT-49** | rights-grant schema; `authorize(asset,purpose,at_time)`; consent-store *interface*; withdrawal-graph traversal + deletion **simulation** on synthetic fixtures; claim-suspension wiring; fail-closed on unknown | real consent/contract language; retention/privacy obligations; real deletion authority; legal rights interpretation |
| **DT-53** | discovery protocol, job map, promise alternatives, falsifier set as a **synthetic framework** | the final product-promise/scope decision; any participant contact |
| **DT-51** | component-level license obligation inventory + cost/risk comparison from the SBOM, with a **recommendation** | choosing the distribution branch (owner + qualified counsel) |

## 4. Deficiency reconciliation (vs `control/deficiency-register.yaml`)

- **DEF-002** (reproducibility / workstation leakage): **closed** by DT-50 — two-clean-env CI parity proven (run 29864106617), SBOM + FFmpeg/pedalboard GPL captured.
- **DEF-001** (DT-45..48 production integration): **refined** — evidence semantics, provenance, metric registry, and multiaxis verdict are merged and tested; DT-49 rights enforcement is the remaining autonomous integration piece.
- **DEF-003** (real-audio perceptual validation): **open, human-gated** — requires rights-cleared corpus + preregistered listening (DT-55/DT-62/DT-56/DT-57 → DT-66/DT-67); acquisition & recruitment are human gates.
- **DEF-004** (metric calibration): **partially addressed** by DT-47 (36 metric cards, 33 honestly-unset thresholds); full calibration is DT-64 (needs held-out real data → human-gated acquisition).
- **DEF-005** (unattended autonomy): **open** — controller milestones (DT-77+/AR-07..09,17) are downstream and blocked.
- **DEF-006 / DEF-007** (usability / release ops): **open** — downstream of the human gates above.

## 5. Exit gate (AR-01)

A fresh agent reading this file + `canonical-state.json` + the milestone registry
can identify the exact frontier and next automatic action:
**do the DT-49/DT-53/DT-51 autonomous preparation, then present one consolidated
human-decision packet.** No routine approval is required to begin.

---

## 6. Cross-project contamination ruling (2026-07-23)

An external analysis worried that code from a separate music **publishing /
distribution** platform had been merged into DrakoTune, and that the roadmap had
drifted away from audio into governance busywork. **Both concerns are disproven
by direct repository evidence.**

### 6.1 No music-distribution / publishing code exists here

Whole-repo term counts (`.py`/`.md`/`.yaml`/`.json`, `.git` excluded):

| Term | Hits | Note |
|---|---|---|
| `isrc` | 0 | — |
| `royalt*` | 0 | — |
| `a&r` / `record label` / `distributor` | 0 | — |
| `music distribution` / `streaming service` | 0 | — |
| `aggregator` | 1 | "Papers with Code, Kaggle" **dataset** aggregators for research discovery (`docs/research/PUBLIC_VOCAL_AUDIO_DATASET_RESEARCH.md`) |
| `spotify` | 1 (in `src/`) | `src/dsp/pipeline.py` — **Spotify *Pedalboard***, the GPL-3.0 DSP library |
| `publishing` | 2 | both **out-of-scope** declarations (`PRODUCT_SPEC.md`, `DT_69_76.md`) |

Conclusion: no ISRC/royalty/streaming/catalog/A&R/aggregator/publishing code
leaked in. Every superficial match resolves to the *Pedalboard* DSP library, LUFS
delivery targets, dataset-research tooling, or an explicit out-of-scope note.

### 6.2 The governance modules are OFF the runtime audio path

`grep` for imports of `rights` / `product_discovery` / `provenance` /
`data_governance` / `tooling` / `license_policy` across the runtime path
(`src/webapp/`, `src/orchestration.py`, `src/dsp/`, `src/dsp_engine/`,
`src/decision/`, `src/diagnostics/`, `src/evaluation/`) returns **0 matches**.
Those modules are imported only by `tests/` and `scripts/`. They cannot gate,
block, or alter actual audio processing. The runtime chain is:
`webapp/jobs.py → preprocess → preflight → diagnostics → orchestration(decision)
→ dsp_engine(render) → evaluation → report`.

### 6.3 The roadmap is already audio-first; the frontier is a real human gate

DT-54–DT-92 are audio work (listening protocols, rights-clean corpus, champion
DSP calibration/improvement DT-77–DT-80, packaging last). No audible improvement
had shipped **not** because the agent avoided sound, but because the next steps
are gated by one consolidated human decision (product scope, rights/consent
posture, distribution license) — see `CONSOLIDATED_HUMAN_DECISION.md`. The agent
completed every *autonomous* half and correctly stopped at that boundary.

## 7. Terminology glossary (the words that misled the external analysis)

These repo terms have **software/product** meanings, never music-industry ones:

| Term in this repo | Means | Does NOT mean |
|---|---|---|
| **distribution** | shipping the software application binary; GPL-copyleft packaging branch (DT-51/71/88) | distributing music to streaming services |
| **rights** | consent + retention over *evaluation audio assets* used in datasets (DT-49/55/62) | music publishing / performance rights |
| **discovery** | product/user research (customer-development interviews) (DT-53) | music or content discovery |
| **license** | OSS dependency license (GPL/LGPL/permissive) of code deps (DT-50/51) | music licensing |
| **catalog** | dataset catalog / metric registry card | music catalog |
| **aggregator** | dataset aggregator (Papers with Code, Kaggle) | music aggregator/distributor |

## 8. What the 2026-07-23 run changed

Encoded the three human-gate decisions (D-A product promise as *target promise* +
*currently-supportable claim*; D-B authorized-non-private evaluation posture; D-C
hosted-only distribution), executed the previously-dormant scorecard/evidence
audit (before + after), ran one bounded objective-only DSP experiment, and added
lightweight anti-drift checks. Details in `scorecard.yaml`, `evidence-index.json`,
`deficiency-register.yaml`, `AURELIAN/00_CONTROL/DECISION_LOG.md`, and the
experiment artifacts under `reports/evaluations/`. Also removed a stale tracked
cross-agent injection file (`.claude/rules/cross-agent-protocol.md`) and the
gitignored `.autoclaw/` leftover from an unrelated 2026-05-20 experiment.
