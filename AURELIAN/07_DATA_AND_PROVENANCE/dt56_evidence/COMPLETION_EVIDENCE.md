# DT-56 Completion Evidence — Listening Protocol and Immutable Response Schema

**Date:** 2026-07-23 · **Depends on:** DT-46, DT-47, DT-54 (all complete).
Supersedes the legacy **M24/M43** CSV listening records. Synthetic data only.

## What was completed autonomously (Field 15 *Automatic*)

| Deliverable | Location |
|---|---|
| Immutable, identity-safe protocol/trial/assignment/response schema | `src/listening/schema.py` |
| Integrity layer (uniqueness, resolution, panels, balance, corrections, import) | `src/listening/integrity.py` |
| Exploit + property test suite (16 tests) | `tests/test_listening_protocol.py` |

## The five audit exploits are rejected/surfaced structurally (Field 13)

| Exploit | Defense | Test |
|---|---|---|
| **N-002** one listener, eight rows = n=8 | `independent_listener_count` counts distinct listeners; `duplicate_rows` isolates the 7 extras | `test_duplicate_rows_do_not_inflate_sample` |
| **N-003** clean-vocal harm passes | `ResolvedPreference.PREFER_ORIGINAL` is an explicit category, never "not processed" | `test_original_preference_is_explicit_not_collapsed` |
| **N-004** ties disappear | `TIE_NO_DIFFERENCE` is a first-class outcome and counted | `test_ties_are_counted` |
| **N-005** panels pooled | `panel_breakdown` reports per panel; `panels_disagree` flags interaction | `test_panels_reported_separately_and_disagreement_flagged` |
| **N-006** side/order bias hidden | blinded `Assignment` holds side→treatment separately; responses live in A/B space; `side_choice_diagnostic` + `assignment_balance` surface degeneracy | `test_all_A_clicks_flagged_as_degenerate`, `test_preference_needs_assignment_no_treatment_leak` |

Plus: forged trial/listener IDs rejected (`validate_response`), append-only
corrections (`apply_correction` supersedes, never mutates), idempotent quarantined
legacy import (`import_legacy`), missing-assignment responses fail closed.

## Boundaries

- **Out of scope (Field 8):** statistical thresholds, recruitment, confirmatory
  execution — DT-57+. This is the schema + integrity layer only.
- **Human-only (Field 15):** consent/privacy terms and opening the protocol to real
  participants. No human-subject collection is authorized (Field 22).
- **Claim impact (Field 21):** removes the invalid legacy gate; **no** confirmatory
  eligibility before DT-60/DT-61. Legacy M24 data stays exploratory (quarantined).
