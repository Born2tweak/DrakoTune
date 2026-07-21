# End-to-End Traceability Matrix

**Status:** validated derived navigation and coverage view v1.2  
**Purpose:** show where each consequential requirement comes from, how it is specified, where it is implemented, how it is verified, and what it may claim.

This matrix has no independent authority. Evidence records, canonical specifications, the threshold registry, and `MILESTONE_REGISTRY.yaml` are authoritative; drift validation regenerates or blocks this view.

| Requirement | Evidence/risk | Canonical contract | Milestones | Verification evidence | Maximum claim before later gates |
|---|---|---|---|---|---|
| Honest result states | E-003–E-006; R-001/R-002 | Quality spec; schema examples | DT-45/48 | Semantic truth table and adversarial fixtures | Engineering behavior only |
| Independent identities | E-004/E-008; R-008/R-016 | Data/provenance spec | DT-46/49/56 | Duplicate/graph/correction tests | None |
| Metric applicability | E-009/E-010; R-011 | Quality spec; threshold registry | DT-47 | Metric-card/domain/reference tests | Named engineering measurement |
| Collateral harm cannot hide | E-003; R-001 | Quality spec; verdict schema | DT-48/64 | Harsh fixture and multiaxis property tests | No perceptual claim |
| Purpose-specific rights | E-012/E-017; R-008/R-010/R-019 | Data/provenance and security/licensing specs | DT-49/55/62 | Purpose authorization and withdrawal drill | Only rights-authorized use |
| Reproducible build | E-002/E-014; R-006/R-018 | System and lab specs | DT-50 | Clean environment parity, hashes, SBOM | Exact-build engineering facts |
| Distribution branch | E-014; R-005; D-015 | Security/licensing spec | DT-51/71/88 | Actual-bundle SBOM/license/build reviews | No public binary until DT-91 |
| Stable DSP/application seam | CA-04/CA-06; R-018 | System architecture | DT-52/69 | Golden/contract/parity/recovery tests | Baseline behavior only |
| Valid product promise | E-016; R-003/R-004 | Product spec | DT-53/54 | Discovery and usability result packages | Tested workflow/scope facts |
| Fair rights-clean acquisition | E-012/E-018; R-017 | Data and security/privacy specs | DT-55/58/62/65 | Contract/purpose/spend/consent audit | No efficacy claim |
| Immutable tie-aware listening | E-004–E-006; R-002/R-009 | SAP and schema examples | DT-56/61 | Duplicate/tie/order/panel/concurrency fixtures | Protocol validity only |
| Cluster-aware inference | E-011 | SAP | DT-57/59/60 | Simulation calibration, diagnostics, preregistration | No confirmatory claim until study |
| Scientifically set thresholds | E-011; N-002 | Threshold registry | DT-59/60 | Pilot estimates and frozen simulations | Pilot remains exploratory |
| Rights-clean grouped corpus | E-007/E-012; R-003/R-016 | Data/provenance spec | DT-62/63/85 | Hash/rights/group/near-duplicate/coverage validation | Named corpus composition |
| Calibrated champion | E-003/E-007 | Quality/lab specs | DT-64 | Frozen held-out calibration package | Bounded objective calibration |
| Clean preservation | E-005/E-006; R-001/R-002 | Quality spec and SAP | DT-66/68/90 | Preregistered equivalence/harm and replication | Named build/population only after approval |
| Repair efficacy | E-003/E-007; R-001/R-003 | Quality spec and SAP | DT-67/68/90 | Preregistered defect/harm and replication | Named defect/build/population only |
| Claim traceability/retraction | R-004/R-008/R-019 | Security/licensing/claims spec | DT-68/84/90/91 | Dependency/rights/expiry/suspension tests | Exact approved wording only |
| Local non-destructive projects | E-016; R-014 | Desktop/project spec | DT-69/72/73/74 | Original, atomic revision, relink, export E2E | Local workflow facts |
| Honest duration/performance | E-015/N-012; R-007 | Threshold and desktop specs | DT-70/75 | Target-device RSS/disk/cancel/crash/audio-equivalence | Named hardware/build/duration only |
| Accessible recoverable UI | Product P-06/P-07; R-014 | Desktop spec | DT-72–76 | Keyboard/AT/fault/usability evidence | Bounded usability facts |
| Evidence-led DSP changes | R-001/R-016; D-008 | Lab spec | DT-77–80 | Preregistered champion comparison/rollback | No inherited old-build claim |
| Safe model research | E-013/E-017; R-010/R-012 | Lab/system architecture | DT-81/82 | Rights/reproduction/isolation/resource/promotion tests | Research observation only |
| Continuous renewal | E-019; R-012/R-020 | Continuous-research spec | DT-83 | Frozen replay, partial-failure, proposal audit | No adoption/claim authority |
| Integrated assurance | R-004–R-020 | Security/privacy/licensing/claims spec | DT-84/89 | Threat/license/deletion/update/rollback drills | Readiness evidence, not release |
| Target-genre beta | R-003/R-016 | Product, SAP, desktop specs | DT-85–87 | Frozen RC, consent, beta result/incident package | Closed-study evidence only |
| Public release | All critical evidence/risks | All canonical specs | DT-88–91 | Signed installers, operations drill, replication, claim audit | Exact signed claim matrix |
| General-mixing expansion | Q-002/Q-009; R-003/R-007 | Product/system decision framework | DT-92 | New decision packet and future T0–T4 roadmap | Existing claims do not expand |

## Coverage rule

A requirement is not complete merely because a milestone is complete. Its verification evidence must exist, remain rights-valid and build-compatible, and support the requested claim level. Missing links block promotion and create a roadmap/evidence finding automatically.
