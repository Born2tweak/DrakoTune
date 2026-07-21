# Test and Evaluation Validity Audit

**Verdict:** software regression evidence is strong for the current prototype; product-quality validity is weak and can be falsely positive.

## Baseline evidence

- Fresh environment: 362 collected, 360 passed, 2 skipped, 5 warnings.
- Audio regression: six fixtures exactly match stored goldens.
- Representative v2 render completed with trace/report/manifest.
- `pip check` reports no broken requirements.

These results support “the audited implementation behaves consistently in this environment.” They do not support “the output is professionally better.”

## Construct-validity failure

The harsh fixture met two target-movement objectives while collateral indicators worsened: sibilant-frame p95 +0.0074, mud ratio +5.2135, and loudness -1.2 LU, with residual harshness/noise. The result shape allowed “passed” to dominate these contrary observations.

## Corpus limitations

Current corpus-v2 contains 80 clean and 160 synthetically degraded clips. Cells are small (commonly four), six pairs error, and SI-SDR outcomes are mixed/negative in places. Calibration records substantial false positives (including reverb 41.2%, hum 21.2%, noise 22.5%). It is excellent for deterministic engineering regression and intentionally injected defects, but it does not estimate natural prevalence, professional preference, or target-genre robustness.

## Required outcome model

Every evaluation emits:

- task and metric applicability;
- baseline/comparator/treatment identity;
- target effect plus uncertainty;
- collateral-harm vector and hard safety checks;
- slice and independent-unit counts;
- missing/error state distinct from fail;
- prespecified decision rule and multiplicity family;
- evidence/claim eligibility and reasons;
- exact code/config/data provenance.

## Gate redesign

Use four levels: unit/property safety; deterministic synthetic regression; rights-clean held-out real-data evaluation; independent preregistered listening. A higher layer cannot repair a missing lower-layer safety result, and a lower layer cannot stand in for a higher-layer perceptual claim.

## Test gaps

Add adversarial semantic tests, corrupted/unsupported input tests, group-split leakage tests, cross-platform/build fingerprints, long-duration memory/cancellation tests, and mutation/property tests for safety invariants. Record skipped tests as unavailable evidence, not pass.
