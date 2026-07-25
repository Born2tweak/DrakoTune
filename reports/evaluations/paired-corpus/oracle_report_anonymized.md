# DT-55E oracle probe — evidence report

Authorization D-029 (local/internal/eval-only). **Diagnostic only**: the
probe forces the planner's OWN treatments to engage and measures distance
to the aligned wet target. No threshold tuned, nothing promoted, no
perceptual claim. Sources are lossy — distances are directional.

`inconclusive_alignment` pairs are EXCLUDED from every aggregate below.

## Per-pair evidence

`range binding` = the distance was STILL falling at the top of the
registry's safe range, i.e. the optimum lies outside what the planner is
allowed to apply (a parameter-range limit, not a missing processor).

| pair | champ acts | phrases | champ→wet | oracle→wet | improvement | best candidate | searched | range binding | active processors | conf | classification |
|---|--:|--:|--:|--:|--:|---|--:|---|---|--:|---|
| P-01 | 0 | 33 | 2.795 | 1.578 | +43.5% | forced_lowmid@1.0 | 15 | **yes** (-0.091) | HighpassFilter, PeakFilter | 1.00 | **engagement_gap** |
| P-02 | 0 | 23 | 6.403 | 6.385 | +0.3% | forced_lowmid_denoise@0.4 | 15 | no (+0.016) | HighpassFilter, PeakFilter, NoiseGate | 0.17 | **missing_processor** |
| P-03 | | | | | | | | | | | incorrect_pair |
| P-04 | 2 | 0 | inf | inf | +0.0% | — | 15 | — | — | 0.00 | **inconclusive_alignment** |
| P-05 | 1 | 101 | 4.783 | 5.052 | -5.6% | forced_lowmid@0.2 | 15 | no (+0.083) | HighpassFilter, PeakFilter | 0.76 | **missing_processor** |
| P-06 | 0 | 43 | 5.756 | 5.273 | +8.4% | forced_lowmid@1.0 | 15 | **yes** (-0.023) | HighpassFilter, PeakFilter | 0.16 | **data_limitation** |
| P-07 | 0 | 15 | 2.708 | 2.948 | -8.8% | forced_full@0.4 | 15 | no (+0.099) | HighpassFilter, PeakFilter, PeakFilter, NoiseGate | 0.75 | **missing_processor** |
| P-08 | 0 | 0 | inf | inf | +0.0% | — | 15 | — | — | 0.00 | **inconclusive_alignment** |
| P-09 | 0 | 28 | 4.298 | 4.269 | +0.7% | forced_lowmid_denoise@0.4 | 15 | no (+0.023) | HighpassFilter, PeakFilter, NoiseGate | 0.13 | **missing_processor** |
| P-10 | 0 | 16 | 7.197 | 6.414 | +10.9% | forced_lowmid_denoise@1.0 | 15 | **yes** (-0.108) | HighpassFilter, PeakFilter, NoiseGate | 0.07 | **engagement_gap** |

## Aggregate (valid pairs only)

- pairs total: **9**; valid: **7**; excluded as inconclusive: **2**
- median improvement: **+0.67%**
- mean improvement: **+7.05%** (bootstrap 95% CI -3.00% .. +20.45%)
- champion abstention rate: **86%**; engagement rate: **14%**
- range-binding pairs: **3** (43% of pairs where a sweep measured a slope)

### Classification counts

- `engagement_gap`: 2
- `missing_processor`: 4
- `data_limitation`: 1
- `inconclusive_alignment`: 2

### Processor activation frequency (best candidate per valid pair)

- `PeakFilter`: 8
- `HighpassFilter`: 7
- `NoiseGate`: 4
