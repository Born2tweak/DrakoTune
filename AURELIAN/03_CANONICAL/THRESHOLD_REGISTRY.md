# Threshold Registry

**Status:** canonical planning registry v1.1  
**Rule:** unknown scientific or product thresholds are set by named experiments, never invented to make a milestone executable.

| ID | Threshold or decision boundary | Current state | Authority/evidence | Setter milestone | Use before set |
|---|---|---|---|---|---|
| TH-001 | Finite output and valid audio serialization | Hard invariant | Executable safety requirements/tests | DT-45/48 retain | Must pass; errors are unsafe. |
| TH-002 | Output peak/ceiling policy | Existing engineering policy; exact registered value comes from code/config | Current safety implementation and metric card | DT-47/48 | Engineering safety only; not quality. |
| TH-003 | Meaningful target-efficacy effect per defect | Unknown by real target population | Synthetic movement is insufficient | DT-59 pilot → DT-60 lock | No perceptual pass/claim. |
| TH-004 | Collateral-harm budget per metric/defect | Partly engineering, perceptual margin unknown | Harsh fixture demonstrates need, not final value | DT-47/59/60 | Hard known safety only; otherwise indeterminate/quarantined. |
| TH-005 | Clean-preservation equivalence/non-inferiority margin | Unknown | Requires expert pilot and construct-specific method | DT-59 → DT-60 | No do-no-harm claim. |
| TH-006 | Minimum independent listener/item/singer/session allocation | Unknown | Must follow variance, ties, attrition, target precision/power | DT-59 → DT-60 | No universal `n`; pilot is exploratory. |
| TH-007 | Side/order/attention/reference-check tolerance | Protocol-specific, unset | Assignment simulation and pilot behavior | DT-57/59/60 | Integrity failures remain visible and can invalidate. |
| TH-008 | Launch-critical genre/recording coverage | Unknown pending product discovery | Target job and strata taxonomy | DT-53/54, frozen at DT-60/85 | Claims name only observed strata; no generalization. |
| TH-009 | Maximum supported clip duration | Unknown | Named target users, platform, hardware, RSS/disk/cancel curves | DT-70 | UI/CLI must state existing tested limits only. |
| TH-010 | Minimum supported hardware and platform | Unknown owner/product decision | Target user evidence and performance matrix | DT-70 | No desktop performance/platform promise. |
| TH-011 | Runtime, peak RSS, disk, startup, and cancel budgets | Unknown | Reproducible target-device measurements | DT-70, enforced DT-75 | Historical 0.07× is descriptive only. |
| TH-012 | Challenger material-benefit and non-harm boundary | Unknown per candidate/task | Frozen champion and applicable evidence | DT-78 preregistration | Candidate cannot promote. |
| TH-013 | Model/sandbox CPU/GPU/RAM/disk quota | Operationally configurable | Local capacity and approved experiment budget | DT-82 | Fail closed at configured safe local quota. |
| TH-014 | Research-source request/cost/rate ceiling | Source-specific and time-varying | Official API terms/current account authority | DT-83 source config | No unbounded retry or paid use. |
| TH-015 | Risk escalation score | Defined as ≥15 in current risk register | Control-plane risk policy | Replanning can revise prospectively | Blocks affected public/distribution work unless accepted. |
| TH-016 | Maximum parallel execution lanes | Four by policy, dynamically lower under resources/conflicts | Autonomy policy v1.1 | Roadmap replan | Scheduler may reduce automatically, not exceed without policy change. |
| TH-017 | Compensation and total study budget | Unknown | Current platform rules, professional rate, task duration, owner authority | DT-58 | $0 external financial authority. |
| TH-018 | Claim expiry/retest interval | Claim-specific, unset until evidence | Evidence stability, build, population, rights, release policy | DT-68/90/91 | Candidate claim must have an expiry before approval. |

## Threshold lifecycle

`unknown → proposed → pilot-estimated → preregistered/frozen → evaluated → retained/revised prospectively → superseded`.

Every threshold record stores units, direction, task/population/slices, metric version, estimation method, uncertainty, failure rule, effective build/protocol, approver when human-only, and recheck trigger. A post-outcome revision cannot change the verdict of the completed experiment; it creates a new future protocol.
