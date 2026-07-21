# B — Code and Architecture

**Decision:** identify reliable seams and unsafe coupling before implementation.

Trace CLI/web entry points through preprocessing, diagnostics, decision planning, DSP execution, evaluation, reporting, persistence, and export. Verify behavior with tests and fixtures. Map identities, failure states, configuration, side effects, memory ownership, and license-bearing dependencies. Distinguish executable truth from stale documentation.

**Exclusions:** refactoring during audit; aesthetic code review without product/evidence relevance.

**Deliverable:** current component map, contracts, drift list, preservation/replacement decisions, and minimal strangler seams.

**Stop when:** every user-visible flow and evidence-producing boundary has a verified owner and test reference.
