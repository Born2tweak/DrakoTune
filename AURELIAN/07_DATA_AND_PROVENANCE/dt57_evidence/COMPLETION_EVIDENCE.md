# DT-57 Completion Evidence — Statistical Preregistration + Adversarial Validation (autonomous portion)

**Date:** 2026-07-24 · **Depends on:** DT-48, DT-56 (complete). Synthetic data only.
Supersedes the legacy M24 naive-binomial analyzer (`scripts/listening_analyze.py`).

## Autonomous deliverables (Field 15 *Automatic*)

| Deliverable | Location |
|---|---|
| Immutable preregistration schema + analysis lock (content hash) | `src/analysis/prereg.py` |
| Clustered, tie-aware model (listener cluster bootstrap; indeterminate, no naive fallback) | `src/analysis/model.py` |
| Seeded power / sample-size simulation harness | `src/analysis/power.py` |
| Design diagnostics (separation, single cluster, tie/artifact mass, dropout) | `src/analysis/diagnostics.py` |
| Calibration + adversarial test suite (16 tests) | `tests/test_analysis.py` |
| SAP candidate (human view) | `AURELIAN/03_CANONICAL/STATISTICAL_ANALYSIS_PLAN.md` |
| Machine prereg candidate (4 PENDING human choices; not freezable) | `dt57_evidence/prereg_candidate.json` |

## Acceptance criteria (Field 13) status

- **Known simulated effects recover; null within calibration:** strong effect power
  ≥ 0.80; null type-I ≤ 0.15 (one-sided 95% CI target ~0.025). ✅
- **Exploits cannot pass:** row-count (listener-clustered), ties (explicit mass),
  side/order (DT-56 blinded assignment), panel pooling (DT-56 breakdown),
  post-hoc endpoint (lock hash), selective exclusion (prespecified), early stopping
  (fixed-N). ✅
- **Failed convergence is indeterminate:** < 2 decisive clusters / all-ties →
  INDETERMINATE, never naive binomial. ✅

## Boundaries (Field 8/21/22)

- Out of scope: selecting final `n` without pilot variance (deferred to DT-60);
  analyzing real confirmatory data.
- Creates **method eligibility only** — no result, no claim, no chosen sample size.
- **Human-only gate:** independent statistical method review + threshold/alpha/margin
  sign-off. `freeze()` refuses to lock while any threshold is PENDING (4 unset).
