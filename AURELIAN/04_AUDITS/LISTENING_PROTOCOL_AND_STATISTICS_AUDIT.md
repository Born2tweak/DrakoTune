# Listening Protocol and Statistics Audit

**Verdict:** prior tooling is exploratory only. Any future verdict produced under the former M24 rules is quarantined.

## Confirmed failure modes

| Exploit/check | Observed result | Invalid inference |
|---|---|---|
| One listener repeats one processed vote eight times | `n=8`, `p=0.0039`, pass | Independent listener support |
| Eight listeners prefer original on clean item | Processed rate 0.0, do-no-harm pass | Clean processing is harmless |
| All responses are ties | Defect omitted; clean passes; agreement 1.0 | Safe and highly reliable |
| Experts choose original; general panel chooses processed | Aggregate 50%; no interaction | No meaningful population difference |
| Processed always on side A; all select A | Can pass; no side diagnostic | Treatment effect rather than side bias |

## Additional findings

- CSV ingestion lacks robust duplicate/listener/trial validation and immutable correction lineage.
- Re-running append workflows can duplicate records.
- Device, monitoring, environment, expertise strata, side-specific artifacts, and order are not fully represented.
- Defect ties are discarded; clean “none” is effectively treated as not processed-preferred.
- Pairwise agreement is too weak to characterize reliability or bias.
- There is no preregistered estimand, model, exclusion plan, multiplicity family, power calculation, or independent analysis lock.
- The repository contains no actual independent response corpus to salvage; only tooling/informal owner evidence exists.

## Replacement protocol

Register protocol/version and immutable items before opening recruitment. Use unique participant identities protected from direct exposure, one response per participant/trial/version, balanced randomized assignments, concealed treatment, level/delay alignment, explicit tie/no-difference and side-specific artifact answers, environment/device checks, and panel qualification. Separate cleanup defect, clean equivalence/harm, and creative preference tasks.

Analyze listener/item crossed effects and singer/song/session clusters; estimate panel interactions. Report effect intervals, ties, raw independent counts, exclusions, missingness, order/side checks, and robustness analysis. Plan confirmatory sample size by simulation after a small paid pilot. Lock the analysis before unblinding treatment labels.

## Historical status

M24 completed useful tooling work but did not complete perceptual validation. The roadmap maps that work to legacy exploratory infrastructure and replaces its evidence gate at DT-56–DT-62.
