# Next Five Ready Milestones

**Authority:** validated derived execution view; YAML registry state wins on conflict.

“Next five” means the next dependency-respecting queue. Only DT-45 is currently ready; after it completes, DT-46, DT-47, DT-50, and DT-53 may run as separate autonomous lanes when their prerequisites pass.

| Order | Milestone | Current state | Start trigger | First deliverable | Stop condition |
|---:|---|---|---|---|---|
| 1 | DT-45 Evidence Semantics and Claim Quarantine | Ready | Human accepts this planning package and assigns evaluation owner. | Typed result/claim schema and legacy mapping fixtures. | Stop if vocabulary/authority is disputed; do not change DSP. |
| 2 | DT-46 Identity and Provenance Schema v2 | Blocked | DT-45 complete; data/privacy reviewers assigned. | Identity graph/schema ADR and legacy fixture inventory. | Stop on direct-identity/privacy ambiguity. |
| 3 | DT-47 Metric Applicability Registry | Blocked | DT-45 complete; audio/evaluation reviewers assigned. | Complete inventory of current metrics and draft cards. | Quarantine any measure whose domain/reference cannot be established. |
| 4 | DT-50 Reproducible Environment and SBOM | Blocked | DT-45 complete; supported baseline/build owner assigned. | Locked environment proposal and exact FFmpeg/dependency inventory. | Preserve old baseline if clean parity fails. |
| 5 | DT-53 Product Promise Discovery and Scope Decision | Blocked | DT-45 complete; research consent/owner approval. | Bounded discovery protocol and promise alternatives. | Retain narrow current spec if participant evidence is inconclusive. |

DT-48 follows DT-46+47; DT-49 follows DT-46; DT-51 follows DT-49+50. The scheduler may continue unblocked lanes without repeated owner confirmation under [the autonomy policy](AUTONOMY_AND_PARALLEL_EXECUTION.md).
