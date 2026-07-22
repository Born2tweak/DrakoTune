# DrakoTune Full Autonomous Remediation Program

Status: governing execution contract  
Mode: continuous autonomous remediation  
Target: evidence-backed 10/10 in every required category  
Repository facts: must be reconciled from the actual DrakoTune repository

## 1. Mission

Transform DrakoTune into an autonomous, reproducible, production-integrated, evidence-driven vocal-processing product that can improve its engineering system and actual audio results without routine human direction.

The program must research, plan, implement, integrate, test, review, recover, validate, document, release-gate, and extend its own roadmap. It must remain honest about what the evidence supports and abstain when evidence is insufficient.

This document does not authorize unsupported claims such as “Grammy-level,” “professional quality,” “universally better,” “safe for every voice,” or “mastering replacement.” Those claims remain prohibited until the evidence and claims systems independently authorize them.

## 2. Execution mandate

The executing agent must:

1. Inspect the actual repository before relying on prior transcripts or milestone labels.
2. Reconcile branches, open pull requests, CI, production entry points, roadmap documents, evidence, tests, and canonical state.
3. Replace every `RECONCILE_FROM_REPOSITORY` placeholder using direct repository or external-system evidence.
4. Correct false completion states and reopen milestones when necessary.
5. Build or repair the machine-readable execution controller described by this package.
6. Select the highest-priority dependency-ready milestone.
7. Execute the smallest coherent vertical slice that produces independently verifiable value.
8. Run proportional tests, adversarial checks, production-reachability checks, and independent review.
9. Commit intentionally, push, monitor CI, repair failures, and continue.
10. Update canonical state and evidence before selecting the next milestone.
11. Generate new milestones whenever research or implementation exposes a gap.
12. Maintain 10–20 implementation-ready milestones beyond the active frontier when enough evidence exists.
13. Continue until every safely executable milestone is complete or the remaining frontier requires human authority.

The agent must not stop merely because it completed a phase, wrote a report, opened a pull request, started CI, encountered a technical failure, needs research, faces a reversible architecture choice, or discovered missing work.

## 3. Definition of 10/10

Ten out of ten is a release-gated state, not a subjective rating. Every category in `control/scorecard.yaml` must independently pass. No averaging is permitted.

A category passes only when:

- all mandatory controls are integrated into real production paths;
- acceptance and adversarial tests pass;
- immutable evidence is attached to an exact commit and environment;
- known limitations and prohibited claims are recorded;
- rollback or recovery behavior is verified where applicable;
- the evidence is current and within its declared applicability domain;
- an independent audit has not found an unresolved release-blocking defect.

If one category fails, the system must block the affected release capability or claim while continuing safe remediation elsewhere.

## 4. Authoritative state hierarchy

When records disagree, use this precedence:

1. Reproducible behavior at the verified commit.
2. Production entry-point execution and generated evidence.
3. CI records and immutable artifacts.
4. Machine-readable canonical state and registries.
5. Current decision records and architecture decisions.
6. Roadmaps and narrative documentation.
7. Historical transcripts.

Documentation must be corrected when contradicted by higher-authority evidence.

## 5. Continuous execution loop

The controller must repeatedly perform this loop:

1. Acquire or recover the work lease.
2. Reconcile local state, remote state, open pull requests, and CI.
3. Validate control-plane schemas and evidence links.
4. Recalculate milestone readiness.
5. Select the highest-priority safe milestone.
6. Create or recover its working branch.
7. Implement one coherent vertical slice.
8. Run formatting, static checks, unit tests, integration tests, audio goldens, end-to-end tests, and milestone-specific adversarial tests.
9. Run independent architecture, correctness, security/privacy, rights, reproducibility, claims, product-integration, and roadmap-completeness reviews.
10. Repair blocking findings and repeat verification.
11. Record artifact hashes, environment fingerprint, test results, limitations, negative results, and claim effects.
12. Push and observe CI until terminal.
13. Diagnose and repair CI failure when within authority.
14. Merge only when all required gates pass and repository policy permits autonomous merge.
15. Reconcile canonical state from the merged commit.
16. Detect newly exposed gaps and add dependency-placed milestones.
17. Select the next ready milestone immediately.

If no milestone is ready, the controller must classify why. It must continue preparatory or unrelated work before requesting human input.

## 6. Human-authority boundary

Routine engineering work is autonomous. This includes inspection, research, implementation, testing, CI repair, reversible migrations, dependency updates within policy, documentation, experiment preparation, synthetic evaluation, milestone creation, and roadmap maintenance.

Human authority is limited to:

- participant consent and participant-facing study terms;
- rights or privacy terms for real non-public audio;
- spending or paid recruitment;
- unavailable credentials, verification codes, CAPTCHA, or biometric steps;
- material legal, licensing, or distribution obligations;
- destructive deletion that cannot be recovered;
- final public release when repository policy reserves that authority;
- publication of strong professional-quality claims.

Before requesting a decision, the controller must finish all safe preparation, research options, recommend a default, show consequences, batch related decisions, and identify work that continued meanwhile.

