# Practitioner priors vs. mode contracts

**Date:** 2026-08-03
**Status:** DT-107 shipped. Presence and harshness stages retuned in `src/modes/contracts.py`;
full suite green (1005 passed). Rejected candidates preserved in §10.
**Evidence class:** PRIOR. Nine short social-media instructional clips. Not a study, not
measurement, not evidence of perceptual improvement. Nothing here may support a product claim.
**Claims dataset:** [`data/practitioner_claims/mixing_corpus_claims.json`](../../data/practitioner_claims/mixing_corpus_claims.json)
**Compared against:** [`src/modes/contracts.py`](../../src/modes/contracts.py) @ `b8424f7`

---

## 1. Why this exists

F-23 recorded that the autonomous audio frontier is exhausted and that every remaining
milestone which would reduce the measured audio gap is gated on an owner decision. This
document tests a narrower question that does not require one: **where do the authored mode
constants disagree with what working rap-vocal engineers say they do?**

The constants in `contracts.py` are honest engineering choices, but they are unsourced.
This gives them an outside reference for the first time. It changes no code.

## 2. What the source material actually is

25 clips were supplied. They split into two groups that must be handled differently:

| Group | Count | Duration | Use |
|---|---|---|---|
| Instructional | 9 | ~11 min | This document. Propositional claims + attribution. |
| Finished commercial rap vocals | 16 | ~8 min | **See §5 — blocked.** |

## 3. Where the engine already agrees

These are the strongest agreements, and they are worth recording because they mean the
existing constants were not arbitrary.

| Area | `contracts.py` | Practitioner prior | |
|---|---|---|---|
| Low-mid mud cut | Peak 320 Hz, −4 dB, Q 1.3 (rap); 300 Hz elsewhere | 200–500 Hz (PC-004, n=2) | agrees |
| Staged compression | two serial stages + parallel bus | staged compression, each stage doing little (PC-007, n=3) | agrees |
| Parallel ratio | parallel bus at 10:1 | about 10:1 (PC-010) | exact |
| Cut before boost | subtractive EQ precedes additive | cut before boosting (PC-015, n=4) | agrees |
| Reverb placement | `Send`, i.e. a return, and last | reverb best placed on a return (PC-015) | agrees |
| Mono survival | mono fold-down checked | if the mix fails on any system, return to level balance (PC-017) | agrees |

## 4. Where they disagree

Ordered by how actionable the disagreement is. Each is a **hypothesis to test**, not a
defect report — the corpus is opinion, and the engine's choice may still be the better one.

### CONFLICT-001 — Modern Rap boosts the band practitioners cut

`_modern_rap` applies `PeakFilter(3200 Hz, +2.5 dB, Q 1.1)` statically, while also running
`DynamicEQ(2000–4500 Hz, max −5 dB)` to catch harshness in the same region.

The corpus cuts 2.5–5 kHz (PC-006) and places its presence boosts at **1.2 kHz, 1.7 kHz and
8 kHz** (PC-011) — deliberately straddling that band rather than sitting in it.

Note this is not automatically wrong: a static presence lift with a dynamic catch on top is a
legitimate, common design. But the corpus offers no support for a static boost there, and the
frequencies it does boost are ones the engine currently leaves alone.

**Measured on the five rap takes (2026-08-03), and the test was not clean.** Replacing
`PeakFilter(3200, +2.5)` with `PeakFilter(1700, +2.0)` + `PeakFilter(1200, +1.5)` raised output
loudness on every take (+0.21, +0.28, +0.48, +0.93, +1.00 LU) and reduced crest by up to 1.0 dB.

**This does not validate the practitioner placement.** The variant applies boosts at two bands
totalling +3.5 dB against the shipped +2.5 dB, so it is louder partly because it is simply more
boost. Band placement and total gain are confounded. Reporting the loudness rise as support for
PC-011 would be exactly the error N-016..N-022 identified — objective movement read as
improvement. **A gain-matched A/B plus listening is required before this conflict is resolved
in either direction.** The renders are retained for that listening pass.

