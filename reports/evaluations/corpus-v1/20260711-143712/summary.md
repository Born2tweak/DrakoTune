# Benchmark 20260711-143712 — corpus-v1

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
| hum | mild | v2 | 6 | -5.743 | -3.986 | 0.046 | 0.0000 |
| hum | moderate | v2 | 6 | -1.219 | -0.307 | -0.055 | 0.0000 |
| hum | strong | v2 | 6 | 2.929 | 1.487 | -0.189 | 0.0000 |
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

## Post-recalibration comparison (v2 engine, vs run 20260711-140753)

Spectral analyzer 1.2.0 (M26) improved ΔSI-SDR in 15 of 21 cells by removing
spurious processing: low_level/moderate −18.96 → 0.00 dB (transparent level
restore), low_level/strong −22.27 → −3.51, harshness/strong −4.57 → −0.94,
harshness/moderate −10.52 → −5.36, noise/mild −9.94 → −6.37, reverb and codec
cells all improved (fewer false detections → less collateral reshaping).
Logged regressions: noise/moderate −0.95 → −2.11 and proximity/moderate
+1.43 → −1.56 (recalibrated detectors now fire mud/sibilance on some of these
clips; flagged for the M24 perceptual round before any counter-tuning).
