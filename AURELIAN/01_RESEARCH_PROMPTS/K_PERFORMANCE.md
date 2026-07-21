# K — Performance

**Decision:** set honest clip-duration and hardware targets and choose memory architecture.

Benchmark stage-level CPU, wall time, peak RSS, temporary disk, cancellation latency, startup, and output determinism across duration, sample rate, channels, and minimum hardware. Compare whole-buffer, memory-mapped, and overlap-aware chunked processing; identify stateful DSP boundary effects.

**Exclusions:** extrapolation from one short synthetic clip; performance changes that alter audio without golden/listening review.

**Deliverable:** reproducible benchmark matrix, budgets, bottleneck profile, streaming design, and fallback scope.

**Stop when:** maximum supported duration and memory are demonstrated on target minimum hardware with failure recovery.
