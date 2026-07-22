# Remediation Control-Plane Reconciliation Record (AR-00 / AR-01 / AR-02)

**Reconciled:** 2026-07-21 · **Verified commit:** `75cc057` · **Executor:** claude-code (autonomous)

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
