# K — Performance Report

**As of:** 2026-07-21  
**Repository evidence:** S-R06.

## Baseline

The historical performance report records approximately 0.07× realtime on its tested fixture, but memory scales near 180 MB per audio minute, reaching roughly 900 MB for five minutes; two historical MemoryErrors are recorded. Runtime speed is promising, yet the whole-buffer memory architecture is not a safe desktop-duration foundation.

## Unknowns

The evidence does not yet establish minimum-hardware behavior, startup/import cost, platform variance, stereo cost, peak temporary disk, cancellation latency, concurrent job behavior, thermal throttling, or stateful-processor chunk equivalence. Short synthetic fixtures underrepresent decoding and long-buffer behavior.

## Recommendation

First freeze an instrumented benchmark protocol and budgets. Then profile ownership/copies stage by stage. Prefer bounded whole-buffer support for the earliest internal vertical slice while designing overlap/state-aware chunking behind stable DSP interfaces. Every optimization must retain bit/metric goldens where exact equivalence is expected and listening review where it is not.

No public duration promise should precede demonstration on named minimum hardware with clean failure and recovery.

## Evidence audit and measurement gaps

| Evidence/dimension | Observed | What it supports | What it does not support | Required experiment |
|---|---|---|---|---|
| S-R06 historical benchmark | Approximately 0.07× realtime in its recorded scenario. | Core processing can be faster than realtime on that build/input/hardware context. | Startup, decode/encode, minimum hardware, platform parity, long-file stability. | Frozen end-to-end duration/rate/channel matrix. |
| S-R06 memory | Near-linear estimate around 180 MB per audio minute and about 900 MB at five minutes. | Whole-buffer memory is a material desktop risk. | Exact copy ownership or chunking savings. | Stage RSS/copy profiling plus low-RAM tests. |
| S-R06 failures | Two MemoryErrors recorded. | Failure is not hypothetical. | Current prevalence or cause on the final architecture. | Reproduce/classify through deterministic fault/stress harness. |
| Short representative audit run | Completed quickly and produced complete artifacts. | Current happy path is operational. | Useful-duration, cancellation, disk-full, crash, stateful-boundary, platform behavior. | DT-70/75 target-device and fault matrix. |
| Stateful processors | Filters/dynamics/gates/reverb/delay can carry history, latency, and tails. | Chunking needs explicit overlap/state semantics and audio validation. | Simple fixed chunks will remain equivalent. | Impulse/sine/noise/boundary goldens and expert review where non-exact. |

## Threshold-setting rule

DT-70 names the first platform and minimum hardware, measures representative user durations, and establishes budgets from product/user evidence. If whole-buffer processing cannot meet them, DT-75 implements and validates the narrowest chunk/state design necessary; the roadmap does not declare “fast” from the historical 0.07× result alone.

## Recheck triggers

Rebenchmark after dependency/native-build changes, DSP/backend changes, new channel/sample-rate/duration support, project-service buffering changes, first-platform selection, minimum-hardware revision, or any runtime/RSS/disk/cancellation regression.
