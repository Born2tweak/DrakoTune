# M — Continuous Research Report

**As of:** 2026-07-21  
**Sources:** S-W01–S-W04.

## Source strategy

Use official arXiv, Crossref, OpenAlex, and GitHub APIs/feeds rather than search-page scraping. Store query version, cursor/page state, response identity/hash, retrieval time, source terms/cost posture, and parsed records. OpenAlex’s 2026 authentication/credit model demonstrates why source health and cost are versioned evidence.

## Processing stages

Fetch → validate schema/source → normalize identifiers → deduplicate → classify domain → extract claimed contribution → screen license/weights/data/applicability → link contradictions → score review priority → emit a proposed evidence/roadmap diff. Failures generate health findings, never empty “no change” conclusions.

## Governance

The watcher may flag new papers, releases, advisories, retractions, license changes, benchmark changes, and source failures. It may automatically append validated metadata/evidence, update source health, and advance low-risk maintenance/readiness state inside the accepted policy. It cannot install/adopt a production dependency or model, change product scope or public claims, spend, recruit, reinterpret rights, distribute, or change production without the applicable human-only gate.

## Initial implementation

Begin with a manual deterministic scan and frozen API fixtures. Add scheduled execution only after replay, pagination, rate-limit, deduplication, and failure-mode tests pass and an operations owner/cadence is named.

## Source/API evidence audit

| Source | Official capability | Material operational constraint | Watcher behavior | Recheck trigger |
|---|---|---|---|---|
| S-W01 arXiv API | Official query interface for arXiv metadata/records. | Query syntax, pagination, rate guidance, versions/corrections, and API terms must be honored. | Store query/cursor/raw response hash; dedupe by stable identifiers/version; bounded retries. | Source terms/schema/API change. |
| S-W02 Crossref REST | Official scholarly metadata API. | Metadata completeness varies; abstracts/full text may have separate rights and publisher sources remain authoritative. | Use DOI/version/update metadata; never infer paper validity or adoption from presence. | API/schema/terms change. |
| S-W03 OpenAlex | Broad scholarly graph API; current authentication/credit model is documented. | 2026 freemium/daily-credit posture shows cost/auth assumptions can change. | Version cost/auth health; fail closed on exhaustion/change; no silent partial “no news.” | Every run plus policy notice. |
| S-W04 GitHub APIs | Official release, repository, and advisory metadata. | Archived repositories, moved tags, API pagination/rate/auth, and license-file changes need distinct events. | Pin repository identity; hash release/license/advisory records; dedupe/update events. | Release/advisory/license/repository state. |
| ITU/EBU/dataset/vendor pages | Primary standard, dataset-card, and license/terms evidence. | Some lack structured feeds and may change without semantic versioning. | Approved low-frequency content-hash checks; store minimal permitted snapshots/metadata. | Hash/date/terms/version change. |

## Candidate priority model

Priority is a review queue, not an adoption score. It combines task relevance, evidence independence, reproducibility, rights clarity, target-data coverage, resource feasibility, contradiction severity, and security urgency. Missing rights or applicability cannot be compensated by novelty or citation count.

## Failure semantics

Authentication, cost, terms, schema, pagination, partial-page, rate-limit, and parse failures are distinct health events. A partial scan cannot conclude “no relevant change.” Notifications are deduplicated and audited; safe shutdown checkpoints the current page and releases its lease without committing a partial canonical change.
