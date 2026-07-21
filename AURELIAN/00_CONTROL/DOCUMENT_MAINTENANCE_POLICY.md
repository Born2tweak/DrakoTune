# Document Authority and Maintenance Policy

**Status:** canonical v1.1

## Document classes

| Class | Contents | Mutation rule |
|---|---|---|
| Executable authority | Code, tests, immutable result packages | Behavior changes only through milestone acceptance evidence. |
| State authority | `PROJECT_STATE.md`, `MILESTONE_REGISTRY.yaml`, decision/risk/question logs | Atomic update at transition; YAML owns milestone status/dependencies. |
| Canonical contracts | `03_CANONICAL/` | Versioned change with affected decisions, milestones, schemas, and migration. |
| Evidence | Source registry, evidence ledger, research reports, audits, negative results | Append/correct with provenance; never rewrite contradiction away. |
| Execution contracts | Roadmap detail files | Stable scope/acceptance; status text is a snapshot validated against YAML. |
| Derived navigation | Markdown registry, next-five view, traceability summaries | Regenerate or validate from authorities; never independently change state. |
| Historical | Root milestone history and archived Aurelian records | Preserve with supersession pointer. |
| Temporary | `09_TEMPORARY/` | No downstream authority; delete/archive after the active decision. |

## Minimal update sets

- Milestone transition: YAML registry, project state, relevant evidence/decision/risk, completion package; derived views validated.
- New research source: source registry, evidence ledger, one domain report; roadmap only if an accepted proposal changes it.
- Canonical schema/spec change: changed spec, schema example/validator, decision, affected milestone contracts, migration.
- Claim change: claim record, supporting result/rights state, project/public surface, retraction/expiry audit.
- Rights withdrawal: withdrawal event, authorization hold, derivation/claim traversal, verification; do not broadly rewrite research history.

## Drift controls

Before accepting any milestone or document release, validate:

1. YAML milestone IDs, dependencies, statuses, and detail links.
2. Every detail milestone contains fields 1–24 exactly once.
3. Local Markdown links resolve.
4. Evidence-ledger/source IDs referenced by decisions/specs/milestones exist.
5. Threshold IDs and claim IDs are unique and resolvable.
6. Root README/current-state wording does not exceed the claim registry.
7. No canonical file points to temporary material as authority.
8. `git diff --check`, repository tests, and applicable artifact regressions pass.

## Compaction

At each horizon transition, archive superseded proposals and redundant narrative, update concise synthesis/navigation, and preserve immutable evidence links. Compaction may remove repetition but cannot delete decisions, negative results, contradictory evidence, rights events, or completed milestone proof.

## Size budget

New documents require a distinct authority or operational purpose. Prefer extending an existing domain report or registry over creating parallel summaries. Generated/derived views identify their authority. If two documents answer the same question, one is marked historical/derived or they are consolidated in the next horizon review.
