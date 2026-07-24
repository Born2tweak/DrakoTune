# Statistical Analysis Plan — Preregistration CANDIDATE (DT-57)

**Status:** candidate v1.0.0 — analysis *method* implemented + validated
autonomously. **NOT frozen:** every threshold/alpha/margin/sample-size is a
`__PENDING_HUMAN_SIGNOFF__` field; independent method approval + threshold sign-off
are the only remaining gates (Field 15). Selecting final `n` is deferred to pilot
variance (Field 8; DT-60). Machine form: `src/analysis/prereg.py`; candidate
instance: `07_DATA_AND_PROVENANCE/dt57_evidence/prereg_candidate.json`. Supersedes
the legacy M24 naive-binomial analyzer (`scripts/listening_analyze.py`).

> This document does not authorize recruitment, unblinding, endpoint selection
> after outcomes, or any claim (Field 22). It creates *method eligibility only*.

## 1. Population (supported input + launch strata)

Dry single lead rap/pop vocal per the accepted DT-54 launch-critical strata
(D-028): genre rap/melodic_rap/pop; presentation spoken_rapped/melodic; language
english; recording home_untreated/plosive_prone/sibilant_prone. Analyses are
reported **within** stratum; no genre-generalization claim (DT-54 Field 21).

## 2. Estimand

The **listener-mean processed-preference proportion among decisive responses**,
estimated at the **listener** unit (not the response row — N-002), within a
stratum × study arm. Ties, artifacts, and cannot-tell are separate reported masses
(N-003/N-004), never coerced into a preference.

## 3. Hypotheses (H0 / H1) and endpoints

Endpoints are tagged **OBJECTIVE** (measured DSP metric, no listeners) or
**PERCEPTUAL** (listener judgement); they are never averaged together.

| Endpoint | Kind | Direction | H0 | H1 |
|---|---|---|---|---|
| Repair efficacy (DT-67) | PERCEPTUAL | superiority | processed-preference ≤ 0.5 + δ_sup | > 0.5 + δ_sup |
| Do-no-harm on clean input (DT-66) | PERCEPTUAL | non-inferiority | processed-preference < 0.5 − δ_ni (harm) | ≥ 0.5 − δ_ni |
| Output safety (peak/clip/true-peak) | OBJECTIVE | threshold | metric outside safe bound | within bound |
| Fidelity preservation (SI-SDR/seg-SNR) | OBJECTIVE | threshold | below preservation floor | at/above floor |

δ_sup (superiority margin), δ_ni (non-inferiority margin), and each α are
**PENDING human sign-off** (§9). Objective endpoints need no listeners and are
evaluated by the existing DSP metrics (`src/diagnostics/`, `src/evaluation/`).

## 4. Exclusion, abstention, invalid-response rules (prespecified)

- **Listener exclusion:** failed catch/attention trials (rate PENDING) → excluded,
  prespecified so exclusion cannot be chosen after seeing outcomes.
- **Invalid responses:** forged/duplicate/ambiguous → quarantined by DT-56
  (`import_legacy`, `active_responses`), never counted, never silently dropped.
- **Abstention:** cannot-tell is a first-class mass; the model abstains
  (INDETERMINATE) rather than guessing on degenerate designs (§7).

## 5. Multiplicity, missing data, stopping

- **Multiplicity:** Holm across primary endpoints (family-wise control); secondary
  endpoints reported as exploratory.
- **Missing data:** dropout reported per arm/stratum; **sensitivity** = complete-case
  vs worst-case imputation (§8); dropout correlated with outcome is a diagnostic flag.
- **Stopping rule:** **fixed-N, no interim analyses** → structurally prevents early
  stopping / optional-stopping inflation. Any interim look would change the plan
  hash and void the lock.

## 6. Minimum-effect thresholds & sample size (PENDING + computed)

- δ_sup, δ_ni, α, target power: **PENDING human sign-off**.
- **Final n:** deferred to pilot variance (DT-59 → DT-60). It is *computed*, not
  guessed: `src/analysis/power.py` Monte-Carlo estimates power(n | δ, α, ICC via
  Beta κ, tie/artifact rate) and `power_curve` yields n→power; the owner picks the
  operating point after pilot variance is known.

## 7. Analysis model (clustered, tie-aware, no naive fallback)

`src/analysis/model.py`: per-listener decisive proportions → **cluster bootstrap
over listeners** for the CI (respects clustering, N-002). Degenerate designs
(< 2 decisive clusters, all-ties, single cluster) return **INDETERMINATE** — never
a naive binomial (Field 19). Decisions apply only a **human-supplied** threshold
(`evaluate`), never an invented one.

## 8. Sensitivity analyses

Complete-case vs worst-case dropout imputation; ICC/κ robustness (power under
higher between-listener heterogeneity); tie-rate robustness; leave-one-panel-out.
All run on synthetic data now; frozen for confirmatory use later.

## 9. Protections against post-hoc substitution / p-hacking / selective exclusion / early stopping

| Threat | Structural protection | Test |
|---|---|---|
| Post-hoc metric substitution | plan is a frozen hash; endpoint swap breaks the lock | `test_post_hoc_endpoint_change_breaks_the_lock` |
| p-hacking via threshold choice | thresholds are `PENDING`; `freeze()` refuses to lock unset values; `evaluate` never invents a threshold | `test_freeze_refuses_while_thresholds_pending`, `test_evaluate_uses_supplied_threshold_only` |
| Selective exclusion | exclusions prespecified in the frozen plan | §4; lock hash |
| Early stopping | fixed-N, no interim; interim look changes the hash | §5 |
| Row-count inflation | listener-clustered estimand | `test_one_listener_many_rows_is_one_cluster` |
| Spurious pass on degenerate data | INDETERMINATE, no fallback | `test_all_ties_is_indeterminate_no_naive_fallback` |

## 10. Immutable schema + adversarial tests

Schema: `src/analysis/prereg.py` (frozen dataclasses + content-hash lock).
Adversarial + calibration suite: `tests/test_analysis.py` (16 tests) — separation,
single cluster, perfect ties, dropout-tied-to-outcome, post-hoc endpoint,
nonconvergence→indeterminate, plus power (strong effect ≥ 0.80) and type-I control
(null ≤ 0.15, one-sided 95% CI target ~0.025).

## Human sign-off required (goes to the consolidated decision packet)

δ_sup, δ_ni, per-endpoint α, target power, catch-trial exclusion rate, and
independent method (statistical) review. **No value here is set on the owner's
behalf.** Final n follows pilot variance at DT-60.
