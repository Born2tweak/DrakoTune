# DT-100 Pitch Correction — Spike Report (DT-98 deliverable)

**Date:** 2026-07-30 · **Status:** feasibility measured, pipeline defined ·
**Evidence:** `scripts/v3_pitch_spike.py`, `output/v3_renders/dt98/pitch_spike.json`
**Class:** design input. No perceptual claim; nothing here is promoted.

DT-100 proposes: contour → key/scale target → correction curve → resynthesis →
formants → Natural/Modern/Hard. This spike ran the stages that can be run with
today's dependencies and measured them, rather than assuming they compose.

**Headline: DT-100 cannot be built from the current primitives.** Two stages fail
on measurement, not on taste. Both need new components with their own gates.

> **Update 2026-07-30 — both components are built (F-19, F-20).** R1
> (`src/dsp_engine/pitch.py`): continuous, no lattice, <5 cents on known tones,
> 0.03x realtime. R2 (`src/dsp_engine/psola.py`): TD-PSOLA, +/-0.4 cents across
> -900..+1200 cents, formants preserved better than `PitchShift` on all three
> fixtures. **Both were blockers; neither is now.** What remains open is not DSP:
> how much correction is right is a listening question inheriting Q-016.
> `PitchShift` stays transposition-only until that is settled.

---

## Stage 1 — Contour: `librosa.pyin` cannot reach correction precision

pyin tracks a sung line perfectly well *as a melody*. It does not resolve pitch
finely enough to *correct* it, and buying that resolution is what breaks.

Tracking quality on rights-clean Tier A fixtures (10 s each, `fmin` 65 Hz,
`fmax` 1000 Hz):

| fixture | voiced | median confidence | octave jumps | cost |
|---|--:|--:|--:|--:|
| vocalset_female1_straight | 83% | 0.89 | 0 | 1.52× realtime |
| vocalset_female1_vibrato | 86% | 0.69 | 0 | 0.57× realtime |
| vocadito_1 | 68% | 0.55 | 0 | 0.47× realtime |

Zero octave jumps across all three — tracking itself is sound.

**The defect appears in precision.** pyin returns f0 on a quantized candidate
grid, so "distance from equal temperament" is the *grid's* offset, not the
singer's intonation. The first run of this spike reported a median deviation of
**20.8 cents and a p90 of 40.8 cents — identical to three decimal places across
three different recordings**, which is what exposed it: all deviations lay on a
lattice ≡ 0.79 cents (mod 10).

Resolution costs, measured on a 2-second excerpt:

| `resolution` | grid | median &#124;cents&#124; | cost |
|---|--:|--:|--:|
| 0.1 (default) | 10.00 c | 29.21 | 0.54× realtime |
| 0.05 | 5.00 c | 29.21 | 2.16× realtime |
| 0.02 | 2.00 c | 28.00 | **19.67× realtime** |
| 0.01 | — | — | **`MemoryError` on 2 seconds** |

Costs are from the committed script; an exploratory first run reported the 0.1
row at 3.77× because it absorbed librosa's warm-up. The shape is what matters and
it is stable: cost is flat down to a 5-cent grid, then rises roughly an order of
magnitude by 2 cents, then fails outright.

At 2-cent resolution a 3-minute vocal costs roughly an hour of CPU for contour
extraction alone (≈20× realtime). At 1 cent the Viterbi decode exhausts memory on a two-second
excerpt — which connects directly to N-012 (memory scaling already recorded as a
real constraint, not a theoretical one).

**Requirement R1.** DT-100 needs a *continuous-valued* f0 estimator — one whose
precision comes from interpolation rather than from enumerating candidates.
Autocorrelation/YIN with parabolic peak interpolation is the obvious deterministic
candidate and stays inside current dependencies. A learned tracker (CREPE and
similar) must clear the component-rights gate in
`02_RESEARCH/G_ENHANCEMENT_AND_ASSESSMENT_MODELS.md` before it is even a
candidate: code licence does not grant weights or training-data rights (E-017).

