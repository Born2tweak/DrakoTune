# Bounded DSP experiment — sibilance de-essing (2026-07-23)

**Objective-only. No perceptual claim.** Reconciliation spike (not a DT-80 promotion).
Contract: `EXPERIMENT_CONTRACT.md` (predeclared before rendering). Data: `results.json`.
Champion commit: `61fc94f`. Corpus: `corpus-v1` (160 degraded pairs) + 3 CC-BY real clips.

## Verdict: REJECTED (as a blanket treatment) — champion abstention vindicated

| Predeclared criterion | Result | Pass? |
|---|---|---|
| Sibilance-band reduction ≥ 20% (mean, 12 sibilance pairs) | **26.1%** | ✅ |
| Do-no-harm: SI-SDR on non-sibilance ≥ champion − 0.5 dB | 22/148 clips regressed (median −8.6 dB, worst −42 dB) | ❌ |
| Do-no-harm: no peak > −0.2 dBFS ceiling beyond champion | 12 clips (all `clipping` family) exceeded; worst 1.117 | ❌ |
| Do-no-harm: no clipping increase vs champion | 1 clip (vocadito_16) 0.0 → 7.5e-5 | ❌ |

**Overall:** the treatment meets the sibilance-reduction bar but breaches do-no-harm
decisively, so it is **rejected**. This is a product-advancing negative result
(logged N-014), not a null run.

## Why (root cause)

- The decision engine emits **0 actions** on the corpus sibilance samples: measured
  `sibilance_frame_p95 ≈ 0.088` is **below** the DeEsser's minimum in-range
  `frame_threshold` (0.10), and de-essing is otherwise only added as a
  post-compression guard (no compressor is planned here). The champion therefore
  safely abstains.
- Forcing a blanket in-range de-ess then (a) badly harms fidelity on low_level /
  codec / harshness content (SI-SDR), and (b) runs *after* the executor's −0.2 dBFS
  ceiling, so on hard-clipped inputs the band recombination overshoots unity.

## Improvement brief (seeds DT-77)

1. Sibilance treatment must be **detection-gated per clip**, never blanket — the
   champion's conditional gating is correct and should be preserved.
2. Any de-ess must execute **inside** the output-safety envelope (re-apply the
   ceiling after the array processor), not after `execute_plan`.
3. Catching this synthetic sibilance class needs a **validated lowering** of the
   de-ess frame floor below 0.10, with its own do-no-harm proof — a separate
   experiment, not a blanket change.

## Real-clip production baseline (champion, 3× CC-BY)

First tracked production baseline on the real clips (previously only gitignored
scratch existed). Confirms safety + non-destructive behavior:

| clip | actions | in peak | out peak | clipping | ≤ ceiling | source overwritten |
|---|--:|--:|--:|--:|:--:|:--:|
| vocadito_1 | 0 (abstain) | 0.531 | 0.531 | 0.0 | ✅ | no |
| vocalset_female1_straight | 0 (abstain) | 0.389 | 0.389 | 0.0 | ✅ | no |
| vocalset_female1_vibrato | 2 | 0.439 | 0.238 | 0.0 | ✅ | no |

On clean real vocals the champion largely abstains (0 actions) or applies a small
attenuating chain; it never clips, never exceeds the ceiling, never overwrites the
source (P-01). No perceptual quality is claimed.
