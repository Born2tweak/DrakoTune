# M — Continuous Research

**Decision:** design a reproducible watcher that proposes, but cannot self-authorize, roadmap changes.

Use official APIs/feeds for arXiv, Crossref, OpenAlex, GitHub releases/advisories, and selected standards/vendor pages. Define query versioning, pagination, rate/cost limits, deduplication, source snapshots, relevance scoring, license/applicability extraction, contradiction tracking, alert thresholds, human review, and replay tests.

**Exclusions:** brittle scraping, unattended adoption, unsourced summaries, or assuming a scheduled task runs indefinitely.

**Deliverable:** source registry, watcher state schema, deterministic scan fixture, proposal diff format, and operations runbook.

**Stop when:** identical inputs produce identical proposals and source/API failure cannot alter canonical state.
