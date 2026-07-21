# Risk Register

Scales: likelihood and impact are 1–5. Score is their product before controls.

| ID | Risk | L | I | Score | Evidence/trigger | Control | Owner | Residual target |
|---|---|---:|---:|---:|---|---|---|---|
| R-001 | Objective metrics reward target movement while collateral harm increases. | 5 | 5 | 25 | Representative harsh fixture passed objectives while sibilance and mud rose. | Multiaxis outcomes, harm budgets, applicability, blinded listening. | Evaluation lead | ≤8 |
| R-002 | Listening analyzer produces false confidence from duplicate rows, ties, and clean-vocal logic. | 5 | 5 | 25 | Five adversarial fixtures generated false/misleading passes. | Immutable identities, uniqueness checks, tie model, preregistration, clustered analysis. | Research lead | ≤5 |
| R-003 | Synthetic corpus does not represent target production variation. | 5 | 5 | 25 | Small cells, high false-positive rates, mixed/negative SI-SDR. | Rights-clean real recordings stratified by source/session/genre. | Data lead | ≤10 |
| R-004 | Public or professional-quality claims exceed evidence. | 4 | 5 | 20 | No independent listener corpus. | Claim registry, quarantine, evidence expiry, approval gate. | Product owner | ≤4 |
| R-005 | GPL/LGPL obligations conflict with desired desktop distribution. | 4 | 5 | 20 | Pedalboard GPL-3.0; audited FFmpeg build enables GPL; PySide dual licensing. | SBOM, counsel review, explicit distribution branch, DSP adapter. | Legal/engineering | ≤8 |
| R-006 | Unpinned dependencies make results and packages irreproducible. | 4 | 4 | 16 | Lower bounds only; no lockfile; CI installs newest releases. | Locked environments, build manifests, reproducible fixtures. | Engineering | ≤4 |
| R-007 | Memory grows linearly and prevents useful desktop clip lengths. | 4 | 4 | 16 | Historical report estimates ~180 MB/minute and ~900 MB at 5 minutes. | Profiling, bounded duration, chunked/streaming render design. | Performance owner | ≤6 |
| R-008 | Consent withdrawal cannot be applied to derived artifacts or claims. | 4 | 5 | 20 | Current manifest lacks subject/session/take/derivation graph. | Rights graph, deletion ledger, reversible build/index, claim invalidation. | Data/privacy lead | ≤5 |
| R-009 | Listener/device/order/panel effects masquerade as treatment quality. | 4 | 4 | 16 | Current schema lacks environment and panel fields; no bias analysis. | Balanced randomization, device capture, panel strata, mixed effects. | Research lead | ≤6 |
| R-010 | Model or dataset code license is mistaken for weights/data rights. | 4 | 5 | 20 | DiffVox uses private/MedleyDB data; NISQA weights are non-commercial despite MIT code. | Component-level rights review and use-purpose matrix. | Data/legal | ≤5 |
| R-011 | Full-reference speech metrics are misapplied to creative vocal processing. | 4 | 4 | 16 | PEAQ/ViSQOL have specific domains and references. | Metric applicability registry and “not computable/not applicable” states. | Evaluation lead | ≤5 |
| R-012 | Automated research silently changes product direction. | 3 | 4 | 12 | Future watcher could overpromote new papers/models. | Proposal-only watcher, diffs, human approval, rollback. | Research steward | ≤3 |
| R-013 | Hosted upload service exposes private vocal recordings. | 3 | 5 | 15 | Public upload/job path exists. | Data minimization, retention enforcement, access audit, incident response. | Security owner | ≤5 |
| R-014 | Desktop project files reveal paths, audio, or metadata. | 3 | 4 | 12 | Local project format not defined. | Local-only defaults, relative paths, explicit export, redaction. | Desktop lead | ≤4 |
| R-015 | Historical roadmap completion labels imply evidence not actually present. | 4 | 4 | 16 | M24 tooling was conflated with listener validation; stale default-engine text. | Migration map and canonical state pointer. | Project steward | ≤3 |
| R-016 | Target-genre tuning overfits a few singers/songs. | 4 | 5 | 20 | No identity-aware split graph. | Grouped splits by singer/song/session and holdout strata. | Data/evaluation | ≤6 |
| R-017 | Professional recruitment underpays or creates unclear reuse rights. | 3 | 4 | 12 | No approved compensation/contract. | Budget approval, fair-rate floor, explicit grant dimensions. | Product owner | ≤4 |
| R-018 | Processing transforms introduce latency/state differences across platforms. | 3 | 4 | 12 | Native DSP/plugin dependencies and FFmpeg builds vary. | Cross-platform golden tests and build fingerprinting. | Engineering | ≤4 |
| R-019 | Public examples leak unlicensed stems or artist identity. | 3 | 5 | 15 | Evaluation and publication rights are not separated. | Publication-specific rights gate and provenance check. | Content owner | ≤3 |
| R-020 | Research sources or APIs change terms/cost unnoticed. | 3 | 3 | 9 | OpenAlex authentication/pricing changed in 2026. | Source registry dates, watcher health checks, fail-closed ingestion. | Research steward | ≤3 |

Review at every milestone handoff and whenever a control fails. A score ≥15 blocks dependent public or distribution work unless explicitly accepted by its decision owner.