## 7. Remediation sequence

Phases are ordered dependency groups. They are not approval checkpoints.

### Phase A — Repository reconciliation and audit freeze

Required actions:

- enumerate every production entry point: CLI, API, batch, web/listening, report generation, preset promotion, and release surfaces;
- reconcile current branch, remote default branch, open pull requests, CI, tags, and release artifacts;
- classify every existing milestone as planned, implemented, integrated, verified, validated, released, blocked, or superseded;
- locate code with no production callers and production paths bypassing canonical systems;
- identify stale, contradictory, manually asserted, or unlinked evidence;
- freeze or quarantine unsupported public claims;
- populate the deficiency and evidence registries;
- calculate the first ready queue from facts.

Exit gate: a fresh agent can identify the exact current frontier and next automatic action from repository artifacts alone.

### Phase B — Reproducibility repair

Repair DT-50 or its reconciled successor so that:

- locks derive only from declared dependencies;
- runtime, development, web, research, and optional groups are separated;
- supported platforms and unsupported boundaries are explicit;
- CI installs from committed locks in clean environments;
- FFmpeg version, build configuration, codecs, licenses, and hashes are recorded;
- SBOM output uses CycloneDX or SPDX;
- distributable artifacts are rebuilt, reinstalled, and tested;
- full tests and audio goldens run from locked environments;
- repeated renders satisfy documented deterministic tolerances;
- vulnerabilities are reported with severity and disposition;
- dependency update and rollback procedures are tested.

Exit gate: a clean supported environment reconstructs DrakoTune and produces equivalent verified outputs without workstation leakage.

### Phase C — Production integration closure

Integrate DT-45 through DT-48 or their reconciled equivalents into every applicable real path:

- ingestion creates provenance;
- processing maintains input/output lineage;
- metrics consult applicability and uncertainty definitions;
- evaluation produces typed evidence;
- verdicts include improvement, safety, collateral harm, applicability, and abstention;
- reports and interfaces render only evidence-eligible claims;
- presets cannot promote without complete evidence;
- CLI, API, batch, web/listening, and report flows agree;
- missing provenance, unknown rights, invalid evidence, or unsupported applicability fail closed;
- legacy bypasses are migrated or blocked.

Required adversarial tests include missing provenance, unknown rights, inapplicable metric, conflicting evidence, quality improvement with collateral harm, invalid listening study, claim escalation, and preset-promotion bypass.

Exit gate: removing or bypassing a canonical evidence component causes end-to-end tests to fail.

### Phase D — Autonomous execution closure

Implement and verify:

- machine-readable readiness calculation;
- deterministic milestone selection;
- work leases and stale-lease recovery;
- CI polling, log classification, repair, and continuation;
- retry budgets and exponential backoff for transient failures;
- evidence-based completion authority;
- automatic gap-to-milestone creation;
- rolling 10–20 milestone lookahead;
- crash and session recovery;
- consolidated human decision packets;
- automatic quarantine and rollback;
- seeded unattended failure rehearsal.

Exit gate: an unattended rehearsal selects work, catches a seeded defect, repairs it, handles failed CI, merges verified work, updates evidence, creates a newly discovered milestone, and continues.

### Phase E — Targeted research and decision conversion

Execute the streams in `control/research-registry.yaml`. Research is incomplete unless it produces:

- source-backed findings with dates and applicability;
- explicit decisions or bounded alternatives;
- architecture decision records where appropriate;
- calibration or validation experiments;
- dependency-placed milestones;
- claims enabled, restricted, or prohibited;
- a monitoring trigger for future evidence changes.

Research must not silently change frozen product behavior.

### Phase F — Evaluation validity

For every metric, establish:

- role: safety gate, diagnostic, comparison control, perceptual proxy, optimization target, descriptive-only, or prohibited-for-quality;
- required reference signal and alignment assumptions;
- applicability domain;
- calibration source or experiment;
- uncertainty and abstention rules;
- failure behavior for silence, low signal, clipping, loudness mismatch, and alignment errors;
- permitted and prohibited interpretations.

Exit gate: no metric influences a verdict without documented applicability, calibration, uncertainty, and evidence.

### Phase G — Rights-cleared evaluation corpus

Build or authorize a corpus covering the declared product domain, including varied voices, ranges, delivery styles, genres, microphones, rooms, noise, reverberation, clipping, plosives, sibilance, breathiness, proximity effect, short clips, and full songs.

Every asset must record provenance, permitted use, retention, deletion, identity protection, subgroup metadata where appropriate, train/evaluation separation, duplicate checks, and leakage checks.

Public and synthetic assets may be processed autonomously when licenses clearly permit the intended use. Ambiguous licenses or original participant recordings require the relevant human gate.

Exit gate: the corpus supports only the scope its rights and coverage can defend.

### Phase H — Qualified listening validation

Build randomized, blinded, loudness-matched evaluation with:

