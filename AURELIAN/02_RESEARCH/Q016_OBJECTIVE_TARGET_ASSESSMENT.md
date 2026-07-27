# Q-016 — What may an automated search optimise against a wet reference?

**As of:** 2026-07-26. Decision authority: research lead + audio lead (Q-016).
**Status: nothing selected.** This assembles the evidence a decision needs; it does
not make one, and no candidate here is promoted.

**Sources:** the repository's registered ones only —
`AURELIAN/02_RESEARCH/C_AUDIO_QUALITY_AND_LISTENING_STANDARDS.md` (S-E01…S-E07),
`G_ENHANCEMENT_AND_ASSESSMENT_MODELS.md` (S-C01…S-C04, S-E05, S-E06), N-011,
N-018, N-019, N-020, N-021, N-022.

## 1. The question is narrower than "which perceptual metric"

N-019 narrowed it. The preservation guards are not what protect the search — SI-SDR
is scale-invariant and correlation-based, so a 20:1 compressor, an above-floor gate
and a +12 dB shelf all *score well* on it. The admissible bounds do the protecting.
So the question is not "which floor" but **what a target must measure that a
correlation-preserving distance cannot**.

N-020 narrowed it again, from the other side: candidate targets cannot even be
compared without a reference that is defensible in each candidate's own terms.

## 2. Off-the-shelf metrics: what the registered sources already establish

| Metric | Registered? | Construct | Disposition for THIS use |
|---|---|---|---|
| PEAQ (S-E05, ITU-R BS.1387-2) | yes | full-reference perceptual impairment, device/codec domain | **Not applicable as the oracle target.** C-report: a creative dry→wet transformation violates the implied device-under-test comparison. Codec-like fixtures only. |
| ViSQOL (S-E06) | yes | full-reference speech/audio similarity, Apache-2.0 | **Closest legitimate candidate**, and still gated: requires a legitimate reference, pinned implementation and singing-vocal calibration before it may be registered as a metric card. |
| NISQA (S-C04) | yes | no-reference speech-communications MOS | **Rejected as a production criterion** — weights are CC BY-NC-SA 4.0 and the construct is communications speech. Observation only. |
| DNSMOS, PESQ, STOI, HASQI, PEMO-Q | **no** | — | **Not assessed.** No registered source exists, so this document asserts nothing about their licences, domains or suitability. Registering a source is the prerequisite, not a formality. |

The unifying constraint is N-011: speech-enhancement or communications success is
not vocal-mixing validity. Every metric above was built to answer "how damaged is
this copy of a known signal", and DrakoTune's task is "how close is this treatment
to a different, professional rendering of the same performance".

## 3. Repository-internal candidates (built, audited, none selected)

`src/paired_corpus/objectives.py`. All level-invariant by per-phrase RMS
normalisation, which closes loudness inflation by construction rather than by a
guard — the registry permits +12 dB of clean gain, and a metric that can be
improved by turning it up will be.

| candidate | what it adds | on ground truth (invertible pairs) | on noisy surrogates |
|---|---|---|---|
| `composite_v1` (in use) | 3 band ratios, crest, tilt | recovers the exact inverse; **0 of 147** pathologies beat it | beaten once (a `Limiter` at its bound) |
| `mfcc_l1` | spectral-envelope shape, c0 dropped | same | beaten once (same `Limiter`) |
| `logmel_l1` | frequency-resolved band differences | same | clean; auditable only after log-magnitudes were floored (N-021) |
| `mrstft_log` | multiple time/frequency resolutions | same | reference still loses to no-op, so **untestable** there |

Two things follow. Under the **current** SI-SDR constraint all four fail
`CONSTRAINT_ADMITS_HONEST`, so every gap-closure number measured under it is a lower
bound (N-019, N-021). Under the **candidate** constraint (N-022) all four are
structurally sound on ground truth — and gaming resistance then does not
discriminate between them at all, so it cannot be the basis for choosing one.

## 4. What a decision needs that does not exist yet

1. ~~**A metric-independent honest reference.**~~ **Cleared (N-021):**
   `make_invertible_pair` builds a surrogate whose degradation is three registry
   filters, so the exact inverse is inside the admissible space and provably
   optimal. All four candidates recover it. With a reference that cannot be blamed,
   **none of the 147 admitted pathologies beats it under any candidate** — so
   gaming resistance does not discriminate between them, and selection still cannot
   be made on this evidence.
2. **A preservation constraint that admits honest work.** N-019 said the current
   floor is both too permissive (admits compression, gating, shelving) and too
   strict (rejects a professional low-mid cut). **N-021 shows it is worse than
   mis-tuned: it is anti-correlated with correctness.** SI-SDR is measured against
   the RAW, and the better a treatment corrects the raw the further from the raw it
   is — so the exact inverse, 92 dB from the target, is rejected on every seed. No
   value of the threshold fixes a constraint pointing the wrong way; it needs to be
   measured against the performance content that must survive, not against the
   untreated input. **Candidate replacement built and evidenced (N-022):**
   `src/paired_corpus/preservation.py` measures voiced-frame retention plus the
   existing crest/ceiling/clipping guards. It admits the exact inverse on all four
   seeds and admits honest treatments the floor rejects, while rejecting the gating
   the floor admitted at 43 dB SI-SDR; pitch-contour correlation was measured and
   REJECTED as a component (1.000 for a 20:1 compressor). With it in place all four
   candidate objectives are structurally sound on ground truth. **Not wired in:**
   swapping the admissibility rule changes every number the corpus has produced, so
   it is put to this decision rather than taken.
3. **Listening data.** DEF-003. Unchanged by any of the above and not engineerable. `PERCEPTUAL_ALIGNMENT` is permanently UNTESTABLE
   until it exists, so **no objective in this repository can be certified for
   production**, by construction. That is the honest state, not a gap to be
   engineered around.

## 5. Recommendation to the decision-makers

Do **not** select an objective yet — but the reason has changed. §4.1 and §4.2 were
ordinary engineering and both now have evidenced answers; §4.3 does not and cannot
be engineered around. What remains is a decision with two parts:

1. **Adopt or reject the candidate preservation constraint (N-022).** Adopting it
   changes every number the corpus has produced — F-9's +32.8% included, since that
   figure was measured under a constraint that rejects correct answers. That is a
   re-measurement, not a refactor, and it needs sign-off.
2. **Choose whether to pursue ViSQOL registration** (below), which is the only path
   here that moves toward perceptual grounding without listening data.

Until both are settled `composite_v1` keeps its **diagnostic-only** status by
default rather than by merit, every number measured with it is a lower bound, and no
DSP change may be promoted on the strength of it.

If one metric is to be pursued for registration, the registered evidence points to
**ViSQOL** — full-reference, permissively licensed, and the only candidate whose
construct is close to "how audible is the difference between my rendering and the
professional one". Registering it means pinning an implementation, validating the
alignment policy, and calibrating on singing vocals first (S-E06's own conditions),
and it introduces a dependency the SBOM-parity gate must accept. That is a decision
with cost, so it is put here rather than taken.
