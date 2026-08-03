# Video-derived vocal chains — implementation specifications (DT-108)

**Date:** 2026-08-03
**Source:** 25 clips in the supplied `Mixing` folder. All 25 were transcribed from source
audio with `faster-whisper small.en` (segment timestamps) and frame-sampled at 1 fps.
**Classification, re-derived independently:** 9 instructional, 16 music-only. Music-only
clips contain no instruction and are excluded from everything below.

## Evidence tags used throughout

| Tag | Meaning |
|---|---|
| **VISIBLE** | Read directly off a plugin interface in an extracted frame |
| **STATED** | Spoken by the creator in the transcribed narration |
| **INFERRED** | Deduced from interface context, not shown as a number |
| **APPROX** | A DrakoTune stand-in for a proprietary plugin's *function* |
| **UNKNOWN** | Not readable and not stated — left at a DrakoTune default, never invented |

## Method limit, stated plainly

I cannot hear audio. Narration was transcribed by ASR and frames were read visually.
**No before/after audio demonstrated in any video was perceptually evaluated**, because I
cannot listen to it. Where a creator says a stage fixes something, that is recorded as their
claim, not as a verified result. Nothing in this document is a perceptual finding.

Rights: per ADR 0006 the source clips are Tier D. No transcript, frame, or audio from them is
committed. What follows is parameter facts and paraphrase only.

---

## The corpus contradicts itself. That is the main finding.

Two creators give directly opposing instructions on the two parameters that matter most:

| | @angelomota (170352) | @leteveon_ (170615) |
|---|---|---|
| 2.5–5 kHz | **cuts** it | — |
| 3.2 kHz | avoided; boosts at 1.2k/1.7k/8k instead | **boosts** it, plus 6.4 kHz |
| High-pass | **80 Hz** ("cuz I got a low voice") | **90 Hz**, alt caption "115 instead" |

**This corrects an earlier claim of mine.** I previously wrote that Modern Rap's 105 Hz
high-pass "sits above every stated value" in the corpus. That was wrong: 170615's on-screen
caption offers 115 Hz. The corpus is not unanimous, and 105 Hz is inside its range.

Per instruction, these are **not averaged**. Each creator is implemented as its own mode.

---

## Spec 1 — `challenger_angelomota` (clip 170352, @angelomota, 114.8 s)

**Context:** answering "what's the vocal chain", own voice, described as low. Rap.
**Routing:** fully serial into two effect sends. No parallel bus shown.

| # | Plugin (VISIBLE) | Function | Settings | Evidence |
|---|---|---|---|---|
| 1 | Ableton Gate | remove dead noise | Threshold −52.0 dB, Attack 9.54 ms, Hold 10.0 ms, Release 145 ms, Floor −40.0 dB, Lookahead 1.5 ms, Return 3.00 dB | **VISIBLE** (all) |
| 2 | FabFilter Pro-Q 3 | subtractive EQ | HPF ~80 Hz; dip 200–500; dip 1 kHz; cut 2.5–5 kHz | STATED; curve shape VISIBLE, exact gains UNKNOWN |
| 3 | FabFilter Pro-C 2 | peak control | 2 ms attack, 80 ms release, 4:1, ~6 dB GR; style **Clean**, mono, oversampling off, auto-gain + auto-release on | numbers STATED, style/mode VISIBLE, threshold INFERRED |
| 4 | Waves API 2500 | levelling | 6:1, quick attack, ~−6 dB GR | STATED; knobs VISIBLE but not legible |
| 5 | FabFilter Pro-Q 3 | additive EQ | boosts at 1700, 1.2k, 8k; optional low boost | STATED; gains UNKNOWN |
| 6 | Empirical Labs Distressor | harmonic compression | 6:1, ~4 dB GR | STATED |
| 7 | Slate Fresh Air | HF excitement | knobs read **18** and **24** | **VISIBLE** |
| 8 | Output Thermal | saturation | width + heat used; drive turned down; dry/wet adjusted | STATED, values UNKNOWN |
| 9 | Polyverse Wider | stereo width | **10%** | **VISIBLE** + STATED |
| 10 | FabFilter Timeless 2 | delay | UNKNOWN | STATED only |
| 11 | reverb (name unclear on ASR) | space | UNKNOWN | STATED only |

**Reproduced exactly:** gate settings; chain order; compression ratios; boost/cut frequencies.
**Approximated:** Distressor → `Compressor` + `Saturation` (no program-dependent detector);
Fresh Air → 12 kHz high shelf (**a shelf lifts existing HF; Fresh Air synthesises new HF —
these are not the same process**); Thermal → blended `Saturation` (no multiband wavefolder);
Polyverse Wider → very low-level `Doubler` (**a widener manipulates phase/delay of one signal;
a doubler adds detuned copies — audibly different**).
**Cannot reproduce:** true spectral excitation, Distressor's detector behaviour, Timeless 2's
filtered/modulated delay character.

---

## Spec 2 — `challenger_leteveon` (clip 170615, @leteveon_, 49.2 s)

**Context:** "how to mix underground vocals". Narration says "use this" throughout, so almost
all identification here is from on-screen captions in frames, not from speech.
**Routing:** serial, plus an instruction to bus the vocal chain to a pre-master bus.

