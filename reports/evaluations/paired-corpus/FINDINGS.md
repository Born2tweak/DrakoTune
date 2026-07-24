# Paired-Corpus Gap Analysis — Findings (DT-55D)

**Date:** 2026-07-24 · **Authorization:** D-029 (local/internal/eval-only) ·
**Material:** ~10 raw/wet rap-acapella pairs (single dominant artist), lossy MP3.
Pair IDs are anonymized (P-01…P-10); the title map stays local
(`data/restricted/`, gitignored), as does all audio and per-phrase detail.
**Class:** exploratory, directional. **No perceptual claim. Does NOT satisfy
DEF-003** (rights + representativeness both fail: one artist, lossy, tiny).

## Headline finding (F-1): the champion abstains on real rap acapella

Across the 9 processable pairs, the current champion applied **0 processing
actions on 7 of them** (one pair: 1 action, one: 2). On the best-aligned pair
(P-01, envelope-corr 0.84, 33/34 phrases aligned) the diagnosis *sees* the defects
but does not act:

| measured on P-01 raw | value | meaning | champion response |
|---|---|---|---|
| `mud_ratio` | 6.62 | heavy low-mid boxiness ("weak mic") | no low-mid cut fired |
| `noise_floor_dbfs` | −44.5 | audible hiss | `reduce_noise` at **conf 0.22 → report_only** (not applied) |
| `centroid_hz` | 2622 | dark/muffled | no brightening |
| `sibilance_frame_p95` | 0.095 | just below the 0.10 de-ess floor | de-ess cannot engage (cf. N-014) |
| `harshness_ratio` | 0.022 | present | not treated |

**Interpretation.** The gap the owner heard ("subtle improvement, still boxy,
unclear, weak-mic, fatiguing") is primarily a **decision-engine engagement**
problem, not a DSP-quality problem: the planner's confidence/threshold gating —
calibrated on synthetic degradations and clean studio *singing* — rates its
confidence too low to act on real home-recorded *rap* vocals, so it passes them
through nearly untouched. You cannot perceive a chain that never runs.

Per the DT-55E oracle framing, this splits the quality gap decisively toward
**(b) missing engagement / miscalibrated triggering** first, before **(a)
parameter tuning** or **(c) missing modules**.

## Secondary findings

- **F-2 (alignment limits on real rips):** 2 pairs aligned 0 phrases
  (env-corr 0.41–0.44) and 1 classified `incorrect_pair` (corr 0.13) — likely not
  the same performance/edit, or a very different mix. These need human review; the
  aligner correctly refused rather than fabricating matches.
- **F-3 (directional wet character):** where alignment held, the wet references
  trend **brighter** than the champion (median Δtilt +1 to +4 dB/oct) and, on the
  cleanest pair, carry **less** low-mid (P-01 Δlowmid −0.07). Consistent with
  professional low-mid control + presence lift — lossy-MP3 + low-corr, so
  directional only.

## What this does NOT show

Not that DrakoTune's processors are good or bad (they barely ran); not any
perceptual quality; not generalization (one artist). It shows *where to look*.

## Recommended next work

1. **DT-77 brief B-1** (`AURELIAN/02_RESEARCH/DT77_IMPROVEMENT_BRIEF.md`):
   recalibrate planner engagement on real rap-acapella feature distributions —
   highest leverage.
2. **DT-55E oracle probe:** on the verified-exact pairs, force the existing chain
   to engage (apply the currently-gated mud cut + noise reduction within safe
   bounds) and measure whether the objective gap to the wet target shrinks without
   a do-no-harm breach — answers (a)-vs-(b)-vs-(c) with evidence.
3. Any retuning must use artist-held-out splits + a predeclared contract; never
   tune thresholds to fit this tiny corpus (overfitting/leakage).
