# Evaluation and Statistical Analysis Plan

**Status:** canonical protocol framework v1.0  
**Important:** each confirmatory experiment instantiates and preregisters this framework before data collection/unblinding.

## 1. Evidence tiers

| Tier | Purpose | Eligible conclusion |
|---|---|---|
| T0 | Unit/property/safety checks | Implementation invariant only |
| T1 | Synthetic known-transform regression | Detector/processor behavior on named fixtures |
| T2 | Rights-clean held-out real data | Bounded objective performance on named population |
| T3 | Independent preregistered listening | Population/task-specific perceptual conclusion |
| T4 | Replicated external/temporal evidence | Time-bounded product claim within tested strata |

No tier substitutes for a higher tier. Every result states its tier.

## 2. Experimental units and identities

Required IDs: protocol, preregistration, experiment, software build, configuration, metric version, treatment, comparator, asset, work/song, singer/performer, source/dataset, recording session, take, item/stimulus, listener, panel, assignment, response, analysis run, result, rights/consent, and claim. Direct identity is kept separately from analysis pseudonyms.

Independent counts are reported for listeners, items, singers, works, sessions, sources, and every declared stratum. Response rows are never described as sample size without qualification.

## 3. Trial families

### Repair/defect

Primary estimand: treatment effect on prespecified defect judgment/severity among applicable items. Include tie/no-difference and side-specific artifacts. Known-reference objective metrics may support but not replace listening.

### Preserve/do-no-harm

Primary estimand: equivalence/non-inferiority on perceived impairment or a prespecified no-meaningful-difference outcome, plus artifact endpoints. “Processed was not preferred” cannot pass this family.

### Creative/style

Primary estimand: preference or similarity to declared intent/reference. Never pool with repair. A preference does not establish defect reduction or general quality.

### Usability

Primary estimands: task success, error/recovery, expectation comprehension, time, and calibrated trust; separate from audio preference.

## 4. Design requirements

- Freeze items, treatments, level/delay alignment, assignment generation, exclusions, endpoints, models, multiplicity families, and stopping before unblinding.
- Conceal treatment identity; randomize and counterbalance side/order within listener and item.
- Include task-appropriate references/anchors only where scientifically legitimate.
- Capture device, headphones/monitors, environment, browser/app/build, interruptions, expertise/panel, and qualification.
- One active response per `(protocol version, participant, trial)`; corrections append and supersede.
- Attention/reference checks are prespecified and cannot be outcome-dependent.
- Items are split/grouped before transformation to prevent singer/song/session/source leakage.

## 5. Statistical models

Primary pairwise outcomes use a prespecified mixed-effects binomial/multinomial/ordinal model appropriate to ties, with treatment fixed effect and listener/item random effects. Add singer/work/session/source effects when the design supports them. Panel and treatment interaction is estimated when populations differ.

For tie-bearing pairwise data, a Davidson-style model or prespecified multinomial mixed model is preferred over discarding ties. Continuous/ordinal defect ratings use appropriate cumulative/link models. Hierarchical bootstrap resampling the true cluster hierarchy is a robustness analysis. Model diagnostics, convergence, separation, sensitivity, and assumptions are reported.

## 6. Effect and decision reporting

Report estimate, compatible interval, raw outcomes including ties, independent-unit counts, absolute and relative effects where sensible, model diagnostics, exclusions/missingness, side/order balance, subgroup results, and robustness. Binary “pass” is derived only after this display.

Thresholds include a scientifically meaningful benefit/equivalence margin, hard safety/harm limits, confidence/interval requirement, multiplicity adjustment, and minimum independent coverage. Unknown, inapplicable, error, protocol deviation, or rights failure cannot pass.

## 7. Multiplicity and subgroups

Each experiment names primary endpoint(s), key secondary endpoints, exploratory endpoints, and correction family. Launch-critical strata are prespecified. Exploratory slices are labeled and do not retroactively narrow/expand the claim. A material protected/target subgroup harm blocks or scopes the claim under the preregistered rule.

## 8. Sample-size procedure

Do not use a universal `n`. Run a 2–3 engineer pilot with diverse representative items to estimate duration, attrition, ties, treatment effect, and listener/item/singer variance. Simulate the final model across candidate listener/item allocations. Select counts meeting target power/precision and minimum independent item/singer/session coverage under conservative assumptions. Freeze before confirmatory recruitment.

## 9. Missing, exclusions, and corrections

Reasons are enumerated. Technical failure, unavailable/inapplicable endpoint, withdrawal, failed qualification, incomplete trial, and analysis error are distinct. Exclusions are reported before/after counts. Withdrawal follows rights/deletion policy and invalidates dependent analyses/claims as needed. Corrections never mutate raw records.

## 10. Independence and analysis lock

Confirmatory treatment labels remain blinded through data cleaning and analysis-code verification. Prefer a reviewer/analyst who did not tune the tested treatment. Tuning data, pilot data, and confirmatory data are disjoint by grouped identities.

## 11. Result package

Package preregistration, protocol/UI/build, consent/rights versions, assignment seed/algorithm, item manifests/hashes, redacted raw data, exclusions, analysis code/environment, full outputs/diagnostics, deviations, decision, claim links, reviewer approvals, and correction history. Raw personal identity/audio is excluded unless specifically authorized.

## 12. Current quarantine

No result from the former row-binomial M24 analyzer is confirmatory. Any future imported legacy response is exploratory and must retain its legacy schema/method label.
