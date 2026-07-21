# DT-52 Completion Evidence — Application and DSP Seam Characterization

**Evidence key:** `dt52_behavior_parity`
**Milestone:** DT-52 (lane `build`, profile `automatic_internal`, resource_class `medium`)
**Generated:** 2026-07-21

## Acceptance criteria (Field 13) — status

| Criterion | Result | Evidence |
|---|---|---|
| Baseline tests/goldens unchanged | met | full suite 478 passed; 6/6 audio goldens match |
| Representative render semantically equivalent | met | `test_render_array_is_bit_identical_to_engine`, `test_render_file_matches_render_plan` (bit-identical) |
| No UI adapter imports backend internals | met | `test_application_layer_does_not_import_pedalboard_at_top_level` (AST scan) + dependency-inversion test with a fake backend |

## Design

A typed application seam wraps the existing v2 pipeline without changing sound:

- `Analyze / Render / Evaluate` commands + typed results carrying a canonical
  `ResultStatus` and a `BuildIdentity` (backend name, **license**, engine version).
- `DspBackend` Protocol: capabilities (supported processors + safe ranges),
  stateful flag, latency, license identity. `PedalboardBackend` adapter declares
  `license_id = "GPL-3.0-only"` — the GPL obligation is explicit at the seam, not
  hidden (DT-50 captured it; DT-51 is the human distribution decision).
- The service depends only on the abstract backend; the AST test proves no
  application module imports `pedalboard`.

## Adversarial matrix (Field 16)

| Case | Handling | Test |
|---|---|---|
| Unsupported processor/parameter | `supports()` rejects; `validate_plan` flags | `test_unsupported_processor_and_param_rejected` |
| Backend unavailable | typed `error`, no crash | `test_backend_unavailable_is_typed_error_not_crash` |
| Cancellation | `cancelled` status, no output written | `test_cancellation_before_render_writes_no_output` |
| Partial/failed output | typed `error`, no partial file | render error path |
| Mismatched build | `error` with `build_mismatch` reason | `test_build_mismatch_blocks_render` |

## Verification

- Full suite: **478 passed, 4 warnings** (DT-50 baseline 466 + 12 new DT-52 tests).
- Audio regression: **6/6 fixtures bit-identical to goldens** — no DSP change.

## Deliverables (write_set: application_interfaces, dsp_backend, characterization_tests)

| Component | Path | sha256 (first 16) |
|---|---|---|
| Backend contract + adapter | `src/application/backend.py` | `aebfcb49cdb75822` |
| Typed commands/results | `src/application/commands.py` | `737e9c89abee1208` |
| Application service | `src/application/service.py` | `8c5fcdfe78f966b8` |
| Package API | `src/application/__init__.py` | `45a5da3c1b80b877` |
| Characterization suite | `tests/test_application_seam.py` | `a5dc43c06a0f5a45` |

## Claim impact (Field 21) / non-authorization (Field 22)

`preserves_baseline_only`. No quality claim. Does not select a replacement DSP,
alter sound, or authorize desktop packaging.

## Handoff (Field 24)

DT-64, DT-69, DT-70, and DT-79 can build on the stable seam. Those milestones
additionally depend on human-gated work (DT-49 rights, DT-53 product scope) and
later research milestones, so no further `automatic_internal` H0 milestone is
ready — the roadmap has reached its first human-only gate boundary.
