# Security, Privacy, and Claims Audit

**Verdict:** useful hosted safeguards exist, but privacy and claims are not yet governed end to end; local-first reduces but does not eliminate risk.

## Assets and threat surfaces

- Unreleased vocal/audio and derived renders.
- Artist/listener identities, consent, qualifications, and responses.
- Local project paths, logs, crash dumps, temp files, manifests, and exports.
- Hosted upload/job/download endpoints, signed links, retention jobs, resource exhaustion.
- Dependencies, FFmpeg/media parsers, installers, update channel, model assets, signing keys.
- Evidence/claim linkage and public audio examples.

## Findings

M44 rate limiting/concurrency code improves resource-abuse posture. Signed downloads and retention are positive controls. However, production deployment state was not verified, and no end-to-end evidence proves deletion, log redaction, incident handling, consent propagation, or claim retraction. Local projects have no canonical safe schema yet. The repository lacks a formal claim registry.

## Required controls

Validate file type by content, bound decode/runtime/disk, use isolated temp directories with restrictive permissions, scan/update dependencies, minimize and redact logs, default telemetry off, encrypt sensitive research identities where stored, separate lookup keys, audit access/deletion, and sign updates. Retention/deletion failures are security events. Preserve evidence without retaining source audio where a hash/provenance record suffices.

## Claim levels

1. **Engineering:** deterministic, test/fixture facts.
2. **Bounded performance:** named dataset/task/build metrics.
3. **Independent perceptual:** preregistered, rights-clean, population-specific findings.
4. **Product/generalized:** requires replicated evidence, subgroup limits, approval, and expiry.

Absence of evidence, inapplicable metrics, skipped tests, rights ambiguity, protocol deviations, or expired results block promotion. Claims must be retractable when evidence or consent changes.

## Immediate public-language boundary

Allowed: inspectable deterministic prototype; local baseline tests; experimental cleanup. Not allowed: professional/studio-quality guarantee, universal improvement, clean do-no-harm, “private” absolute, or AI engineer replacement.
