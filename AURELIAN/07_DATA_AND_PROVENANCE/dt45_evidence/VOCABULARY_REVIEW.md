# DT-45 Semantic Vocabulary Review

**Review type:** automatic evidence-producing review (per
`AURELIAN/00_CONTROL/AUTONOMY_POLICY.md` — "semantic vocabulary, compatibility,
and internal claim-inventory checks" are Field 15 **Automatic**, not a human
gate). No public claim wording or product-scope decision occurs in DT-45, so no
human-only gate is triggered.

## Vocabulary conformance

Every canonical enum in `src/evaluation/semantics/enums.py` matches
`AURELIAN/03_CANONICAL/IMPLEMENTATION_SCHEMA_EXAMPLES.md` ("Canonical enums")
value-for-value:

| Enum | Count | Conforms |
|---|---|---|
| Result/verdict status | 9 | yes |
| Applicability | 6 | yes |
| Measurement status | 6 | yes |
| Evidence tier | 5 | yes |
| Rights permission | 6 | yes |
| Grant status | 6 | yes |
| Claim class | 4 | yes |
| Claim status | 7 | yes |
| Experiment status | 8 | yes |
| Milestone status | 7 | yes |
| Human-gate category | 16 | yes |

Distinctness invariant verified: `unknown`, `not_applicable`, `error`, and
`indeterminate` are four distinct values and are never coerced into one another
(`test_distinct_missing_states`). Unknown enum values raise a schema error and
are never aliased (`test_unknown_enum_is_rejected_not_aliased`).

## Internal claim-inventory check

The seeded inventory (`claim_inventory.json`) was reconciled against the
`PROJECT_STATE.md` evidence table:

| Evidence-table area | Inventory claim | Rendered status |
|---|---|---|
| Determinism / software regression (supported locally) | `claim_determinism_regression` | **approved_internal** (only approved claim) |
| Signal safety (partial) | `claim_signal_safety_complete` | quarantined |
| Defect reduction (synthetic/metric only) | `claim_defect_reduction_generalized` | quarantined |
| Professional quality (unsupported) | `claim_professional_quality` | quarantined |
| Genre robustness (unsupported) | `claim_genre_robustness` | quarantined |
| Clean-vocal do-no-harm (unsupported) | `claim_clean_vocal_do_no_harm` | quarantined |
| Public hosted pilot (unverified in audit) | `claim_public_hosted_pilot_live` | quarantined |

This matches DT-45 Field 21: unsupported professional/generalized/do-no-harm
language is suspended; only audited engineering statements are permitted.

## Reviewer

Autonomous evidence review under the accepted Aurelian v1.2 autonomy policy.
Recorded as `signed vocabulary review` for Field 23 completion evidence.