### CONFLICT-002 — the high-pass sits above every stated value

| | cutoff |
|---|---|
| Natural | 75 Hz |
| Rescue | 95 Hz |
| **Modern Rap** | **105 Hz** |
| Corpus (PC-001, n=4) | 80–100 Hz, central ~85 Hz |

Modern Rap is 15–25 Hz above the stated central value. One source names this exact failure
mode as motivation for a different technique: a low cut placed too high removes vocal body and
leaves the result too bright (PC-002).

Modern Rap is also the mode measured at −17.15 LUFS, 3.5 LU quieter than Natural/Bold. A
higher high-pass removing low-end energy looked like a plausible partial contributor.

**This was measured, and the loudness hypothesis is refuted.** Modern Rap / Bold rendered on
the Tier A real fixtures at 105 Hz (shipped), 85 Hz (corpus central) and 75 Hz:

| Fixture | 105 Hz | 85 Hz | 75 Hz | max ΔLUFS |
|---|---|---|---|---|
| vocadito_1 | −15.42 | −15.34 | −15.38 | **+0.08** |
| vocalset_female1_straight | −14.26 | −14.25 | −14.24 | **+0.02** |
| vocalset_female1_vibrato | −14.78 | −14.78 | −14.78 | **0.00** |

The high-pass cutoff moves integrated loudness by at most 0.08 LU. **It does not explain the
3.5 LU shortfall**, and re-tuning it will not close that gap. The cause is elsewhere — the
density/parallel stage, the sends, or the export gain stage are the remaining candidates.

Two honest limits on this result. First, it measures loudness only; the *tonal* objection in
PC-002 (thin, over-bright, no body) is untested and remains open. Second, and more seriously:

> **All three real fixtures are solo singing, two of them explicitly female, and none is a rap
> vocal.** The corpus value is conditioned on the opposite voice type — the source places the
> cut below 80 Hz **because their own voice is low** (PC-001). A 105 Hz cut removes far less from a female singing
> voice than from a low male rap delivery, so this test is weak evidence for the population
> Modern Rap actually targets.

That gap is itself a finding: **the flagship rap mode has no real fixture representing its
target voice.** Every real-vocal result for Modern Rap to date inherits that limitation.

**Update (2026-08-03): the gap is now closed, and the refutation holds.** Five owner-supplied
male rap takes were characterized (§4a) and the experiment was repeated on them. Across all
five, moving the high-pass from 105 Hz to 85 Hz or 75 Hz changes integrated loudness by
**at most 0.13 LU** (range −0.13 to +0.11). CONFLICT-002's loudness hypothesis is refuted on
the correct voice population, not just on female singing. The tonal objection in PC-002
remains untested and still requires listening.

### CONFLICT-003 — the two compression stages ramp the wrong way

| | stage 1 | stage 2 |
|---|---|---|
| Modern Rap | −18 dB, **3:1**, 4 ms, 90 ms | −26 dB, **2.5:1**, 25 ms, 220 ms |
| Corpus (PC-008/009) | **4:1**, 2 ms, 80 ms, ~−6 dB GR | **6:1**, fast, ~−6 dB GR |

The engine's ratio *decreases* across stages; the corpus's *increases*. Stage 1 timing is
close (4 ms/90 ms vs 2 ms/80 ms). The corpus's second stage is a fast, higher-ratio grab; the
engine's is a slow leveller. These are genuinely different design intents.

### CONFLICT-004 — the doubler is likely much wider than practice

DT-98 ships `Doubler(±9/+11 cents, 17/25 ms, pan ±0.7, level 0.32)`.

The corpus's only numeric width statement is **~10%**, with an explicit caution against very
wide settings on a mono source (PC-013).

`level 0.32` with hard ±0.7 pans is not directly comparable to an unnamed plugin's "10%", so
this is not a like-for-like contradiction. But the *stated intent* is restraint, and the
current setting is not restrained. This is the one conflict that touches freshly shipped code.

### CONFLICT-005 — air is boosted where the corpus cleans

