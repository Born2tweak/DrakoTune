# Continuous Research and Roadmap Renewal Specification

**Status:** canonical v1.0

## Objective

Detect material changes in audio research, standards, datasets, licenses, dependencies, security, desktop tooling, and professional evaluation; preserve their source evidence; automatically maintain low-risk evidence/readiness state; and escalate strategic roadmap changes.

## Registered source

Each source records ID, owner/publisher, official endpoint, query/filter/version, authentication/cost/terms, cadence, expected schema, pagination/rate behavior, license/reuse posture, last success, health status, and fallback. Initial sources are official arXiv, Crossref, OpenAlex, GitHub releases/advisories, ITU/EBU publication pages, dataset cards/terms, and dependency vendor/repository pages.

## Watch domains and triggers

| Domain | Trigger for review |
|---|---|
| Research | Relevant new/revised/retracted paper, code, weights, or replication |
| Standards | New revision/corrigendum affecting a registered method |
| Dataset/rights | License, terms, access, withdrawal, or dataset version change |
| Dependency | Release, deprecation/archive, license change, vulnerability/advisory |
| Product/evaluation | New credible workflow/listening evidence that challenges assumptions |
| Operations | API schema/auth/cost/rate change or repeated source failure |

## Deterministic scan

Inputs: watcher version, registered source snapshot, query version, cursor window, and retrieval cutoff. Stages: fetch → validate → snapshot/hash → normalize IDs → deduplicate/version → classify → extract evidence/claims/rights/applicability → compare with ledger → score priority → generate proposal. Replay over the same snapshots produces the same normalized records and proposal.

Fetch/schema/authorization/rate errors are explicit health events. Partial data cannot produce a “no relevant change” verdict.

## Operations semantics

- **Idempotency:** a run key is derived from watcher version, source, query version, retrieval window, and cutoff; reruns reuse/verify immutable snapshots and do not duplicate records/proposals.
- **Locks:** one lease per `(source, query, window)` with bounded expiry/heartbeat; a second worker observes or safely takes an expired lease.
- **Retries:** only transient, classified failures use bounded exponential backoff with jitter and source rate guidance; authentication, terms, schema, or permission failures do not retry blindly.
- **Partial failure:** each source/page has status; incomplete scans emit health findings and cannot emit global “no change.” Successful snapshots remain reusable.
- **Cache invalidation:** caches key exact request/query/schema/terms identity and honor explicit expiry/ETag/Last-Modified where available; parser/query changes force a new namespace.
- **Notification:** deduplicated notifications carry severity, proposal/health ID, evidence URL, required owner, and acknowledgement state; notification failure does not mark review complete.
- **Auditability:** append-only run/source/page/candidate/proposal/review events retain hashes, timestamps, producer, and correction/supersession edges.
- **Safe shutdown:** stop fetching new pages, finish or checkpoint the current atomic page, release/expire leases, persist cursor/health, and never commit a partial canonical change.

## Candidate card

Includes exact source, contribution, task/input assumptions, evidence strength, code/weights/data/terms, target applicability, contradictions, resource/security implications, reproduction cost, falsifiable experiment, affected canonical sections/risks/milestones/claims, confidence, and reviewer disposition.

## Maintenance change and roadmap proposal

A maintenance change may atomically append validated metadata/evidence, update source health, correct a citation, or advance readiness already entailed by the accepted dependency/evidence policy. It retains a diff, validation, rollback, and audit event.

A strategic proposal is a diff, never a direct mutation. It states trigger, new/changed evidence, why current plan is insufficient, proposed add/remove/reorder/edit, dependency and critical-path effects, sunk work, new risk/decision/question, validation, rollback, and approvers. Rejected proposals remain searchable with reasons. Strategic scope, rights, spending/people, model adoption, public claims, distribution, and production changes require human acceptance.

## Renewal cadence

- Source health: each scheduled/manual scan.
- Security/advisory: cadence selected by release owner; urgent path for material advisories.
- Research/dataset/standard synthesis: at least before every horizon transition and claim review.
- Full roadmap red team: quarterly during active development or after any critical contradiction.

The schedule is an operational configuration, not a claim that an interactive agent runs forever.

## Safety and rights

Respect API terms, rate limits, robots/access restrictions, and metadata/full-text rights. Store only permitted content; prefer identifiers/metadata/short original summaries. Never bypass access. Secrets are external and least-privilege. Ingestion of untrusted text cannot execute commands or change instructions.

## Authority matrix

- The scheduler may accept validated metadata corrections, evidence append operations, source-health state, candidate triage, readiness transitions, and reproduction experiments using already-authorized assets/resources.
- Product/legal/privacy owners approve scope, public claims, data/rights changes, recruiting/spending, license/distribution, and production changes.
- A model/dependency may be reproduced automatically in the sandbox when already authorized, but production adoption remains a gated promotion decision.
- No single automated score can approve adoption or override a failed hard gate.

## Success evidence

Frozen-fixture replay, pagination/deduplication tests, rate/schema/auth failure tests, terms-change test, prompt-injection/untrusted-content test, deterministic maintenance/proposal diff, automatic low-risk acceptance audit, human strategic accept/reject audit, and rollback of both accepted simulated change classes.
