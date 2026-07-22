# DT-53 Discovery Protocol & Promise Framework (autonomous prep)

**Status:** autonomous framework complete; **participant contact and the final
product-scope decision remain human-only gates.** · **Generated:** 2026-07-21

This is the reusable framework the DT-53 contract's Field 15 marks *Automatic*:
a discovery protocol, a job map, falsifiable promise alternatives, and validators
— all provable on synthetic records. A human drops real *consented* interview
records into the same `ResearchNote` shape and gets the same checks. Nothing here
contacts a participant, and no promise is selected.

## 1. Approved discovery protocol (ready to run once participants are approved)

- **Recruitment (HUMAN GATE):** owner approves who is contacted and how. No
  outreach happens autonomously.
- **Session:** 30–45 min, approved interview + workflow observation of the user
  cleaning up one of their own vocal takes.
- **Consent & privacy (enforced in code):** explicit recording consent recorded
  as `consent_state`; pseudonym only (no direct identity); `retention_until`
  deadline; a `deletion_path` must exist. Records failing any of these are
  **excluded from synthesis** (`usable_notes`).
- **Contradictions retained:** dissent is recorded as a `contradicts` edge and
  surfaced by `audit_contradictions`; a confirmation-biased synthesis cannot
  hide it.

## 2. Job map (candidate; to be confirmed by evidence)

| Step | Description | Hypothesized current pain |
|---|---|---|
| J1 | Get a rough vocal take out of the DAW | export friction |
| J2 | Tame harsh sibilance / plosives | manual de-ess is fiddly |
| J3 | Even out level / presence | inconsistent loudness |
| J4 | Decide if it's "good enough" to share | no reference / uncertainty |
| J5 | Keep the original safe | fear of destructive edits |

## 3. Falsifiable promise alternatives (the human chooses at most one)

Each alternative is admissible only because it carries falsifiers. Choosing among
them is the `product_scope` human gate.

| ID | Promise | In scope | Out of scope | Falsifiers |
|---|---|---|---|---|
| PR-A | Automatically clean a **single dry** rap/pop vocal | single_dry_vocal | full_mix, accompaniment | `accompaniment_required`, `misread_automatic` |
| PR-B | **Assist** an artist with guided cleanup (manual control retained) | guided_controls | fully_automatic_promise | `wants_fully_automatic`, `too_slow_to_be_worth_it` |
| PR-C | Provide an **honest second opinion** (diagnose, don't process) | diagnosis_only | audible_processing_claim | `wants_processing_not_advice` |

## 4. Contradiction watch (the engineer↔creator tension)

The clearest anticipated contradiction: an **engineer** persona wants manual
control (`wants_manual_control`); a **creator** persona wants it automatic
(`wants_automatic`). The framework retains both as a contradiction rather than
averaging them, so a promise cannot silently claim to satisfy both.

## 5. What the code enforces (Field 14)

- `validate_note` / `usable_notes` — completeness + consent + retention, fail-closed.
- `audit_contradictions` — retains and surfaces dissent.
- `check_promise_falsifiers` — a promise with any observed falsifier resolves to
  `FALSIFIED`; with only support → `SUPPORTED`; with neither → `INSUFFICIENT`
  (retain the narrow current spec).

Implementation: `src/product_discovery/`; tests: `tests/test_product_discovery.py`
(16 passed). Evidence: `AURELIAN/07_DATA_AND_PROVENANCE/dt53_evidence/`.

## 6. Human gates that remain (do NOT proceed autonomously)

1. **Participant contact / recruitment** — who is interviewed.
2. **The product-promise / scope decision** — which of PR-A/B/C (or none), and
   the launch boundary (cleanup vs. style; single-vocal vs. context; who it's for).

Until (2) is decided, the roadmap keeps the narrow current spec (Field 19).