| # | Plugin (VISIBLE) | Function | Settings | Evidence |
|---|---|---|---|---|
| 1 | Noise Gate | gate | caption: "use as 1st effect in your preset" | **VISIBLE** caption |
| 2 | Autotune Artist / Waves Tune | pitch | BandLab **80%**; "no humanize"; on-screen **4237**; Auto Key shown | STATED + **VISIBLE** |
| 3 | FabFilter Pro-Q4 / EZ EQ | high-pass | caption: "**cut at 90** and adjust later"; alt "**high pass at 115** instead" | **VISIBLE** captions |
| 4 | RComp / Digi Comp | light compression | "very lightly just to grab the peaks"; caption warns it may be the only compressor on BandLab | STATED + caption |
| 5 | DeEsser | de-essing | wideband, **mix ~60%**; plugin threshold **−2.4 dB** | STATED + **VISIBLE** |
| 6 | Graphic EQ | tone | **"boost 3.2k & 6.4k"**; 100 Hz −3.6 dB visible | **VISIBLE** caption |
| 7 | EQ | air | "clean up 10–15 kHz", then "high shelf starting around **10k**" | STATED + **VISIBLE** |
| 8 | H-Delay / D-Delay | delay | time readout ~0.353 s | **VISIBLE**, low confidence |
| 9 | Valhalla VintageVerb / Studio Reverb | space | mix ~31 | **VISIBLE**, low confidence |
| 10 | stereo widener | width | UNKNOWN | STATED |
| 11 | Aphex Exciter | excitement | Tune / Harmonics knobs shown, values UNKNOWN | **VISIBLE** plugin |
| — | Soothe2 | resonance | caption: put on a pre-master bus, not the vocal | **VISIBLE** caption |

**Reproduced exactly:** gate-first order; 90 Hz high-pass; 3.2k and 6.4k boosts; 10–15 kHz
cleanup then 10 kHz shelf; wideband de-essing.
**Approximated:** Aphex Exciter → `Saturation`; widener → low-level `Doubler`.
**Cannot reproduce:** pitch correction is deliberately **omitted** — this chain's defining move
is a hard autotune, and no DrakoTune mode surfaces pitch correction. **This mode is therefore
materially incomplete relative to the video.** Soothe2's dynamic resonance suppression on a bus
is also out of scope (`ResonanceSuppressor` is per-track and static in comparison).

---

## Spec 3 — `challenger_mixedbytra` (clip 170828, @mixedbytra, 71.5 s)

**Context:** lead vocal chain for YNW Melly, "772 Love pt. 2". Named commercial record.
**Routing:** serial channel strip, **plus a parallel duplicate track visible in the mixer that
the narration never mentions** (`PARA.dup1`, carrying a Fairchild 670 and a reverb).

| # | Plugin | Function | Settings | Evidence |
|---|---|---|---|---|
| 1 | Metric Halo ChannelStrip EQ | remove mud | HPF + low-mid dips; curve VISIBLE, values UNKNOWN | STATED + curve VISIBLE |
| 2 | UAD SSL E Series | tone | UNKNOWN | STATED + plugin VISIBLE |
| 3 | Waves R-COMP | compression | **Thresh −19.7, Ratio 3.79:1, Gain +2.4, Output −11.7** | **VISIBLE — the only fully legible compressor in the corpus** |
| 4 | de-esser | sibilance | UNKNOWN | STATED |
| 5 | UAD Pultec EQP-1A | tone | "smiley face" = simultaneous low and high boost | STATED + VISIBLE |
| — | `PARA.dup1` | parallel density | Fairchild 670 + reverb, sends at ~−17.1 | **VISIBLE in mixer, never narrated** |

**Reproduced exactly:** R-COMP threshold, ratio and makeup gain; chain order; Pultec smiley as
a low-shelf + high-shelf pair.
**Approximated:** Fairchild 670 → `Compressor` + `Saturation` in a `Parallel` branch.
**Cannot reproduce:** Pultec's simultaneous boost-and-attenuate interaction on the same band
(the reason a real Pultec low boost sounds the way it does), SSL E Series curves (unreadable),
variable-mu detector behaviour.

---

## Specs 4–9 — the remaining instructional clips

These carry **no per-plugin settings to extract**; they are conceptual or product content. All
were transcribed and frame-checked; none yielded a reconstructable chain, so none became a mode.

| Clip | Creator | Content | Why no chain |
|---|---|---|---|
| 170750 | — | recording → 2 compressors → de-ess → fast autotune → EQ → saturation → delay → reverb | Order STATED, **every value UNKNOWN**; no plugin UI shown |
| 171211 | — | Cardi-style multiband: HPF 80, compress 120–200 Hz, boost that band back | Technique STATED; **DrakoTune has no compress-and-restore band processor** (see PC-003) |
| 170107 | — | what parallel compression is; ~10:1, blend under dry | Concept only; already implemented in Modern Rap |
| 170235 | — | plugin order: EQ → pitch → comp → EQ → saturation → reverb on a return | Order only, no values |
| 170527 | — | eight-step mix process; "cut first, add later"; reference in mono | Process advice, not a chain |
| 170556 | — | five free plugin recommendations | Product recommendations, no technique |

---

## Status

These three modes are **experimental challengers**. They are registered in `MODES` and
therefore reachable through every product surface, but **Modern Rap is unchanged and remains
the default**. No challenger may be promoted on measurement alone — that is precisely the error
N-016..N-022 identified. Promotion requires listening.
