# DT-48 Completion Evidence — Multiaxis Verdict Engine

**Evidence key:** `dt48_multiaxis_adversarial_suite`
**Milestone:** DT-48 (lane `evidence`, profile `automatic_internal`, resource_class `medium`)
**Generated:** 2026-07-21

## Acceptance criteria (Field 13) — status

| Criterion | Result | Evidence |
|---|---|---|
| Harsh fixture cannot receive an unqualified pass | met | `test_harsh_fixture_target_pass_with_harm_is_harmful_tradeoff` → `harmful_tradeoff` |
| Every status/reason stable | met | `test_verdict_is_deterministic_and_serializes` |
| Subgroup/harm/unknown block correctly | met | panel-interaction, collateral-harm, and unknown-rights tests |

## Reproduced listening exploits (Field 14) — all refused

| Negative result | Exploit | Engine response | Test |
|---|---|---|---|
| N-001 | target improves, collateral defect worsens | `harmful_tradeoff` | `test_all_targets_improve_but_hard_harm_still_blocks` |
| N-002 | 8 duplicate rows, 1 listener counted as n=8 | `indeterminate` (independence = listeners×items) | `test_n002_duplicate_rows_one_listener_not_independent` |
| N-003 | "processed not preferred" read as do-no-harm | `indeterminate` (needs prespecified equivalence) | `test_n003_clean_preserve_needs_prespecified_equivalence` |
| N-004 | unanimous ties dropped from evidence | `indeterminate` (rows unaccounted) | `test_n004_dropped_ties_are_detected` |
| N-005 | disagreeing panels pooled to 50% | `indeterminate` (panel interaction) | `test_n005_panel_disagreement_not_pooled` |
| N-006 | processed always on side A, all pick A | `indeterminate` (side bias) | `test_n006_side_bias_all_one_side` |

## Adversarial matrix (Field 16)

Duplicate rows · ties · panel cancellation (`cancelled`) · side bias · missing
metric (`not_applicable`) · rights expiry (all claims blocked) · all targets
improve but hard harm (`harmful_tradeoff`) — each has a dedicated test.

## Design

Ordered hard gates: signal safety → measurement error → listening cancellation
→ collateral harm → applicability → indeterminate → not-applicable → pass →
fail. Harm can never be averaged away behind target improvement. Perceptual
thresholds and harm budgets remain **unset** (DT-47); where a real conclusion
needs one, the engine abstains (`indeterminate`) rather than inventing a pass.
Claim eligibility ladders with the evidence tier: synthetic/unit evidence is
engineering-only; independent-perceptual requires a listening tier, a
structurally valid study, allowed rights, and no collateral harm.

## Verification

- Full suite: **460 passed, 4 warnings** (DT-47 baseline 442 + 18 new DT-48 tests).
- Audio regression: **6/6 fixtures match goldens** — no DSP change.

## Deliverables (write_set: verdict_engine, evaluation_reports, adversarial_tests)

| Component | Path | sha256 (first 16) |
|---|---|---|
| Bundle input types | `src/evaluation/verdict/bundle.py` | `e55d921600d9d21f` |
| Verdict rule engine | `src/evaluation/verdict/engine.py` | `daf3c7516888bd03` |
| Package API | `src/evaluation/verdict/__init__.py` | `8c564b492bf8c461` |
| Adversarial suite | `tests/test_verdict_engine.py` | `16a8801a813c23f7` |

## Claim impact (Field 21) / non-authorization (Field 22)

`blocks_false_passes`. Prevents unsupported pass language and enables future
bounded eligibility decisions. Does not certify the current engine or revive
prior M24 results.

## Handoff (Field 24)

DT-52 (Application/DSP Seam) and DT-57 (Statistical Preregistration) and later
study/result gates can build on stable verdict semantics. DT-52 remains blocked
pending DT-50 (build lane).
