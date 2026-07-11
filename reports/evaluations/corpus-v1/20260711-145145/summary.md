# Benchmark 20260711-145145 — corpus-v1

Engines: v2 · 160 degraded pairs · benchmark v1.0.0. Objective evidence only (ADR 0004): loudness-matched, reference-based; no perceptual claim.

| family | severity | engine | n | ΔSI-SDR (dB) | ΔsegSNR (dB) | Δdefect-band | out-clip max |
|---|---|---|--:|--:|--:|--:|--:|
| clipping | mild | v2 | 5 | -13.116 | -23.183 | 0.008 | 0.0000 |
| clipping | moderate | v2 | 5 | -7.464 | -13.852 | 0.005 | 0.0000 |
| clipping | strong | v2 | 6 | -3.846 | -8.735 | 0.005 | 0.0000 |
| codec | moderate | v2 | 5 | -23.469 | -16.798 | None | 0.0000 |
| codec | strong | v2 | 5 | -18.162 | -15.423 | None | 0.0000 |
| harshness | moderate | v2 | 6 | -5.36 | -5.807 | -0.0 | 0.0000 |
| harshness | strong | v2 | 6 | -0.937 | -0.096 | -0.006 | 0.0000 |
| hum | mild | v2 | 6 | -5.836 | -3.132 | 0.034 | 0.0000 |
| hum | moderate | v2 | 6 | -1.985 | 0.98 | -0.211 | 0.0000 |
| hum | strong | v2 | 6 | 7.48 | 5.108 | -0.615 | 0.0000 |
| low_level | moderate | v2 | 6 | 0.0 | 0.0 | None | 0.0000 |
| low_level | strong | v2 | 6 | -3.506 | -0.416 | None | 0.0000 |
| noise | mild | v2 | 18 | -6.37 | -5.268 | 0.0 | 0.0000 |
| noise | moderate | v2 | 17 | -2.107 | -2.117 | 0.001 | 0.0000 |
| noise | strong | v2 | 16 | 2.568 | 1.513 | 0.005 | 0.0000 |
| proximity | moderate | v2 | 6 | -1.561 | -2.322 | 0.015 | 0.0000 |
| reverb | mild | v2 | 6 | -2.431 | -1.913 | None | 0.0000 |
| reverb | moderate | v2 | 5 | -0.228 | -0.241 | None | 0.0000 |
| reverb | strong | v2 | 5 | -0.068 | -0.139 | None | 0.0000 |
| sibilance | moderate | v2 | 6 | -6.504 | -6.402 | 0.001 | 0.0000 |
| sibilance | strong | v2 | 6 | -2.816 | -3.549 | -0.003 | 0.0000 |

Errored pairs: 7

## M28 HumNotch impact (v2, vs run 20260711-143712)

- hum/strong: ΔSI-SDR +2.93 → **+7.48 dB**; hum-band delta −0.19 → **−0.62**.
- hum/moderate: hum-band removal quadrupled (−0.055 → −0.211) at a small
  fidelity cost (ΔSI-SDR −1.22 → −1.99) — the notch also nicks voice content
  near the mains harmonics. Flagged for perceptual confirmation in M24.
- hum/mild: unchanged by design — the 0%-clean-FP promotion gate
  (≥4 harmonics @ ≥100× contrast) intentionally does not fire at mild
  severity (33% gate recall); mild hum remains advisory + report guidance.
- No SI-SDR movement in any non-hum cell; output clipping 0.0000 everywhere.