Modern Rap: `HighShelfFilter(9500 Hz, +3.5 dB)`. Corpus: clean up the 10–15 kHz region, then a
high shelf (PC-012). Directionally opposed, single source, lowest confidence here.

## 4a. The owner rap corpus, and what it actually is

Five owner-supplied takes (~11.8 min, 32-bit float, 44.1 kHz) closed the fixture gap. Full
characterization: [`data/practitioner_claims/owner_rap_corpus_characterization.json`](../../data/practitioner_claims/owner_rap_corpus_characterization.json).

**The `RawTune` filename is not reliable and must not be trusted as a label.** Measured:

| Take | median cents off grid | within 5c | verdict |
|---|---|---|---|
| *Tier A untuned reference* | *19.2 – 20.8* | *10.3 – 13.9%* | *baseline* |
| Gwapped Up | 19.2 | 13.3% | untuned |
| MoveWrong | 19.2 | 16.8% | untuned |
| Just_Vibe | 10.8 | 23.0% | moderately tuned |
| NotWorthIt_Stressing | 10.8 | 27.8% | moderately tuned |
| **LiveLeak** | **0.8** | **52.0%** | **hard-snapped** |

Three of five carry baked-in pitch correction. **Only Gwapped Up and MoveWrong can test
DT-100's pitch correction**; the rest would be correcting already-corrected audio.

Further per-take processing that rules out specific uses:

- **All five are loudness-normalized** (−11.2 to −12.2 LUFS, peaks at −0.32 to −0.54 dBFS).
  Like the social clips, they cannot serve as loudness references.
- **All five are effectively mono** (L/R correlation 1.000000; MoveWrong bit-identical).
- **MoveWrong is already high-passed** (sub-60 Hz at −2.9 dB vs +9.8 for Gwapped Up) — exclude
  it from high-pass experiments.
- **Just_Vibe is gated to digital silence** (−241 dB floor) — it cannot test gate or noise
  behaviour.

### New lead on the 3.5 LU question

The rap renders surfaced something the female fixtures did not: **output loudness varies
inversely with input loudness.** LiveLeak has the *hottest* input (−11.22 LUFS) and renders the
*quietest* (−15.66), while Gwapped Up at −12.02 in renders −12.84 — a 2.8 LU spread across
takes **within the same mode and intensity**.

The mode's compressor thresholds are absolute (−18, −26, −34 dBFS), with no input levelling
ahead of them, so a hotter input drives proportionally more gain reduction. That is a concrete,
testable mechanism for the cross-mode loudness inconsistency, and it is a better lead than the
high-pass ever was. It also means the measured "3.5 LU spread between modes" is partly a
property of the *input*, not only the mode.

## 5. Gaps — in the corpus, absent from the engine

- **1 kHz dip** (PC-005). No mode has any treatment at 1 kHz; one source dips it for
  further muddiness beyond the 200–500 Hz cut.
- **Compress-and-restore in the low band** (PC-003). Rescue's `DynamicEQ(220–520 Hz)` reduces
  but never restores level. The corpus technique compresses 120–200 Hz *and boosts it back*,
  specifically to keep body while gaining clarity. Modern Rap has no low-band dynamic
  treatment at all. This is the most interesting unimplemented idea in the corpus.

## 6. Blocked: the reference-audio half

The 16 finished commercial clips were intended to supply a target envelope. **Two independent
reasons stop them, and I did not proceed.**

**Reason 1 — governance.** `docs/data/DATASET_GOVERNANCE.md` §1 places "scraped a cappellas
(Looperman/YouTube)" in **Tier D — `excluded`: allowed *nothing*, forbidden *everything*.**
These are social-platform captures of copyrighted commercial recordings with no license. Under
this project's own rule they cannot become an evidence asset. Triage measurements were computed
in a scratchpad and are reported below as a finding *about the material*; they are not
committed and must not be used as targets without an explicit recorded owner decision.

