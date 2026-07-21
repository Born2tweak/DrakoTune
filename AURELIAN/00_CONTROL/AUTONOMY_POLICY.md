# Autonomy Policy

## Purpose

Automation may collect evidence, run deterministic checks, prepare diffs, and recommend work. It must not silently change the product’s legal, scientific, financial, or public posture.

## Default autonomous authority

- Read repository state and public primary sources.
- Create or revise internal documentation, schemas, validators, fixtures, tests, and implementation code inside an already approved milestone.
- Run tests, fixtures, benchmarks, linters, deterministic scans, non-destructive experiments, and already-authorized offline challenger comparisons.
- Update research snapshots, evidence ledgers, negative results, risk status, and proposed roadmap diffs.
- Advance a milestone through automatic gates when dependencies, tests, evidence, and resource limits are machine-verifiable.
- Start dependency-independent milestones in parallel under `05_ROADMAP/AUTONOMY_AND_PARALLEL_EXECUTION.md`.
- Retry bounded transient failures, quarantine invalid artifacts, revert an unpromoted candidate, and continue other unblocked work.
- Fail closed when provenance, rights, identity, applicability, credentials, or external authority is missing.

## Human-only gates

- Spend money or enter a contract.
- Contact, recruit, compensate, schedule, or enroll a person.
- Accept legal terms, grant or interpret rights, approve consent language, acquire restricted data, or alter retention/withdrawal obligations.
- Use unavailable credentials, pass identity/biometric/CAPTCHA verification, sign an attestation, or act as the user in a legally meaningful way.
- Change production, publish/distribute software, rotate/revoke real signing keys, or expose a service to new users.
- Approve public claim language, publish research/audio/examples, or disclose artist/listener information.
- Promote a model or materially audible DSP change to production after confirmatory evidence.
- Delete irreplaceable source/evidence or execute an actual consent-withdrawal deletion plan.
- Make a product-scope decision that changes the supported user/task, distribution branch, or release posture.

Architecture proposals, internal dependency updates with compatible reviewed licenses, test thresholds derived by an already approved preregistered procedure, documentation changes, and reversible source-code implementation do **not** require repeated owner approval. Their milestone acceptance is automatic when objective evidence is complete; exceptions escalate only on a configured risk trigger.

## Review terminology

In milestone Field 15 text, “architecture review,” “audio review,” “security review,” or “accessibility review” means an evidence-producing review activity, not automatically a blocking human approval. It is autonomous unless it requires a named external expert, physical device interaction unavailable to the agent, subjective promotion of a materially audible change, or one of the human-only gates above.

## Prohibited autonomous actions

- Fabricating citations, listener responses, rights, consent, or test evidence.
- Treating an unavailable source or skipped test as a pass.
- Converting correlation, metric movement, or internal preference into a professional-quality claim.
- Circumventing access controls, license terms, robots policies, rate limits, or paywalls.
- Spending, contracting, messaging participants, or shipping a binary without authorization.
- Rewriting historical evidence to make a current result appear stronger.

## Evidence handling

Every automated finding records query/configuration, source, retrieval time, software version, raw artifact identity, transform identity, outcome, uncertainty, and failure state. Corrections append a new record linked to the superseded record. Missing evidence is `unknown`, never `false` or `pass`.

## Roadmap renewal

The watcher creates a change set containing source diffs, applicability, rights, expected value, uncertainty, affected risks/specs/milestones, and rollback. It may automatically merge metadata corrections, source-health state, evidence append operations, readiness transitions, and non-strategic maintenance inside accepted policy. Product scope, legal/rights posture, spending/people, model production adoption, public claims, distribution, or production changes remain human-only.
