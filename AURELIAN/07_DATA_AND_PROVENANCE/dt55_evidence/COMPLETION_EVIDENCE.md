# DT-55 Completion Evidence — Rights-Clean Acquisition and Consent Plan (autonomous portion)

**Date:** 2026-07-24 · **Depends on:** DT-49, DT-54 (complete). Nothing acquired.

## Autonomous deliverables (Field 15 *Automatic*)

| Deliverable | Location |
|---|---|
| Requirement → DT-54 launch-strata map + targets | `src/acquisition/requirements.py` |
| Rights-clean inventory + coverage-gap analysis (88-clip gap) | `src/acquisition/inventory.py`, `dt55_evidence/coverage_and_scenarios.json` |
| Rights / duplicate / leakage / ingestion validators | `src/acquisition/validators.py` |
| Source × purpose grant matrix | `src/acquisition/purpose_matrix.py` |
| Parameterized cost/time/storage scenarios (no spend) | `src/acquisition/costing.py` |
| Consent-withdrawal / grant-expiry simulation | `src/acquisition/withdrawal.py` |
| Canonical plan | `AURELIAN/03_CANONICAL/ACQUISITION_PLAN.md` |
| Tests (Field 14 + Field 16) | `tests/test_acquisition.py` — **13 passed** |

## Acceptance criteria (Field 13)

Every planned source/purpose has a grant path (matrix), quota (targets), cost model,
withdrawal/deletion simulation, attribution requirement, and a blocked fallback
(paid/counsel cells are gated, not auto-granted). ✅ — the *values* (budget, source
mix) are human-set.

## Boundaries (Field 22)

No spending, outreach, data acquisition, contract, training on acquired data, or
publication. Paid/marketplace/professional sources are flagged
`requires_human_authorization`; owner-audio publication needs counsel.

## Human-only choices (→ consolidated packet)

Budget ceiling + source mix; counsel consent/retention/withdrawal terms + license
grants; commissioning/outreach authorization; owner-audio public-example approval.
