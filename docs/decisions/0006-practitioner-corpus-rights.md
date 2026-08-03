# 0006 — Practitioner corpus: paraphrase, do not quote

**Date:** 2026-08-03
**Status:** accepted

## Context

25 social-media clips of rap-vocal mixing instruction were supplied as a possible input to
DT-102/DT-103. They split into 9 instructional clips and 16 finished commercial vocals.

ADR 0003 §1 places social-platform captures in **Tier D — `excluded`: allowed nothing.**
Both halves are Tier D on their face.

## Decision

**The 16 commercial vocal clips are rejected outright.** They are unlicensed captures of
copyrighted recordings, and separately they cannot serve DT-102, which is specified as
raw→studio *deltas* and requires pairs that this material does not contain. No measurement
derived from them enters the repository. (Triage established they all sit at ~−13.8 LUFS and
0.0 dBFS true peak — platform normalisation, not engineering intent — so they could never have
served as loudness references either.)

**The 9 instructional clips are retained as paraphrased technical assertions only.** Tier D
governs the *audio and video as data*. What is retained here is not that material: it is a set
of parameter values and process steps, which are facts and not protected expression. The
creator's specific wording is protected, so it is removed.

Concretely, `data/practitioner_claims/mixing_corpus_claims.json` keeps clip id, timecode,
creator attribution, and a paraphrase of each technical assertion. It holds no verbatim
transcript. No source audio, video, or frame is stored anywhere in the repository, and none
may be shipped in the product. 26 verbatim quotations were removed on 2026-08-03.

## Consequences

- Every claim stays traceable to a source and creator without reproducing their expression.
- Evidence class is unchanged and remains **PRIOR**: nine clips of practitioner opinion.
  Nothing here may support a product claim, and none of it is evidence of perceptual
  improvement. It may inform an engineering default, which is the same latitude ADR 0003 §1
  grants Tier B.
- Where a practitioner prior motivates a parameter change, the change must still be justified
  by measurement and listening in this repository. The prior selects what to test; it never
  settles the result.

## Rejected alternative

Deleting the extracted claims entirely. Rejected because the technical assertions are facts,
the rights concern attaches to expression and to the media, and both are now removed. Discarding
the analysis would lose the one outside reference the authored mode constants have ever had.