**Reason 2 — DT-102 needs pairs, and there are none.** DT-102 is specified as "raw→studio
**deltas**". A delta requires a raw and a treated version of the same performance. This corpus
has finished output only. It could at best describe a one-sided target distribution, which is
not what DT-102 asks for. **This corpus cannot satisfy DT-102 as written**, regardless of the
rights question.

**Triage finding, recorded because it is useful either way:** all 25 clips measure ~−13.8 LUFS
(range −13.05 to −14.5) and **every one hits 0.0 dBFS true peak**. That is platform
normalisation and limiting, not engineering intent. Any loudness target drawn from social-media
captures would be measuring TikTok, not the mix engineer. It follows that this material could
never have validated or refuted the Natural/Bold (−13.65) vs Modern Rap (−17.15) spread, and
future corpus work should not attempt it.

## 7. What I did not do, and why

- **No milestone assigned.** DT-107 is the next free ID, but assigning one and writing to
  `MILESTONE_REGISTRY.yaml` is a governance act, and the registry is the machine authority for
  status. That is the owner's call.
- **No status change** to `PROJECT_STATE.md`.
- **No code changed.** Every conflict above is a hypothesis; acting on any of them without an
  A/B would repeat exactly the error N-016..N-022 warned about.
- **No claim strengthened.** Nine clips of opinion cannot move any row in the evidence table.

## 8. Recommended next step

CONFLICT-002's loudness hypothesis is already measured and refuted (§4). Remaining, cheapest
first:

1. **Confirm the rights assumption on the owner corpus.** Recorded as an assumption in the
   characterization file: these are treated as owner-held and self-recorded. If any take
   involves a featured artist or session vocalist it becomes Tier P and needs consent scope
   first. One question, and it gates everything below.
2. **Test the input-level mechanism (§4a).** Loudness-normalize all five takes to a common
   input LUFS, re-render, and see whether the 2.8 LU output spread collapses. If it does, the
   mode loudness inconsistency is an input-levelling problem rather than a mode-tuning problem
   — which reframes DT-104. Cheapest real lead available, and pure measurement.
3. **CONFLICT-001, properly.** Gain-matched A/B of the 3.2 kHz boost against 1.2/1.7 kHz, then
   listen. The current result is confounded and settles nothing.
4. **CONFLICT-004** — bring the doubler down toward the stated restraint and listen.
5. **DT-100 pitch correction on real rap** — using Gwapped Up and MoveWrong only; the other
   three are already tuned and would test nothing.
6. **PC-003** — prototype low-band compress-and-restore as a new processor.

Items 2–5 are authored, bounded, reversible parameter changes of exactly the kind DT-98 and
DT-100 already proceeded under. Item 6 is new DSP and deserves its own milestone.

## 9. Verification

- `python -m pytest -q` — **999 passed**, 4 warnings (2026-08-03).
- Working tree contains only this document and `data/practitioner_claims/`. No source file,
  mode contract, or registry entry was modified.
- The CONFLICT-002 experiment built the graph through the public `build_graph` API and
  rendered a deep-copied substitution alongside it; repo code was not patched.

---

## 10. DT-107 — experiments run, and what shipped

Three controlled experiments on Modern Rap / Bold, plus a loudness trace. Sources: the two new
male VocalSet fixtures, one female fixture, and two owner rap takes. **All candidate comparisons
are loudness-matched to −18 LUFS before tonal, dynamic and stereo metrics are read**, so a
candidate cannot win by being louder. That confound invalidated the first presence test in §4.

### Adopted — Experiment 1, variant E

Presence boost moved **3200 Hz → 1700 Hz at the same +2.5 dB**, and the dynamic harshness band
retuned **2000–4500 Hz → 2500–5000 Hz** (threshold_ratio 1.35 → 1.25, max reduction 5 → 6 dB).

Loudness-matched, versus shipped, on every one of the five sources:

