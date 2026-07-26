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

## DT-55E oracle probe (2026-07-25) — F-4, F-5, F-6

> **Read F-7 first.** F-4/F-5/F-6 searched the *planner's* strength mapping, not
> the registry's declared safe ranges. Their `missing_processor` verdicts do NOT
> survive F-7; their range-binding and direction observations turn out to describe
> the planner's specs rather than the processors. The 86% abstention measurement
> and the taxonomy stand.

The probe forces the planner's **own** treatments to engage and sweeps them across
the registry's safe strength range (5 strengths × 3 chains = 15 candidates/pair),
measuring composite distance to the aligned wet target. **Diagnostic only**: no
threshold tuned, nothing promoted, no perceptual claim.

### F-4 (correction to F-1's interpretation): engagement alone is *not* sufficient

F-1 established that the champion abstains (still true: **86% abstention** across
valid pairs). F-1 then *inferred* that engagement was therefore the dominant
bottleneck. The oracle measured it, and that inference was **too strong**:

| classification | pairs | meaning |
|---|--:|---|
| `engagement_gap` (≥10% closed) | 2 | forcing the existing chain to run helps materially |
| `data_limitation` (2–10%) | 1 | real movement, below what this corpus can attribute |
| `missing_processor` (≤2%) | 4 | the existing registry cannot get closer at any allowed setting |
| `inconclusive_alignment` | 2 | 0 measurable phrases — **excluded from all aggregates** |

Median improvement across the 7 valid pairs is **+0.67%**; mean **+7.05%**
(bootstrap 95% CI **−3.00% .. +20.45%** — the CI spans zero, so no aggregate
effect is established). Engagement is **necessary but not sufficient**.

### F-5 (new): where the existing treatment helps, the *safe range is binding*

Composite distance vs. strength is **monotone on every pair** — this is signal,
not noise. Three pairs fall continuously and are **still falling at maximum
strength** (slopes −0.091, −0.023, −0.108): the optimum lies *outside* the range
the registry permits. Those are exactly the three pairs that improved most
(+43.5%, +8.4%, +10.9%). At strength 1.0 the muddiness treatment is only a
**−4.0 dB** PeakFilter at 300 Hz; the search wants more than the planner may apply.

**This is a parameter-range limit, not a missing processor** — a materially
cheaper problem, and it was invisible at the original single fixed strength (0.7).

### F-6 (new): on the other four pairs the existing treatment is the *wrong direction*

The remaining four pairs get monotonically **worse** with any amount of low-mid
cut (edge slopes +0.009 to +0.268). The registry offers subtractive low-mid /
harshness filtering plus a fixed-threshold gate; these wet targets do not want
subtraction. Weak supporting signal: improvement correlates negatively with the
measured wet−raw low-mid delta (**r = −0.479, n = 7**) — direction is consistent
with "subtractive treatment helps only when the wet has *less* low-mid than the
raw", but n = 7 cannot establish it. Recorded as a hypothesis, not a finding.

### Bottleneck determination (evidence only)

**Mixed**, and the split is roughly even — so priority follows *measured impact*:

- **3 / 7 pairs are recoverable with existing DSP** (engagement + a wider allowed
  range): +43.5%, +10.9%, +8.4%.
- **4 / 7 pairs appeared unrecoverable** (≤ +0.7%, two negative). **Retracted by
  F-7:** all four close 20.9–57.8% once the registry's own ranges are searched.

## DT-55E Track C registry-safe search (2026-07-26) — F-7

F-4/F-5/F-6 were all measured inside the **planner's** strength mapping. F-7 is
the same question asked of the **processor registry's** own declared safe ranges,
via deterministic coordinate descent (`src/paired_corpus/search.py`), with the
−0.2 dBFS ceiling, zero-clipping and an SI-SDR ≥ 5 dB preservation floor enforced
as part of the objective.

### F-7 — no `missing_processor` verdict survives a search of the real space

| pair | strength sweep (F-4) | registry-safe search | smallest sufficient chain |
|---|--:|--:|---|
| P-01 | +43.5% | **+62.1%** | t5_full |
| P-02 | +0.3% | **+20.9%** | t5_full |
| P-05 | −5.6% | **+57.8%** | t5_full |
| P-06 | +8.4% | **+56.3%** | t5_full |
| P-07 | −8.8% | **+33.7%** | t5_full |
| P-09 | +0.7% | **+45.2%** | t3_tonal_air |

Median **+50.7%**, mean **+46.0%**, bootstrap 95% CI **+33.5% .. +56.9%** (excludes
zero, unlike F-4's). The planner's muddiness treatment caps at −4.0 dB where
`PeakFilter` permits −12..+12 dB — and permits boosting, which retires F-6's
"the registry only subtracts" reading as a planner-spec property, not a processor
property. F-5's range-binding is likewise a **spec** cap, not a registry limit.

**Consequence:** the measured champion→wet gap is attributable to the planner —
what it engages (F-1) and what its specs permit (F-7) — not to absent DSP.
5 of 6 pairs needed the full chain including gate and compressor; 1 needed only
tonal EQ + air.

**What F-7 does not show:** that the planner can *find* these settings from the
raw audio alone. The oracle is given the wet target; the planner is not. That is
the burden of proof for any A-1/A-2 experiment, on held-out artists.

## What this does NOT show

Not that DrakoTune's processors are good or bad (they barely ran); not any
perceptual quality; not generalization (one artist). It shows *where to look*.

Additionally, F-4/F-5/F-6 do **not** show that any change would sound better —
composite spectral distance to a lossy YouTube "wet" is not perceptual quality.
They show which *class* of engineering work has measurable headroom.

## Method limitations of the oracle probe itself

- The sweep varies the planner's `strength` only. Because `_ISSUE_SPECS` maps
  strength to a single parameter per treatment, this spans muddiness cut
  0.8→4.0 dB, harshness cut 0.9→4.5 dB and rumble cutoff 84→100 Hz — but the
  **NoiseGate spec is strength-invariant** (fixed −42 dB threshold), so "denoise
  does not help" is only tested at that one threshold.
- Three predeclared chains, fixed order. Not the full coordinate descent over
  ≤6 params the orchestration plan specifies for DT-55E.
- `missing_processor` therefore means "no *searched* configuration got closer",
  which is weaker than "no configuration exists".
- Registration defect found and fixed 2026-07-25: `extract_youtube_id` took the
  *first* bracket group, so a filename carrying an annotation bracket before the
  id recorded the annotation as the video id (1 of 31 records). Identity keys are
  sha256, so no rights decision was affected. The **local manifest still holds
  the stale id** until the registrar is re-run; the anonymization gate ignores
  non-id-shaped values so a bad parse cannot cause a false failure.
- 2 of 9 pairs contributed nothing (alignment failure); one wet target is a
  self-made extraction rather than a professional master, so it is a weak
  reference by construction (see the local registration manifest).

## Recommended next work

1. **DT-77 roadmap** (`AURELIAN/02_RESEARCH/DT77_IMPROVEMENT_BRIEF.md`) — now
   derived from F-4/F-5/F-6 rather than from F-1's inference.
2. Close the method gaps above (NoiseGate threshold sweep; coordinate descent)
   before treating any `missing_processor` verdict as final.
3. Any retuning must use artist-held-out splits + a predeclared contract; never
   tune thresholds to fit this tiny corpus (overfitting/leakage).
