# Milestone Registry

**Authority:** validated derived view; not state authority.

This is the human-readable view. [`MILESTONE_REGISTRY.yaml`](MILESTONE_REGISTRY.yaml) is the canonical status, dependency, lane, execution-profile, write-set, resource, evidence-key, claim-impact, and quarantine authority. Detail records retain required status/gate fields as execution snapshots; a validator must reject drift from YAML. No milestone is in progress because this planning run stops before execution.

## Evidence-contract links

Each linked detail entry contains Field 6 evidence/risk/decision references and Field 23 completion evidence.

| Milestones | Detail and evidence contract |
|---|---|
| DT-45–DT-52 | [H0 details](MILESTONES/DT_45_52.md) |
| DT-53–DT-60 | [H1 details](MILESTONES/DT_53_60.md) |
| DT-61–DT-68 | [H2 details](MILESTONES/DT_61_68.md) |
| DT-69–DT-76 | [H3 details](MILESTONES/DT_69_76.md) |
| DT-77–DT-84 | [H4 details](MILESTONES/DT_77_84.md) |
| DT-85–DT-92 | [H5 details](MILESTONES/DT_85_92.md) |

| ID | Title | Horizon | Status | Depends on | Primary gate |
|---|---|---|---|---|---|
| DT-45 | Evidence Semantics and Claim Quarantine | H0 | ready | M44/audit | Evidence owner acceptance |
| DT-46 | Identity and Provenance Schema v2 | H0 | blocked | DT-45 | Data/privacy review |
| DT-47 | Metric Applicability Registry | H0 | blocked | DT-45 | Audio/evaluation review |
| DT-48 | Multiaxis Verdict Engine | H0 | blocked | DT-46, DT-47 | Adversarial semantic suite |
| DT-49 | Rights, Consent, and Withdrawal Graph | H0 | blocked | DT-46 | Owner/legal/privacy review |
| DT-50 | Reproducible Environment and SBOM | H0 | blocked | DT-45 | Build/license review |
| DT-51 | Desktop Distribution Branch Decision | H0 | blocked | DT-49, DT-50 | Owner + counsel decision |
| DT-52 | Application and DSP Seam Characterization | H0 | blocked | DT-48, DT-50 | Golden parity review |
| DT-53 | Product Promise Discovery and Scope Decision | H1 | blocked | DT-45 | Product owner decision |
| DT-54 | Target-Genre and Recording Strata Taxonomy | H1 | blocked | DT-53 | Product/audio review |
| DT-55 | Rights-Clean Acquisition and Consent Plan | H1 | blocked | DT-49, DT-54 | Owner/legal/spending review |
| DT-56 | Listening Protocol and Immutable Response Schema | H1 | blocked | DT-46, DT-47, DT-54 | Research/privacy review |
| DT-57 | Statistical Preregistration and Adversarial Validation | H1 | blocked | DT-48, DT-56 | Independent statistical review |
| DT-58 | Expert Pilot Budget, Contracts, and Recruitment Approval | H1 | blocked | DT-55, DT-57 | Owner spending/legal approval |
| DT-59 | Professional Engineer Pilot | H1 | blocked | DT-58 | Consent and analysis lock |
| DT-60 | Confirmatory Design, Power, and Threshold Lock | H1 | blocked | DT-59 | Independent preregistration approval |
| DT-61 | Listening Platform Production Hardening | H2 | blocked | DT-56, DT-60 | Security/accessibility dry run |
| DT-62 | Rights-Clean Seed Corpus Acquisition | H2 | blocked | DT-55 | Per-asset authorization |
| DT-63 | Grouped Splits and Corpus Validation | H2 | blocked | DT-46, DT-62 | Leakage/rights validator |
| DT-64 | Champion Calibration on Held-Out Real Data | H2 | blocked | DT-48, DT-52, DT-63 | Frozen calibration protocol |
| DT-65 | Independent Professional Treatments and References | H2 | blocked | DT-58, DT-62 | Contract/rights/quality review |
| DT-66 | Clean Preserve / Do-No-Harm Confirmatory Study | H2 | blocked | DT-60, DT-61, DT-63, DT-65 | Locked analysis and independent review |
| DT-67 | Repair-Efficacy Confirmatory Study | H2 | blocked | DT-60, DT-61, DT-64, DT-65 | Locked analysis and independent review |
| DT-68 | Evidence Synthesis and Bounded Claim Decision | H2 | blocked | DT-66, DT-67 | Scientific/product/legal approval |
| DT-69 | Shared Project and Application Service | H3 | blocked | DT-49, DT-52, DT-53 | Architecture/recovery review |
| DT-70 | Target-Hardware Performance and Duration Budgets | H3 | blocked | DT-52, DT-53 | Owner budget acceptance |
| DT-71 | Desktop Framework and Build Spike | H3 | blocked | DT-51, DT-69, DT-70 | Licensing/build decision |
| DT-72 | Desktop Import, Preflight, and Analyze Slice | H3 | blocked | DT-69, DT-71 | Security/accessibility E2E |
| DT-73 | Desktop Plan, Render, and Revision Slice | H3 | blocked | DT-48, DT-52, DT-72 | Audio golden/recovery review |
| DT-74 | Level-Matched Audition, Export, and Accessibility | H3 | blocked | DT-73 | Audio/accessibility/usability review |
| DT-75 | Cancellation, Crash Recovery, and Long-File Memory | H3 | blocked | DT-70, DT-74 | Target-hardware stress gate |
| DT-76 | Closed Desktop Usability Pilot | H3 | blocked | DT-68, DT-75 | Consent/usability owner review |
| DT-77 | Evidence-Led Failure Taxonomy and Improvement Brief | H4 | blocked | DT-64, DT-66, DT-67, DT-76 | Audio/research prioritization |
| DT-78 | Deterministic Champion Improvement Preregistration | H4 | blocked | DT-77 | Evaluation lock |
| DT-79 | Deterministic Champion Candidate Implementation | H4 | blocked | DT-52, DT-78 | Scope/audio review |
| DT-80 | Champion Comparison and Promotion Decision | H4 | blocked | DT-79 | Independent evidence gate |
| DT-81 | Differentiable/Model Candidate Reproduction | H4 | blocked | DT-63, DT-68, DT-77 | Rights/reproducibility review |
| DT-82 | Offline Challenger Sandbox and Promotion Gate | H4 | blocked | DT-50, DT-80, DT-81 | Security/rights/rollback review |
| DT-83 | Continuous Research Watcher v1 | H4 | blocked | DT-45, DT-50 | Replay/source-health review |
| DT-84 | Integrated Security, Privacy, License, and Claim Audit | H4 | blocked | DT-68, DT-75, DT-82, DT-83 | Cross-functional audit approval |
| DT-85 | Target-Genre Corpus Expansion | H5 | blocked | DT-62, DT-68, DT-84 | Rights/coverage review |
| DT-86 | Target-Genre Beta Protocol and Release Candidate Freeze | H5 | blocked | DT-76, DT-80, DT-85 | Preregistration/release freeze |
| DT-87 | Closed Target-Genre Beta Execution | H5 | blocked | DT-86 | Consent/security/operations gate |
| DT-88 | Cross-Platform Packaging and Distribution Proof | H5 | blocked | DT-51, DT-75, DT-84, DT-86 | Clean-machine/legal release review |
| DT-89 | Signed Updates, Rollback, Deletion, and Support Drill | H5 | blocked | DT-88 | Incident/support owner gate |
| DT-90 | Replicated Quality and Usability Evidence | H5 | blocked | DT-87, DT-89 | Independent replication review |
| DT-91 | Public Release and Claims Gate | H5 | blocked | DT-88, DT-89, DT-90 | Owner/science/legal/security approval |
| DT-92 | General-Mixing Expansion Decision | H5 | blocked | DT-91 | Explicit product/architecture decision |
