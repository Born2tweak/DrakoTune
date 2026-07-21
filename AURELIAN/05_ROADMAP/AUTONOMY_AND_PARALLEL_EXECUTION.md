# Autonomy and Parallel Execution Policy

**Status:** canonical execution policy v1.1  
**Purpose:** keep scientific and legal gates hard without turning routine engineering into owner-approval theater.

## Operating rule

At initialization, DT-45 is the only ready milestone and none is in progress. After its completion, dependency-independent work may run concurrently. The scheduler may keep up to four active lanes when they do not edit the same authority record, use confirmatory data, exceed local resource budgets, or invoke a human-only gate.

## Default lanes after DT-45

| Lane | Earliest work | Autonomous scope | Merge/handoff constraint |
|---|---|---|---|
| Evidence semantics | DT-46 → DT-48 | Schemas, validators, migrations, adversarial tests | DT-48 waits for DT-46 and DT-47. |
| Metrics and evaluation | DT-47 → DT-57 | Metric cards, applicability tests, statistical simulation | Human method approval only before real confirmatory collection. |
| Reproducibility and distribution research | DT-50 → DT-51 | Locks, SBOM, build fingerprints, branch decision packet | Owner/counsel chooses the distribution branch. |
| Product and data planning | DT-53 → DT-55 | Discovery protocol, strata, acquisition/consent packet | Contact, spending, and legal terms remain human-only. |
| Continuous research | DT-83 preparation | Frozen API fixtures, queries, replay, and source-health tests | Paid/credentialed scheduled operation requires its authority. |

Later lanes may overlap desktop service/performance work, data-ingest tooling, and watcher work wherever the dependency graph permits.

## Automatic milestone acceptance

A milestone may automatically move from `in_progress` to `complete` when:

1. all machine-verifiable acceptance criteria pass;
2. required artifacts and completion evidence are content-addressed;
3. no human-only gate applies to the actual change;
4. no critical or high unresolved finding affects the handoff;
5. data rights and resource use remain inside prior authority;
6. canonical registry and project state update atomically;
7. rollback or quarantine has been exercised where required.

The scheduler records the decision and continues to the next unblocked milestone without asking for a ceremonial “continue.”

## Escalation triggers

Escalate only for money, people, credentials, legal/rights/consent, public claims or publication, production/release, irreversible deletion, material product-scope change, or a failed/ambiguous critical safety gate. Present one consolidated decision packet with a recommended choice, consequences, and safe default.

## Concurrency safety

- Acquire a lease for each canonical file, schema, or module family before mutation.
- Parallel lanes use isolated branches/worktrees or non-overlapping patches and reconcile before acceptance.
- A milestone cannot consume an unaccepted artifact from another lane.
- Confirmatory data are read-only and unavailable to tuning lanes.
- CPU, RAM, and disk quotas prevent experiments from starving validation work.
- Failed lanes quarantine artifacts and release leases without blocking unrelated lanes.

## State authority

`MILESTONE_REGISTRY.yaml` is the canonical milestone state and dependency record. Markdown registry and detail files are explanatory views and execution contracts. A validator must reject drift before a milestone transition.

## Human checkpoint bundling

Related decisions are bundled—for example pilot budget, recruitment channel, and consent packet; or distribution branch, repository license, and proposed bundle. Actions already inside the accepted envelope do not request repeated approval.
