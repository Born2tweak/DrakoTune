# D — Statistical Validity Report

**As of:** 2026-07-21  
**Sources:** S-E08–S-E11 and adversarial repository tests.

## Finding

The observation row is not the experimental unit. Judgments are crossed by listener and item and commonly clustered by singer, song, recording session, and source. The current row-level binomial test is invalid for repeated responses and permits a single listener to meet the former `n >= 8` rule.

## Required analysis shape

1. Preregister estimands by task: processed preference, defect absence/severity, equivalence/no-difference, or artifact risk.
2. Register immutable listener, trial, item, source, assignment, software, and experiment identities.
3. Model ties explicitly (for example, a Davidson-style extension) or use a prespecified ordinal/multinomial model.
4. Include listener and item random effects; add singer/song/session grouping where present. Estimate panel and treatment interactions rather than pooling cancellation.
5. Report effect estimates and compatible intervals, not binary p-value gates alone.
6. Use hierarchical bootstrap as a prespecified robustness analysis with the true cluster hierarchy.
7. Determine sample size by simulation from pilot variance/effect estimates and target precision/power.
8. Control endpoint families and disclose exclusions, attrition, missingness, device/environment, side/order balance, and model diagnostics.

## Invalidation

Duplicate key violations, assignment imbalance, identity ambiguity, correction without lineage, post-outcome protocol change, excess failed attention/reference checks, leakage across holdouts, or underpowered strata block confirmatory claims. Exploratory results remain visible but labeled.

## Method evidence audit

| Source/evidence | Contribution | Assumptions | Failure if misused | DrakoTune decision |
|---|---|---|---|---|
| S-E08, Baayen–Davidson–Bates (2008) | Demonstrates why subject and item variability should be modeled rather than collapsed. | Model structure matches the crossed data-generating process and has enough groups. | Row-level independence exaggerates precision and generalization. | Listener and item effects are mandatory; singer/work/session added where supported. |
| S-E09, simulation-based power for mixed models | Power can be estimated by simulating the intended model/design and plausible variance/effect structure. | Pilot assumptions and failure scenarios are credible. | A universal listener count hides item/cluster scarcity and effect uncertainty. | DT-59 estimates inputs; DT-60 freezes allocation/margins. |
| S-E10, hierarchical bootstrap | Provides cluster-aware uncertainty when resampling follows the actual hierarchy. | Resampling levels reflect independent sampling units. | Resampling rows recreates pseudoreplication. | Prespecified robustness analysis, not an automatic replacement for the primary model. |
| S-E11, Davidson tie extension | Pairwise comparison can model ties as information rather than discard them. | Tie mechanism/model fit is appropriate. | Removing ties changes the estimand and can manufacture apparent preference. | Tie-capable model or prespecified multinomial alternative. |
| Adversarial repository fixtures | Demonstrate duplicate, clean-rule, tie, panel, and side-bias false-pass paths. | Specific to legacy analyzer implementation. | Treating them as prevalence estimates. | They are mandatory regression fixtures for DT-56/57. |

## Model-selection rule

The canonical plan does not prematurely lock a single package or link function. The experiment preregistration must select the simplest model that represents its estimand and grouping, simulate its operating behavior, declare convergence/diagnostic failure handling, and preserve a cluster-aware robustness analysis.

## Executable analysis decision table

| Question | Experimental unit and outcome | Primary analysis candidate | Mandatory diagnostic | Prespecified fallback/limit |
|---|---|---|---|---|
| Is a named defect less perceptible/severe? | Independent item/source groups crossed with listeners; ordinal severity or defect-present response. | Ordinal or binary mixed-effects model with listener and item effects and treatment fixed effect. | Convergence, singularity, separation, residual/calibration behavior, per-cluster support. | Cluster-aware interval/bootstrapping or descriptive exploratory result; never row-level binomial inference. |
| Is processed preferred to control? | Listener–item paired choice with processed/control/tie. | Tie-capable paired-comparison model such as a preregistered Davidson extension. | Tie prevalence by panel/item, side/order balance, listener/item influence, fit and convergence. | Preregistered multinomial mixed model; do not discard or split ties post hoc. |
| Is clean-vocal harm acceptably small? | Listener–item impairment judgment plus safety endpoints; equivalence margin fixed before outcome access. | Mixed-effects equivalence/non-inferiority analysis appropriate to the registered scale. | Both interval bounds versus margin, floor/ceiling behavior, panel/item heterogeneity. | Inconclusive/abstain. Failure to reject a difference is not equivalence. |
| Do panels or target strata differ? | Independently sampled listener panels and rights-valid item strata. | Treatment-by-panel/stratum interaction with partial pooling where support permits. | Cell counts, interval width, influential clusters, multiplicity family. | Descriptive subgroup evidence only; no pooled cancellation or unsupported subgroup claim. |
| What sample is needed? | Counts of independent listeners, items, singers/songs/sessions—not response rows. | Simulation of the frozen candidate model across plausible effect, variance, tie, attrition, and imbalance scenarios. | Monte Carlo error and sensitivity to pessimistic assumptions. | Add pilot evidence or reduce claim scope; never substitute a universal `n`. |

## Analysis invariants

- The assignment manifest is created before outcomes and establishes side/order balance and planned missingness handling.
- All response corrections append lineage; no row is overwritten after collection.
- Confirmatory data access freezes the protocol hash. Changes create a versioned exploratory analysis or a new study.
- Multiplicity families are defined by claim, task, panel, subgroup, and endpoint before testing.
- Point estimates, compatible intervals, cluster counts, exclusions, attrition, model diagnostics, sensitivity results, and failures are reported together.
- A model that fails its registered diagnostics produces `inconclusive`, not an automatic switch to the most favorable analysis.

## Recheck triggers

Reopen this report when the protocol changes its outcome scale or cluster hierarchy, pilot data show severe separation/tie/attrition behavior, the selected statistical implementation changes, independent review finds model misspecification, or new primary methods evidence materially changes the preferred analysis.
