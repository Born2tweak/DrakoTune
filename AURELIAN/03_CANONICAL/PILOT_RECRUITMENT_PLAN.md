# Expert Pilot Recruitment & Budget Plan (DT-58, autonomous portion)

**Status:** autonomous groundwork complete; **no outreach, enrollment, spend,
contract, or consent approved** (Field 22). Pilot is explicitly **non-confirmatory**
(Field 21). Machine form: `src/pilot/`; dry-run: `dt58_evidence/dryrun_report.json`.
Depends on DT-55 (acquisition plan) + DT-57 (reviewed analysis).

## 1. Participants & roles

Target: 2–3 qualified **expert mixing engineers** (`Panel.EXPERT_ENGINEER`).
Screener (`src/pilot/criteria.py`): ≥ 3y target-genre mixing experience, calibrated
monitoring, passes an A/B audio-discrimination check. **Accessibility needs are an
accommodation requirement, never a disqualifier.**

## 2. Procedures (reuse frozen infrastructure)

- **Randomization + blinding:** counterbalanced processed-side + play order per
  trial×listener (`balanced_assignments`, DT-56 `Assignment`); responses live in A/B
  space (no treatment leak).
- **Session / response quality:** A/B trials + catch checks; forged/duplicate/ambiguous
  responses quarantined (DT-56 integrity).
- **Withdrawal:** a participant's responses are quarantined on withdrawal, never
  silently dropped; independent-listener count updates accordingly.
- **Analysis:** DT-57 clustered tie-aware model; a 2–3 person pilot yields a wide CI
  and is exploratory only.

## 3. Dry-run (mock data, end-to-end)

3 mock engineers × 12 trials → 36 responses; workflow OK; side-balanced; no
degenerate side bias; analysis converged, point ≈ 0.71, CI ≈ [0.64, 0.78] (wide, as
expected for n=3). Confirms the pipeline runs and that the pilot is **exploratory**,
feeding variance estimates to DT-60 (not a confirmatory claim).

## 4. Budget (formula only — no committed spend)

`src/pilot/costing.py` implements D-017's fair-rate formula (platform-recommended
base × professional premium) + platform fee + contingency. **Base rate and ceiling
are human inputs**; every budget flags `requires_human_authorization`. Illustrative
placeholder (NOT a quote): 3 × 2h @ $30 base × 1.5 premium → ~$378 total. Real
figures require owner + payment/counsel sign-off.

## 5. What is completed without contact or spend

Criteria, screener + qualification logic, randomization/blinding/session/withdrawal/
quality procedures, mock-data dry-run, and the fair-rate/budget formula. **All done.**

## 6. Human-only choices (→ consolidated packet)

Base compensation rate + total ceiling + contingency; recruitment channel + outreach
authorization; consent/contract language + payment handling (counsel); final go/no-go
(D-016). **None performed here.**
