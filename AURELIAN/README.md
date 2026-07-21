# DrakoTune Aurelian Control Plane

**Baseline:** repository commit `a3c51637a0c2ed18994a6950a45a72ccb753a93d`, audited 2026-07-21.

This directory is the authoritative post-M44 research, specification, and planning control plane, revision 1.2. Existing root documents remain valuable evidence of what was built, but where they disagree with this package the authority order is:

1. executable behavior and reproducible tests;
2. accepted decision records;
3. `03_CANONICAL/` specifications;
4. `05_ROADMAP/` dependency and milestone records;
5. `04_AUDITS/` findings;
6. `02_RESEARCH/` external evidence;
7. historical root planning documents.

No roadmap milestone is permission to make a quality claim. A claim becomes eligible only through the evidence, rights, independence, and statistical gates in the canonical specifications. No public binary is authorized until the desktop distribution branch is decided.

## Navigation

- `00_CONTROL/`: state, decisions, risks, questions, negative results, sources, autonomy rules.
- `01_RESEARCH_PROMPTS/`: bounded, reusable research briefs.
- `02_RESEARCH/`: dated findings and the evidence ledger.
- `03_CANONICAL/`: product and engineering contracts.
- `04_AUDITS/`: repository, evaluation, data, performance, and governance audits.
- `05_ROADMAP/`: dependency graph, milestone registry, execution queue, migration, and change control.
- `06_EXPERIMENTS/`: future preregistrations and immutable result packages.
- `07_DATA_AND_PROVENANCE/`: future rights records, manifests, deletion records, and lineage graphs.
- `08_TOOLING/`: future Aurelian validators and research-watcher tooling.
- `09_TEMPORARY/`: explicitly non-authoritative working material.
- `10_ARCHIVE/`: superseded Aurelian records retained for traceability.

## Current stop point

Research, audits, canonical specifications, and the long-range roadmap are the deliverable. Implementation stops before milestone `DT-45` begins.

## Execution authorities

- Milestone state, dependencies, lanes, profiles, resource classes, write sets, completion evidence, claim impact, and quarantine: [`05_ROADMAP/MILESTONE_REGISTRY.yaml`](05_ROADMAP/MILESTONE_REGISTRY.yaml).
- Autonomous and parallel execution: [`05_ROADMAP/AUTONOMY_AND_PARALLEL_EXECUTION.md`](05_ROADMAP/AUTONOMY_AND_PARALLEL_EXECUTION.md).
- Requirement/evidence/verification coverage: [`05_ROADMAP/TRACEABILITY_MATRIX.md`](05_ROADMAP/TRACEABILITY_MATRIX.md).
- Concrete implementation records: [`03_CANONICAL/IMPLEMENTATION_SCHEMA_EXAMPLES.md`](03_CANONICAL/IMPLEMENTATION_SCHEMA_EXAMPLES.md).
- Known and threshold-setting decisions: [`03_CANONICAL/THRESHOLD_REGISTRY.md`](03_CANONICAL/THRESHOLD_REGISTRY.md).
- Document authority and drift control: [`00_CONTROL/DOCUMENT_MAINTENANCE_POLICY.md`](00_CONTROL/DOCUMENT_MAINTENANCE_POLICY.md).
- Revision assessment and remaining unknowns: [`04_AUDITS/DOCUMENT_PACKAGE_REVISION_REVIEW.md`](04_AUDITS/DOCUMENT_PACKAGE_REVISION_REVIEW.md).
