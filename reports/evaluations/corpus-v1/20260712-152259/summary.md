# Benchmark 20260712-152259 — corpus-v1

Engines: v2 · 160 degraded pairs · benchmark v1.0.0. Objective evidence only (ADR 0004): loudness-matched, reference-based; no perceptual claim.

| family | severity | engine | n | ΔSI-SDR (dB) | ΔsegSNR (dB) | Δdefect-band | out-clip max |
|---|---|---|--:|--:|--:|--:|--:|
| clipping | mild | v2 | 5 | -0.213 | -0.389 | -0.0 | 0.0000 |
| clipping | moderate | v2 | 5 | 0.0 | 0.0 | -0.0 | 0.0000 |
| clipping | strong | v2 | 6 | 0.0 | 0.0 | 0.0 | 0.0000 |
| codec | moderate | v2 | 5 | -26.056 | -21.777 | None | 0.0000 |
| codec | strong | v2 | 5 | -20.565 | -19.562 | None | 0.0000 |
| harshness | moderate | v2 | 6 | -6.9 | -9.906 | 0.001 | 0.0000 |
| harshness | strong | v2 | 6 | -1.704 | -3.594 | -0.005 | 0.0000 |
| hum | mild | v2 | 6 | -6.641 | -4.526 | 0.048 | 0.0000 |
| hum | moderate | v2 | 6 | -0.5 | 2.275 | -0.225 | 0.0000 |
| hum | strong | v2 | 6 | 7.48 | 5.108 | -0.615 | 0.0000 |
| low_level | moderate | v2 | 6 | -53.447 | -23.466 | None | 0.0000 |
| low_level | strong | v2 | 6 | -44.221 | -21.97 | None | 0.0000 |
| noise | mild | v2 | 17 | -9.035 | -8.038 | 0.001 | 0.0000 |
| noise | moderate | v2 | 17 | -3.476 | -3.081 | 0.003 | 0.0000 |
| noise | strong | v2 | 16 | 2.147 | 0.944 | 0.005 | 0.0000 |
| proximity | moderate | v2 | 6 | -2.745 | -4.969 | 0.019 | 0.0000 |
| reverb | mild | v2 | 6 | -4.99 | -7.013 | None | 0.0000 |
| reverb | moderate | v2 | 5 | -1.126 | -2.684 | None | 0.0000 |
| reverb | strong | v2 | 5 | -0.727 | -1.124 | None | 0.0000 |
| sibilance | moderate | v2 | 6 | -8.753 | -11.428 | 0.002 | 0.0000 |
| sibilance | strong | v2 | 6 | -4.233 | -7.629 | -0.006 | 0.0000 |

Errored pairs: 8

## M38 findings — objective cost of the 'polished' style preset

Caveat: the nearest clean-preset baseline (20260712-095014) predates the M33
fixes, so low_level deltas are not directly comparable; a fresh full-grid
clean baseline lands with the corpus-v2 rebuild (M40). Within that limit:

1. **Style compression costs fidelity exactly where expected:** quiet inputs
   (post-gain-restore, compressor engages across the board) and mild-defect
   cells pay 2-27 dB dSI-SDR — the known, accepted price of a style choice
   (ADR 0005); never presented as defect repair.
2. **The abstention makes polished SAFER than clean on clipped inputs:**
   clipped audio reads as already-crushed (low crest), the style compressor
   abstains, and the output stays near-identical (dSI-SDR -0.2 vs clean's
   -13.0) — 'do less' wins on damaged material, by design.
3. **Safety green:** output clipping 0.0000 in every polished cell.
4. Perceptual verdict on polished-vs-clean belongs to listeners; matched A/B
   pairs of the product owner's own files are exported for exactly that.
