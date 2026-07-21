# L — Security, Privacy, and Claims Report

**As of:** 2026-07-21

## Security and privacy

Vocal recordings may contain identity, unpublished creative work, and confidential session material. The hosted pilot accepts uploads and creates job/download artifacts; its signed links, retention, rate limiting, and concurrency controls are useful but do not eliminate access, log, deletion, dependency, or incident risks. The desktop product reduces transfer risk only if it remains local by default and avoids leaking paths/audio through projects, logs, crash reports, updates, or telemetry.

Required controls include validated audio parsing, bounded resources, least-privilege storage, retention enforcement, immutable access/deletion audit, dependency/advisory review, safe temporary-file permissions, redacted logs, explicit telemetry opt-in, signed updates, and incident/retraction playbooks.

## Claims

Current permissible language: deterministic prototype; tested on repository fixtures; produces inspectable DSP plans; no professional-quality validation yet. Prohibited until gated: “professional,” “studio quality,” “AI mixing engineer,” generalized “improves vocals,” genre superiority, clean do-no-harm, or privacy absolutes.

Every claim needs an ID, exact wording/context, population/task, supporting experiment and immutable results, independence level, rights, statistical status, subgroup limits, owner, approval, expiry, and withdrawal conditions. A failed control or consent deletion automatically suspends affected claims.

## Threat and claim evidence audit

| Surface/evidence | Existing control | Residual unknown/conflict | Required decision or verification |
|---|---|---|---|
| Hosted upload/job/download source | Signed links, retention concepts, rate limiting, concurrency controls. | Live deployment/configuration, deletion execution, access logs, parser isolation, and incident response were not verified. | Treat code and deployment evidence separately; DT-84 verifies actual boundary if retained. |
| Local desktop hypothesis | Core processing can operate without cloud/account. | Temp files, paths, crash logs, project sharing, updates, and dependencies can still leak or execute untrusted content. | Local-off/telemetry-off defaults plus DT-71/75/84 threat tests. |
| Media parser/native stack | FFmpeg and native libraries handle untrusted audio. | Malformed/resource-exhausting files and vulnerable versions remain attack surfaces. | Controlled builds, bounds, malicious fixtures, advisory monitoring. |
| Research identity/consent | Proposed separation of direct identity and pseudonymous responses. | No production protected store or withdrawal drill exists yet. | DT-46/49 schema and access/deletion verification. |
| Root/project claims | README now disclaims independent perceptual validation. | Historical phrases and deployment statements can drift from canonical claim state. | Claim registry plus automated forbidden/stale wording scan. |
| Audio examples/results | Can communicate product behavior. | Examples are claims and may expose recording/composition/performer identity or cherry-pick outcomes. | Require publication-specific rights, representative labeling, build/result linkage. |

## Claims falsification rule

A claim is suspended when its build differs, evidence expires or is withdrawn, analysis is invalidated, a launch-critical subgroup fails, distribution terms change, or actual deployment behavior contradicts its security/privacy wording. Suspension occurs automatically; republication remains a human-only public-claim gate.

## Recheck triggers

Reopen the threat and claim audit on deployment/configuration change, parser/native dependency advisory, new project/update/telemetry behavior, new participant or artist data, rights withdrawal, incident, claim wording/build change, distribution-branch decision, or before every external release.
