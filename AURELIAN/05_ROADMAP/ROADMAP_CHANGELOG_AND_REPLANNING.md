# Roadmap Changelog and Replanning Protocol

## Changelog

| Version | Date | Change | Trigger | Approval |
|---|---|---|---|---|
| 1.0 | 2026-07-21 | Created DT-45–DT-92 evidence-first roadmap and superseded post-M44 planning authority. | Master research/architecture/roadmap audit. | Proposed for owner acceptance; no milestone started. |
| 1.1 | 2026-07-21 | Added machine-readable status authority, autonomous acceptance, four dependency-safe lanes, deeper research evidence, concrete schemas, thresholds, and traceability; reconciled README claims. | Independent 8.8/10 document review. | Revision requested by owner; no milestone started. |
| 1.2 | 2026-07-21 | Normalized all 48 Field 15 gates, expanded YAML into a complete execution manifest, marked historical and derived authorities, formalized schema fields/enums/errors, and added exact high-consequence method/data/license extractions. | Independent 9.2/10 review identified remaining execution ambiguity and evidence granularity gaps. | Revision requested by owner; no milestone started. |

## Change classes

- **Editorial:** no behavior/dependency/gate/claim change; project steward may merge with review.
- **Evidence update:** append source/result/risk; may change readiness only through reviewed proposal.
- **Milestone amendment:** changes scope, acceptance, dependency, gate, or handoff; requires affected owners and versioned diff.
- **Strategic change:** product promise, data/rights, distribution, model adoption, spending, public claim/release, or roadmap endpoint; requires explicit owner and relevant legal/scientific/security approval.

## Proposal requirements

Every replan records trigger, new/contradictory evidence, affected decisions/risks/specs/claims/milestones, current sunk work, proposed diff, dependency/critical-path impact, resources, validation, rollback, author, reviewers, and disposition. Removed milestones become superseded, never vanish. Failed experiments remain in negative results.

## Automatic triggers for review

- Critical safety/privacy/license/rights/claim failure.
- Invalidated statistical method, data leakage, consent withdrawal, or retraction.
- Candidate build/model/dependency license/security change.
- Two milestone handoff failures for the same assumption.
- Target-hardware budget miss or inaccessible/unsafe core workflow.
- Material new evidence from the watcher.
- Horizon completion and pre-release/claim gate.

## Readiness changes

A completed dependency triggers an automatic readiness evaluation. The scheduler checks exact completion evidence, open findings, rights/resource/human-only gates, and canonical-spec compatibility; it then updates the YAML registry atomically and may start the child within the four-lane concurrency policy. It asks the owner only when an escalation trigger applies.

## Threshold changes

Before data, revise through a versioned preregistration with rationale. After pilot, set confirmatory thresholds through DT-60. After confirmatory outcomes are available, threshold/endpoint changes create a new exploratory or future confirmatory experiment; they never rewrite the completed result.
