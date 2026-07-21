# Decision Log

Decisions are append-only. Reversals create a new entry and name the superseded decision.

| ID | Date | Status | Decision | Rationale and consequences |
|---|---|---|---|---|
| D-001 | 2026-07-21 | Accepted | Treat executable behavior and reproducible tests as the highest current-state authority. | Root planning text contains drift; code and tests establish the v2 default and actual baseline. |
| D-002 | 2026-07-21 | Accepted | Quarantine all professional-quality, preference, and generalized do-no-harm claims. | No independent listening corpus exists and the current analyzer admits false passes. |
| D-003 | 2026-07-21 | Accepted | Replace row-count listening gates with preregistered independent-listener and independent-item designs. | Repeated rows from one listener currently satisfy `n >= 8`; clustered observations require clustered analysis. |
| D-004 | 2026-07-21 | Accepted | Treat ties/no-difference as first-class outcomes. | Discarding ties biases defect results and makes unanimous no-difference look like perfect agreement plus clean safety. |
| D-005 | 2026-07-21 | Accepted | Separate quality objectives into defect reduction, artistic intent preservation, collateral harm, safety, and confidence. | A single metric movement cannot establish perceptual improvement. |
| D-006 | 2026-07-21 | Accepted | Require experiment, source, consent, rights, listener, item, and software identities in evidence records. | Current dataset-level manifests and processing records cannot prove independence, deletion scope, or claim eligibility. |
| D-007 | 2026-07-21 | Accepted | Keep model-based methods behind an offline challenger boundary until data, rights, evaluation, and rollback gates pass. | Recent differentiable mixing work is promising but domain-limited and does not supply production rights or target-genre validity. |
| D-008 | 2026-07-21 | Accepted | Preserve deterministic DSP as the production champion during the evidence rebuild. | It is testable, explainable, reversible, and safer than prematurely shipping an opaque model. |
| D-009 | 2026-07-21 | Accepted | Introduce a DSP adapter boundary before desktop packaging. | The current GPL Pedalboard dependency may determine the distribution license; architecture must permit a reviewed replacement. |
| D-010 | 2026-07-21 | Accepted | Do not distribute a desktop binary until a documented licensing branch is chosen. | Pedalboard is GPL-3.0; the audited FFmpeg build enables GPL; PySide has LGPL/GPL/commercial choices. |
| D-011 | 2026-07-21 | Accepted | Define the initial desktop target as local-first, single-vocal, non-destructive project processing. | It is the smallest coherent user workflow and avoids premature DAW/plugin scope. |
| D-012 | 2026-07-21 | Accepted | Make research watching deterministic, reviewable, and non-self-authorizing. | External change discovery may propose roadmap changes but cannot adopt models, spend money, or publish claims. |
| D-013 | 2026-07-21 | Accepted | Mark synthetic-corpus scores as engineering diagnostics, not product-quality proof. | Current corpus cells are small and some SI-SDR outcomes are mixed or negative. |
| D-014 | 2026-07-21 | Accepted | Require explicit rights dimensions rather than a single license label. | Training, internal evaluation, redistribution, retention, publication, and claim support are distinct permissions. |
| D-015 | 2026-07-21 | Proposed | Choose one desktop distribution branch: GPL-compatible open source, permissive/custom DSP, or hosted-only. | Owner and legal review are required before packaging architecture freezes. |
| D-016 | 2026-07-21 | Proposed | Use a qualified professional-engineer pilot before a larger listener study. | A small pilot can expose protocol, compensation, task-duration, and effect-size assumptions before costly recruitment. |
| D-017 | 2026-07-21 | Proposed | Set external evaluation compensation at or above the platform-recommended rate, with a professional premium for engineers. | Exact vendor, budget, and contract require owner approval. |
| D-018 | 2026-07-21 | Accepted | Treat `MILESTONE_REGISTRY.yaml` as the complete machine execution manifest and milestone Markdown as validated contracts/views. | A single authority now owns status, dependencies, lanes, profiles, resources, write sets, evidence keys, claim impact, and quarantine; validators must reject drift. |
| D-019 | 2026-07-21 | Accepted | Complete DT-45: adopt the typed evidence-semantics model (`src/evaluation/semantics/`) and the claim quarantine registry as the evaluation vocabulary; implements D-002 and D-005 mechanically. | Nine canonical statuses serialize; legacy `EvaluationResult` maps forward with no silent pass; the seeded claim inventory renders only the audited determinism/regression engineering claim as approved. 412 tests pass; 6/6 audio goldens unchanged. Evidence: `07_DATA_AND_PROVENANCE/dt45_evidence/`. Un-quarantining any claim remains a human-only public_claims gate. |
| D-020 | 2026-07-21 | Accepted | Complete DT-46: adopt the identity/provenance graph (`src/provenance/`) with typed opaque IDs, canonical node hashes, append-only corrections, and a graph validator (broken-edge, required-lineage, cycle, duplicate-fingerprint); implements D-006. | Legacy v1 assets import as `legacy` nodes with `unknown` rights and lineage, never inferred. 427 tests pass; 6/6 audio goldens unchanged. Evidence: `07_DATA_AND_PROVENANCE/dt46_evidence/`. Rights enforcement and any real deletion remain human-gated (DT-49). |

## Decision acceptance rule

An accepted decision must identify its authority, affected specifications/milestones, reversibility, and owner. Proposed decisions remain roadmap blockers where named.
