# Prior Roadmap Review and Reconciliation

**Scope:** root roadmap/current-milestone history through M44.  
**Verdict:** substantial engineering value is retained; completion labels are not automatically evidence gates.

## Retained achievements

- Deterministic pipeline, v2 planner, DSP processors, safety/diagnostic modules.
- Test suite, audio goldens, synthetic corpus/calibration/benchmark machinery.
- Reports, manifests, processing records, data-governance foundations.
- Web pilot with job lifecycle, retention, signed links, rate/concurrency controls.
- Early listening UI/analyzer as exploratory tooling.

## Reclassified items

| Prior item | Historical label | Canonical interpretation |
|---|---|---|
| M24 listening | Tooling complete / ≥8 listeners pending | Exploratory tooling only; `n>=8` rule invalidated; replaced by DT-56–DT-62. |
| M29 artist consent | Draft/blocker | Still blocked on owner/legal approval; expanded at DT-49/DT-55. |
| M40 corpus-v2 | Completed | Valid regression asset; not representative quality evidence. |
| M42–M43 | Completed | Preserve code evidence; any quality implication remains gated. |
| M44 rate limiting | Code present/completed history | Retained control; production behavior still needs deployment verification. |
| Legacy default text | Current in one paragraph | Stale; v2 is executable default. |
| 362 tests | README shorthand | 362 collected at audit: 360 passed, 2 skipped. |

## Supersession rule

Prior roadmap documents remain historical evidence. They no longer define post-M44 sequencing, claim eligibility, listening sample adequacy, data rights, desktop distribution, or model adoption. Those subjects are governed by `AURELIAN/03_CANONICAL/` and `AURELIAN/05_ROADMAP/`.

## Migration posture

The new roadmap starts at DT-45 and maps legacy work into four states: preserve, harden, replace, or archive. No completed legacy milestone is rerun without a falsifiable gap. No future milestone may cite a historical “complete” label instead of executable acceptance evidence.