- appropriate A/B, ABX, preference, defect, or MUSHRA-style protocol selected by the research decision;
- listener qualification;
- side and order randomization;
- ties and no-meaningful-difference responses;
- separate preference, defect, and harm questions;
- duplicate trials and attention checks;
- predefined sample size, exclusion, cancellation, promotion, and rejection rules;
- confidence intervals, subgroup analysis, and multiple-comparison handling;
- preserved negative outcomes.

Exit gate: no preset is called better without preregistered qualified listening evidence and acceptable subgroup harm results.

### Phase I — Closed-loop DSP advancement

For each experiment:

1. Identify one measurable vocal defect and intended domain.
2. Freeze the baseline and experiment manifest.
3. Generate bounded candidate treatments.
4. Run safety and technical gates.
5. Run calibrated objective diagnostics.
6. Reject obvious regressions.
7. Run qualified listening when perceptual claims are involved.
8. Analyze subgroup effects and collateral damage.
9. Promote, revise, reject, or quarantine.
10. Preserve positive and negative results.
11. Schedule the next experiment based on residual weakness.

Candidate domains include plosives, sibilance, harshness, dynamics, tonal imbalance, breath/noise handling, proximity buildup, intelligibility, presence, artifact-free leveling, preset selection, and full-song consistency.

Exit gate: every promoted treatment provides meaningful improvement within its declared domain without unacceptable harm.

### Phase J — Product usability, accessibility, and recovery

Validate the full non-engineer workflow: upload, analysis, treatment selection, comparison, understandable abstention, progress, failure recovery, export, original preservation, reproducibility, privacy, and deletion.

Test keyboard and screen-reader use, contrast, warnings, slow devices, long files, interruption, corrupt uploads, unsupported formats, storage failure, and export failure.

Exit gate: representative target users can complete the supported workflow without engineering assistance, and failures do not lose original audio.

### Phase K — Reliability, release, and operations

Implement versioned immutable presets, canaries, monitoring, quality-regression detection, quarantine, rollback, audit logs, incident runbooks, deletion, backup/restore, budgets, rate limits, abuse handling, secrets management, dependency maintenance, and release-claim review.

Exit gate: a seeded production regression is detected, quarantined, rolled back, and documented without corrupting original audio or overstating results.

### Phase L — Independent final audit

An audit separate from implementation must attempt to disprove reproducibility, integration, evaluation validity, generalization, harm controls, privacy, accessibility, security, operational recovery, autonomous continuation, and every public claim.

Any failed category automatically creates or reopens remediation work. No discretionary override can produce 10/10.

## 8. Milestone completion contract

Every milestone must record:

- desired outcome and dependencies;
- affected production paths and explicit non-goals;
- implementation deliverables;
- acceptance criteria and adversarial cases;
- exact commands and results;
- production reachability evidence;
- full regression result;
- commit, CI run, environment, input, output, and artifact hashes;
- limitations and negative results;
- claim effect and applicability domain;
- rollback target and recovery result;
- completion authority;
- newly unblocked milestones;
- evidence freshness and expiration.

A milestone is not complete if any mandatory field is missing, asserted without evidence, stale, contradicted, or bypassable.

## 9. Blocker policy

| Condition | Required autonomous response |
| --- | --- |
| Test failure | Diagnose, repair, rerun |
| CI failure | Inspect logs, classify, repair, rerun |
| Missing dependency | Research and resolve within license/security policy |
| Reversible ambiguity | Compare options and choose the lowest-risk reversible option |
| Missing milestone | Create and dependency-place it |
| Insufficient evidence | Abstain, design evidence collection, continue preparation |
| Pending CI or external job | Poll with bounded backoff and do independent ready work |
| Transient service failure | Retry within budget and preserve resumable state |
| Missing credentials | Finish all other preparation, then request once |
| Consent, rights, spending, legal, or public-release authority | Create one consolidated decision packet |

## 10. Claim and evidence safety

Every public or generated claim must map to current evidence, applicability, rights, subgroup coverage, and expiration. If any link fails, the system must downgrade the claim or abstain.

Documentation, tests, synthetic audio, metric improvements, and unchanged goldens do not independently prove perceptual improvement. Perceptual claims require the listening evidence defined by this program.

## 11. Recovery contract

At every stable transition, write `control/canonical-state.json` atomically with:

- verified commit and branch;
- open pull request and CI state;
- active milestone and work lease;
- last completed action;
- exact next automatic action;
- ready queue;
- retry counters;
- unresolved human gates;
- evidence freshness state.

On startup, reconcile this record against Git and CI. Never trust stale state blindly. A crashed or new session must resume without requiring the user to restate context.

## 12. Final termination conditions

The program may terminate successfully only when:

- every scorecard category independently passes;
- no release-blocking deficiency remains;
- the independent audit passes;
- claims match current evidence;
- release rollback is verified;
- continuous research and monitoring jobs are scheduled or configured.

The program may pause for the user only when all remaining ready work is blocked by recorded human authority. The pause must contain one consolidated decision packet and an exact automatic continuation action for each possible response.

