# Performance and Desktop Feasibility Audit

**Verdict:** computational speed appears adequate for a narrow internal slice, but memory, packaging, cancellation, and platform evidence are insufficient for a desktop promise.

## Existing evidence

The repository report at `reports/evaluations/perf/20260712-150853.md` estimates about 0.07× realtime for its test scenario. It also records linear memory near 180 MB per minute, roughly 900 MB for five minutes, and two MemoryErrors. The audit’s short representative render completed quickly, but that does not test long files or minimum hardware.

## Feasibility dimensions

| Dimension | Status | Gate |
|---|---|---|
| Core short-file runtime | Promising | Reproduce with fixed benchmark and target hardware. |
| Peak memory | Blocking | Stage-level RSS/copy profile; defined max duration; chunking proof. |
| Cancellation/recovery | Unknown | Bounded cancellation latency, atomic state, no false-complete artifact. |
| Cross-platform audio parity | Unknown | Golden/metric tolerances for controlled builds. |
| Startup/import/export | Unknown | End-to-end wall-time budget including decode/encode. |
| Disk/temp behavior | Unknown | Quotas, cleanup, crash recovery, permission safety. |
| Packaging size/update | Unknown | Reproducible installer and delta/full update measurements. |

## Architecture implication

Whole-buffer support can be temporarily bounded for internal testing. Production design should allow chunked analysis/rendering with overlap and explicit state transfer for filters, dynamics, gates, reverbs/delays, loudness analysis, and lookahead. Exact-equivalence processors use goldens; stateful changes require objective and listening review.

## Initial acceptance proposal

The owner must later set supported platform and minimum hardware. Demonstrate representative maximum-duration processing under a fixed peak-RSS budget, no swap-induced failure, responsive progress/cancel, deterministic output for the same build, and successful crash recovery before external desktop evaluation.
