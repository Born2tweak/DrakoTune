# DT-47 Completion Evidence — Metric Applicability Registry

**Evidence key:** `dt47_metric_card_suite`
**Milestone:** DT-47 (lane `evidence`, profile `automatic_internal`, resource_class `medium`)
**Generated:** 2026-07-21

## Acceptance criteria (Field 13) — status

| Criterion | Result | Evidence |
|---|---|---|
| Every current metric has a reviewed card | met | 36 cards cover all `CURRENT_METRICS`; `test_every_current_metric_has_a_card` |
| Inapplicable inputs never produce a quality pass | met | `test_inapplicable_input_never_supports_quality_pass`, `MetricCard.can_support_quality_verdict` |
| Thresholds cite evidence or a setting experiment (else unset) | met | `test_defect_and_perception_thresholds_are_unset`, `test_evidence_backed_value_requires_citation` |

## Honesty posture

- **33 of 36** metric thresholds are `unset_pending_listening_study` — no perceptual
  threshold is invented. Only **true_peak_dbtp** carries an evidence-backed ceiling
  (ITU-R BS.1770-4 / −1 dBTP delivery), a safety measure.
- Loudness/level metrics (`rms_dbfs`, `integrated_lufs`, …) are role `comparability`
  with `loudness_is_not_quality` / `louder_is_not_better` prohibited interpretations.
- Full-reference metrics (`si_sdr`, `segmental_snr`) are valid only with a clean,
  aligned reference and carry `not_perceptual_quality`.

## Adversarial matrix (Field 16)

| Case | Handling | Test |
|---|---|---|
| Missing reference | `MISSING_REQUIRED_REFERENCE` for full-reference metrics | `test_full_reference_metric_missing_reference` |
| Misalignment | documented `misalignment_biases_score` failure mode | same |
| Silence | `silent_reference_nan` / `silent_frames_excluded` failure modes | card `failure_modes` |
| Out-of-domain | `OUT_OF_DOMAIN` applicability | `test_out_of_domain_is_not_applicable` |
| Loudness-as-quality | comparability role, cannot support verdict | `test_loudness_metrics_cannot_be_quality` |
| Stale calibration | `UNKNOWN` applicability | `test_stale_calibration_yields_unknown` |

## Verification

- Full suite: **442 passed, 4 warnings** (DT-46 baseline 427 + 15 new DT-47 tests).
- Audio regression: **6/6 fixtures match goldens** — no DSP change.
- `test_committed_registry_matches_builder` guards drift between the generator
  (`scripts/build_metric_registry.py`) and the committed JSON.

## Deliverables (write_set: metric_registry, applicability_tests)

| Component | Path | sha256 (first 16) |
|---|---|---|
| Card schema | `src/evaluation/metric_registry/schema.py` | `4ef19d4e114a0cba` |
| Registry loader/enforcer | `src/evaluation/metric_registry/registry.py` | `e205ce11758a01c8` |
| Card generator | `scripts/build_metric_registry.py` | `655e55d02576f6a3` |
| Reviewed cards (36) | `AURELIAN/07_DATA_AND_PROVENANCE/metric_registry/metric_cards.json` | `0935fd12b9171104` |
| Applicability suite | `tests/test_metric_registry.py` | `79478b6b2e2eff17` |

## Claim impact (Field 21) / non-authorization (Field 22)

`narrows_objective_interpretation`. Objective claims are narrowed to a named
task/dataset/build with declared applicability; no PEAQ/ViSQOL/MOS-style overall
vocal-quality claim is authorized. No perceptual promotion.

## Handoff (Field 24)

DT-48 (Multiaxis Verdict Engine) is now unblocked (DT-46 + DT-47 complete) and
can implement valid verdict/trial semantics on registered metrics.