---

## Stage 2 — Resynthesis: the fixed-interval primitive cannot be reused

`PitchShift` applies **one** interval to a whole buffer. A correction curve is
per-frame. The only way to approximate one with the other is to slice the signal,
shift each slice, and concatenate — so this spike measured exactly that, against
a single-call shift of the same size as the artifact-free reference:

| fixture | blocks (46 ms) | SI-SDR vs uniform shift |
|---|--:|--:|
| vocalset_female1_straight | 218 | **−27.12 dB** |
| vocalset_female1_vibrato | 218 | **−33.66 dB** |
| vocadito_1 | 218 | **−23.68 dB** |

Negative SI-SDR means the block-wise output is *dominated* by boundary artifacts
relative to the correctly-shifted signal. This is not a tuning problem; block
concatenation destroys phase continuity at every boundary.

**Requirement R2.** DT-100 needs a genuine time-varying resynthesis stage —
PSOLA (pitch-synchronous overlap-add) or a phase vocoder with phase-locking.
This is new DSP, not a configuration of what exists.

---

## Stage 3 — Formants: unmeasured, and deliberately so

Formant preservation could not be probed, because there is nothing yet to probe:
it only becomes measurable once R2 exists. Recording it as *unmeasured* rather
than estimating it is the honest position. What is already known from the
registry: `PitchShift` moves formants with the pitch, which is the "chipmunk"
character at large intervals and is inaudible at the ±10 cents doubling uses —
which is precisely why DT-98's doubling is safe and DT-100's correction is not
covered by the same argument.

---

## The pipeline this spike defines

| stage | status | requirement |
|---|---|---|
| 1. contour | **BUILT** (F-19) | R1 delivered: `src/dsp_engine/pitch.py`, YIN + parabolic interpolation, continuous, 0.03x realtime, <5 cents on known tones |
| 2. key/scale target | **BUILT** (F-21) | `src/dsp_engine/correction.py`; snaps across octave boundaries, NaN preserved on unvoiced |
| 3. correction curve | **BUILT** (F-21) | deadband (excess-only), glide in ms, bounded, unvoiced never touched |
| 4. resynthesis | **BUILT** (F-20) | R2 delivered: `src/dsp_engine/psola.py`, TD-PSOLA, +/-0.4 cents accuracy, formants preserved better than the primitive, 0.03-0.05x realtime. Audio *quality* recorded as unmeasured |
| 5. formants | **measured** (F-20) | PSOLA re-spaces rather than resamples: envelope moves 5.45/8.14/2.78 dB vs PitchShift's 12.62/14.35/4.30 |
| 6. Natural/Modern/Hard | **BUILT** (F-21) | measured distinct in KIND: 40c error -> -38.1 / -20.2 / -0.1 cents |

**All six stages now exist** (F-19, F-20, F-21). The prediction that stages 2, 3
and 6 were cheap once 1 and 4 existed held: they were built in one pass, entirely
authored and bounded, with no search and no automated objective — which is why
none of them waited on Q-016.

What remains is **not DSP**. How much correction is *right* is a listening
question, and it inherits Q-016's unresolved problem of what an automated process
may legitimately optimise.

## What this spike does not establish

That correction would sound good; that any retune setting is musically right;
that ±28 cents of measured deviation is *error* rather than expression (vibrato,
scoops and blue notes are all deviation from equal temperament, and a corrector
that flattens them is destroying the performance). A "how much correction" answer
needs listening, and inherits Q-016's unresolved question about what target an
automated process may optimise at all.

## Standing constraints carried into DT-100

- `PitchShift` remains transposition-only until R1 and R2 exist. No surface may
  call the current capability tuning, pitch correction or Auto-Tune.
- Any learned component enters through the rights gate first (E-017, N-010).
- Cost is a first-class acceptance criterion here, not an afterthought: this
  spike's central finding is that the obvious implementation is too expensive to
  ship, and that was only visible because it was measured.
