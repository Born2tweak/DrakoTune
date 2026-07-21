# DT-45 Legacy Migration Report

**Scope:** how legacy `EvaluationResult` records map to the typed
`EvidenceResult` model without a silent pass. The legacy type is **not**
mutated (read compatibility, Field 19); a forward mapper reads it.

## Mapping rules

| Legacy signal | Typed axis / status |
|---|---|
| `output_clipping` warning | `signal_safety = unsafe` → overall `unsafe` |
| non-finite metric value (NaN/±Inf) in before/after | `error` measurement → overall `error` |
| `passed_checks` and `failed_checks` both non-empty | `target_efficacy = indeterminate` → overall `indeterminate` |
| `passed_checks` only, no harm | `target_efficacy = passed` → overall `passed` |
| `harshness_increased` / `residual_after_processing:*` warning | `collateral_harm = failed` |
| target passed **and** collateral harm | overall `harmful_tradeoff` (not pass) |
| `failed_checks` only | overall `failed` |
| no targeted objective metric present | `target_efficacy = not_applicable` → overall `not_applicable` |
| no before/after metrics at all | `applicability = invalid_input` |

## Fail-closed defaults

- `rights_known` defaults **False**: a mapped legacy result is engineering-eligible
  only on a clean pass *with* known rights. Unknown rights → no eligible claim.
- Evidence tier defaults to `T1_synthetic_regression`, which caps eligibility at
  the `engineering` class. Higher classes are always ineligible for mapped
  legacy results.
- Every mapped result is run through `EvidenceResult.validate()` before return;
  a structurally impossible pass (e.g. passed with a failed axis) raises rather
  than emitting.

## No-silent-pass guarantee

`test_no_silent_pass_property` asserts that a mapped result carries `passed` only
when it is simultaneously applicable, non-`unsafe` on safety, non-`failed` on
collateral harm, and `passed` on target efficacy. Every other legacy shape maps
to a named non-pass status and grants no eligible claim.

## Not migrated here (by design)

- Report/manifest emission is unchanged; DT-48 owns verdict-surface wiring.
- Rights enforcement is vocabulary-only in DT-45; DT-49 builds the graph.