| Source | harsh 2.5–5 kHz | presence 1.2–2 kHz | crest |
|---|---|---|---|
| male1_spoken | 2.75 → **1.26** | 2.26 → **3.71** | 14.72 → **14.96** |
| male1_vibrato | 4.66 → **3.18** | 3.95 → **5.74** | 13.42 → **13.95** |
| female1_straight | −1.08 → **−3.58** | 7.67 → **8.62** | 11.63 → **11.80** |
| Gwapped Up (rap) | −4.71 → **−7.22** | 3.21 → **4.33** | 14.89 → **15.46** |
| NotWorthIt (rap) | −3.22 → **−5.48** | 4.43 → **5.64** | 14.08 → **14.51** |

Less harsh energy, more presence, and *higher* crest (less crushed) on all five, with zero
clipped samples and stereo correlation / mono fold-down unchanged. Total boost gain is
identical to shipped, so this is placement rather than more boost.

The chain had been lifting 3.2 kHz statically while dynamically cutting 2–4.5 kHz — boosting
and taming the same band, with the top of the harsh region uncovered. Moving the lift below
the harsh region lets the dynamic stage act on what it is for.

### Rejected — Experiment 2, staged compression

| Variant | Why it lost |
|---|---|
| B: stage 1 → 4:1, 2 ms / 80 ms (PC-008) | Crest *fell* on four of five sources (14.72→14.23, 14.08→13.38). More crushed, which is the opposite of the goal. Harsh-band energy essentially unchanged. |
| C: B + stage 2 → 6:1 (PC-009) | Cost 0.8–1.5 LU on every source (−13.25→−14.36, −13.17→−14.63) for no tonal gain. Worst candidate tested. |
| D: stage 2 → 6:1 at −22 dB threshold | The only interesting one: +1.2 to +1.4 LU with roughly neutral crest. Not adopted because crest moved *down* on two sources (14.72→14.50, 14.08→13.61) and the practitioner prior it derives from (PC-009) is single-source. A level gain bought with uncertain transient cost is not an objectively safe win. Worth revisiting with listening. |

**No compression change shipped.** The practitioner priors on ratio ordering are real
disagreements (§4 CONFLICT-003), but nothing measured here justified acting on them.

### Rejected for now — Experiment 3, doubler width

Narrowing the doubler behaves exactly as intended and is safe, but measurement cannot choose
the setting:

| Variant | correlation | side energy | mono fold-down |
|---|---|---|---|
| A shipped (0.32, ±0.7) | 0.9879 | −22.17 dB | −0.026 dB |
| B (0.22, ±0.55) | 0.9963 | −27.29 dB | −0.008 dB |
| C (0.16, ±0.45) | 0.9986 | −31.44 dB | −0.003 dB |
| D (0.12, ±0.40) | 0.9994 | −34.85 dB | −0.001 dB |

**The shipped doubler is already mono-safe** (−0.026 dB fold-down loss is inaudible), so there
is no safety argument for narrowing — only PC-013's stated restraint, which is one source and a
taste claim. Narrowing also *reduced* crest slightly on three of five sources. Shipping a width
reduction on this evidence would be substituting a measurement for a judgement. **Held for a
listening pass**; renders retained.

### The 3.5 LU deficit — traced

Not the high-pass (already refuted, §4). Rendering with each stage removed:

| Source | full | no parallel | parallel bus costs |
|---|---|---|---|
| male1_spoken | −13.25 | −12.20 | **1.05 LU** |
| male1_vibrato | −12.56 | −9.67 | **2.89 LU** |
| female1_straight | −14.26 | −11.74 | **2.52 LU** |
| Gwapped Up | −13.17 | −12.48 | 0.69 LU |

**The parallel density bus is the dominant cost**, up to 2.9 LU. `Parallel(blend=0.45)`
attenuates the dry path by (1 − blend) and the crushed branch does not restore the lost level.
Removing it also drives true peak from −4.25 to −1.0 dBFS, i.e. straight into the output
ceiling — so the bus is buying density by spending level, and nothing compensates.

A second, separate effect: the doubler contributes **+3.1 LU on mono input** (where it creates
the stereo image) but only **+0.1 LU on stereo input**. Modern Rap's output level therefore
depends on input channel count. Both findings are level-compensation problems, not tuning
problems, and both are candidates for the next milestone. Neither was changed here.
