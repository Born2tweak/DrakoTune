# DT-58 Completion Evidence — Expert Pilot Budget/Contracts/Recruitment (autonomous portion)

**Date:** 2026-07-24 · **Depends on:** DT-55, DT-57 (autonomous portions complete).
No outreach, enrollment, or spend. Pilot is non-confirmatory (Field 21).

## Autonomous deliverables (Field 15 *Automatic*)

| Deliverable | Location |
|---|---|
| Participant criteria + screener + qualification (accessibility = accommodation) | `src/pilot/criteria.py` |
| Fair-rate + budget formula (always needs authorization; never sets base rate) | `src/pilot/costing.py` |
| End-to-end dry-run (screen→blind→respond→DT-57 analysis) on mock data | `src/pilot/dryrun.py`, `dt58_evidence/dryrun_report.json` |
| Canonical plan | `AURELIAN/03_CANONICAL/PILOT_RECRUITMENT_PLAN.md` |
| Tests (Field 14 + Field 16) | `tests/test_pilot_groundwork.py` — **10 passed** |

## Acceptance criteria (Field 13)

2–3 target-qualified slots defined; fair-rate formula; full cost model with fee +
contingency; screener/qualification + withdrawal/quality procedures; exploratory
(non-confirmatory) framing. ✅ — rate/ceiling/consent VALUES are human-set.

## Dry-run result (mock)

3 mock engineers × 12 trials → 36 responses; workflow OK; balanced; converged, wide
CI (exploratory). Demonstrates the full listening workflow runs and that n=3 is
underpowered — feeding pilot variance to DT-60.

## Boundaries (Field 22)

No contacting, enrollment, spending, contract, or consent. Approval scope is pilot
only, not confirmatory/training/publication/claim.

## Human-only choices (→ consolidated packet)

Base rate + ceiling + contingency; recruitment channel + outreach; consent/contract
+ payment handling (counsel); go/no-go (D-016/D-017).
