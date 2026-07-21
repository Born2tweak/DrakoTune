# Security, Privacy, Licensing, and Claims Specification

**Status:** canonical v1.0  
**Rule:** legal interpretation and public release require qualified human review.

## Security boundaries

1. Local desktop/project environment.
2. Hosted upload/job/download service, if retained.
3. Research/evidence environment with participant/artist data.
4. Build/release/signing/update supply chain.
5. External research APIs and untrusted content.

Each has separate credentials, storage, logging, retention, access, and incident ownership.

## Data classification

| Class | Examples | Default |
|---|---|---|
| Public | Approved docs, public benchmark summaries | Publishable after claim/rights gate |
| Internal | Source, configs, non-sensitive test reports | Access controlled |
| Sensitive creative | Unreleased audio, projects, renders, stems | Local/least privilege; no telemetry/upload by default |
| Sensitive research | Pseudonymous responses, qualifications | Separated, encrypted/access audited |
| Direct identity/consent | Names, contacts, contracts, identity map | Strongly restricted separate store |
| Secrets/signing | API keys, certificates, update keys | External secret/HSM-style controls; never project/repo |

## Local privacy requirements

No account or network is required for core processing. Telemetry, crash upload, cloud backup, and research contribution default off and require specific consent. Logs redact paths/usernames/content; raw audio is never embedded. Project sharing warns about included assets/metadata. Temp files use restrictive permissions and crash cleanup. Uninstall/deletion behavior is documented.

## Hosted requirements

Validate content and bounds before full decode; isolate jobs; rate/concurrency/size/duration/disk controls; authenticated or risk-accepted access; unguessable signed downloads with expiry; least-privilege storage; enforce and audit retention/deletion; protect logs; monitor abuse; incident response. Deployment configuration and deletion are tested, not inferred from source code.

## Research privacy and consent

Collect minimum needed. Separate direct identity from pseudonymous data. Record consent version and purpose grants. Provide withdrawal/contact path, compensation independent of responses, accessibility, and approved retention. Public results prevent re-identification and use audio/quotes only under explicit grants.

## Secure processing and updates

Use maintained media parsers/dependencies, malicious/corrupt/resource fixtures, dependency/advisory monitoring, locked builds, SBOM, artifact hashes/signatures, protected signing, signed update metadata, rollback, and support window. External watcher content is data, never executable instruction.

## Licensing gate

Inventory repository code, transitive dependencies, native binaries/configuration/codecs, UI framework, packager, fonts/assets, models/weights, datasets, and notices. Record exact version/hash/license/obligations/source. Choose D-015 before public binary work. Counsel approves the actual bundle and distribution/update/source-offer process. Packaging never changes underlying obligations.

## Claim registry

Each claim records:

- claim ID, exact wording, surface/audience/date;
- claim class (engineering, bounded performance, independent perceptual, product/generalized);
- task, population, strata, comparator, build/config;
- evidence/result IDs and tier, independence, rights, analysis status;
- exclusions, limitations, uncertainty, known contradictions;
- owner, scientific/legal/product approvers;
- approval/expiry/review date;
- suspension/retraction triggers and replacement wording.

## Claim rules

- Engineering tests support engineering statements only.
- Dataset metrics name dataset/task/build and cannot imply perception.
- Internal/owner listening cannot support independent claims.
- “Professional,” generalized improvement, do-no-harm, genre leadership, and privacy absolutes require specifically applicable evidence and review.
- Unknown/inapplicable/error/skipped/expired/withdrawn evidence cannot support a claim.
- Material subgroup harm scopes or blocks under preregistration.
- Audio examples are claims and require rights plus representative labeling.

## Incidents and retraction

Security breach, deletion failure, rights withdrawal, license change, invalid analysis, data leakage, material regression, or dependency compromise triggers triage. The dependency graph identifies builds, studies, releases, and claims. Suspend affected access/claims, preserve permitted audit evidence, notify owners/participants as required, remediate, revalidate, and publish correction/retraction where applicable.

## Release gate

Threat model reviewed; critical findings closed/accepted; privacy flows and deletion tested; D-015 accepted; SBOM/licenses/notices/build provenance complete; signed update/rollback proven; claim registry clean; support/incident owner named; independent evidence only where claimed.
