# DT-45 Completion Evidence — Evidence Semantics and Claim Quarantine

**Evidence key:** `dt45_semantic_suite`
**Milestone:** DT-45 (lane `evidence`, profile `automatic_internal`, resource_class `low`)
**Generated:** 2026-07-21
**Environment note:** Python 3.14.0 on Windows 11 (system interpreter). The
audited baseline in `PROJECT_STATE.md` was captured under Python 3.12
(360 passed, 2 skipped). Under 3.14 the two environment-gated tests execute and
pass, so the local baseline reads **362 passed** rather than 360 + 2 skipped.
This is an environment difference, not a behavior change; it is recorded here
rather than silently reconciled.

## Acceptance criteria (Field 13) — status

| Criterion | Result | Evidence |
|---|---|---|
| All legacy outputs map without silent pass | **met** | `test_no_silent_pass_property` (7-shape matrix), `map_legacy_evaluation` fails closed on unsafe/nonfinite/harm/conflict/absent-metric. |
| Nine canonical statuses serialize | **met** | `test_nine_canonical_statuses_exist_and_serialize` — exactly the nine spec values round-trip. |
| Quarantined claims cannot render as approved | **met** | `test_quarantined_claim_never_renders_approved`, `test_quarantine_downgrades_even_an_approved_status`, `ClaimQuarantineRegistry.assert_no_quarantined_approved`. |

## Automated verification (Field 14 / Field 16)

- Full suite: **412 passed, 4 warnings** (baseline 362 + 50 new DT-45 tests).
- DT-45 semantic suite: **50 passed** — see `dt45_semantic_suite.txt`.
- Audio regression: **6/6 fixtures match goldens** (no audio-runtime change, Field 17).
- Adversarial matrix covered: NaN / non-finite metric → `error`; absent metric →
  `not_applicable`; skipped/untargeted objective → `not_applicable`; conflicting
  pass+fail → `indeterminate`; target pass + collateral harm → `harmful_tradeoff`;
  output clipping → `unsafe`; unknown rights → engineering claim ineligible.

## Deliverables (write_set: evaluation_schema, claim_quarantine, compatibility_tests)

| Component | Path | sha256 (first 16) |
|---|---|---|
| Canonical enums | `src/evaluation/semantics/enums.py` | `022c90d2e47c3c71` |
| Validation error contract | `src/evaluation/semantics/errors.py` | `8a00849258467dda` |
| Canonical serialization + hashing | `src/evaluation/semantics/canonical.py` | `9eac2e47f09dd7e0` |
| Typed evidence records | `src/evaluation/semantics/records.py` | `e34223cfdc4e9934` |
| Claim quarantine registry | `src/evaluation/semantics/claims.py` | `fad731a37f06a46d` |
| Legacy mapping | `src/evaluation/semantics/legacy.py` | `f251c4f20c4c7156` |
| Package API | `src/evaluation/semantics/__init__.py` | `4a7f52d8046ea9e1` |
| Seeded claim inventory | `AURELIAN/07_DATA_AND_PROVENANCE/claim_inventory.json` | `318737d893987852` |
| Semantic suite | `tests/test_evidence_semantics.py` | `558b98cdd59fbdc5` |

(Hashes are of the working-tree files at evidence time; the merged commit is the
canonical pin.)

## Claim impact (Field 21)

`quarantine_only`. The seeded inventory renders exactly one claim as approved —
`claim_determinism_regression` (an audited engineering statement). Every
professional / generalized / do-no-harm claim is quarantined with an explicit
reason and cannot render as approved. Un-quarantining any of them is a
human-only `public_claims` gate and is **not** performed by DT-45.

## Explicit non-authorization (Field 22)

DT-45 authorizes no public claim, data use, recruitment, or processing change.
No DSP behavior changed. No report/manifest golden changed.

## Handoff (Field 24)

DT-46 (Identity and Provenance Schema v2) and DT-47 (Metric Applicability
Registry) become ready; DT-53 (Product Promise Discovery) research may begin.
Report/manifest verdict-surface integration is deferred to DT-48, whose Field 10
owns evaluation/report/manifest wiring.
