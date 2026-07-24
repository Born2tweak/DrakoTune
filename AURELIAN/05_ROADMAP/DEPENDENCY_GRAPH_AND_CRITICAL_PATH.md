# Dependency Graph and Critical Path

**Authority:** validated derived topology view; YAML registry dependencies win on conflict.

## Critical path

The longest evidence-to-release chain is:

```mermaid
flowchart TD
    A["DT-45 evidence semantics"] --> B["DT-46 identities"]
    A --> C["DT-47 applicability"]
    B --> D["DT-48 verdicts"]
    C --> D
    B --> E["DT-56 listening schema"]
    D --> F["DT-57 statistical validation"]
    E --> F
    F --> G["DT-58–60 pilot and design lock"]
    G --> H["DT-61 platform"]
    B --> I["DT-49/55/62/63 data and rights"]
    I --> J["DT-64–67 independent evidence"]
    H --> J
    J --> K["DT-68 claim decision"]
    K --> L["DT-76 usability pilot"]
    L --> M["DT-77–80 champion decision"]
    M --> N["DT-86–90 beta and replication"]
    N --> O["DT-91 release gate"]
```

Desktop distribution joins the path through `DT-50 → DT-51 → DT-71 → DT-72–DT-75 → DT-76`. Rights-clean data joins through `DT-46 → DT-49 → DT-55 → DT-62 → DT-63`. The release cannot bypass either branch.

## Parallelizable research/build lanes

After DT-45, DT-46, DT-47, DT-50, and DT-53 can proceed in parallel when ownership permits. After stable identities, rights work (DT-49) and listening schema work (DT-56) can proceed independently. After DT-52/53, performance characterization (DT-70) can run while protocol/data gates mature. DT-83 can be implemented after DT-45/50 without waiting for model work, but DT-84 consumes the integrated system.

## Serial integrity constraints

- Analysis method is frozen before pilot; pilot precedes power/threshold lock; lock precedes confirmatory collection.

> **Dependency audit (2026-07-24, DT-57/55/58 groundwork).** The order is verified
> correct and needs no change: DT-57 (analysis method) → DT-58 → DT-59 (pilot) →
> DT-60 (power + threshold LOCK) → DT-66/DT-67 (confirmatory; both depend on DT-60).
> Freeze precedes confirmatory collection. **Explicit guard on the DT-59→DT-60
> boundary:** the pilot is non-confirmatory and its data may inform ONLY the
> confirmatory sample size `n` (via variance). Endpoints, direction, estimand, and
> exclusions are fixed in the DT-57 preregistration content-hash lock
> (`src/analysis/prereg.py`); thresholds (δ, α) are set at DT-60 BEFORE any
> confirmatory data. Pilot results must never redefine endpoints/thresholds
> (post-hoc guard, `test_post_hoc_endpoint_change_breaks_the_lock`). Corpus
> collection (DT-62) is likewise gated behind the DT-55 rights plan, and tuning
> (DT-64) never accesses confirmatory groups (grouped-split leakage control, DT-63).
- Acquisition/rights precede grouped splits; splits precede calibration/studies; tuning never accesses confirmatory groups.
- Distribution decision precedes framework/build; performance budget precedes long-file optimization; reliable workflow precedes usability pilot.
- Evidence/failure taxonomy precedes quality preregistration; implementation precedes frozen comparison; comparison precedes RC freeze.
- Beta RC freezes before execution; packaging/operations and beta precede replication; replication precedes public claims.

## Readiness rule

Only the canonical YAML registry can make a milestone ready/in progress. Dependency completion is necessary but not sufficient: applicable rights, resource, evidence, and true human-only gates must also be satisfied. This package begins with none in progress and DT-45 as the only ready milestone. After DT-45, up to four dependency-independent lanes may run under [the autonomy and parallel-execution policy](AUTONOMY_AND_PARALLEL_EXECUTION.md).
