# Q-016 — What may an automated search optimise against a wet reference?

**As of:** 2026-07-26. Decision authority: research lead + audio lead (Q-016).
**Status: nothing selected.** This assembles the evidence a decision needs; it does
not make one, and no candidate here is promoted.

**Sources:** the repository's registered ones only —
`AURELIAN/02_RESEARCH/C_AUDIO_QUALITY_AND_LISTENING_STANDARDS.md` (S-E01…S-E07),
`G_ENHANCEMENT_AND_ASSESSMENT_MODELS.md` (S-C01…S-C04, S-E05, S-E06), N-011,
N-018, N-019, N-020.

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

| candidate | what it adds | audit outcome (4 pairs) |
|---|---|---|
| `composite_v1` (in use) | 3 band ratios, crest, tilt | auditable; 1 admitted pathology outscored the reference (a `Limiter` at its bound, 1 of 4 pairs) |
| `mfcc_l1` | spectral-envelope shape, c0 dropped | auditable on 3 of 4 pairs; 2 pathologies outscored the reference |
| `logmel_l1` | frequency-resolved band differences | **untestable on every pair** — reference loses to no-op (N-020) |
| `mrstft_log` | multiple time/frequency resolutions | **untestable on every pair** — same cause |

Every one of the four fails `CONSTRAINT_ADMITS_HONEST`: the 12 dB SI-SDR floor
rejects a defensible −4 dB low-mid cut with gentle compression (N-019). So every
gap-closure number measured under it is a lower bound.

## 4. What a decision needs that does not exist yet

1. **A metric-independent honest reference.** N-020's blocker. Options: per-pair
   references defended by an engineer against each metric; or surrogates whose
   degradation is fully invertible by the registry (the current one contains a room
   comb that is not), so "the best an admissible chain can do" is well defined.
2. **A preservation constraint that admits honest work.** N-019. The current floor
   is simultaneously too permissive (admits compression, gating, shelving) and too
   strict (rejects a professional low-mid cut). A floor on waveform correlation is
   the wrong instrument for both jobs.
3. **Listening data.** DEF-003. `PERCEPTUAL_ALIGNMENT` is permanently UNTESTABLE
   until it exists, so **no objective in this repository can be certified for
   production**, by construction. That is the honest state, not a gap to be
   engineered around.

## 5. Recommendation to the decision-makers

Do **not** select an objective yet. The two blockers in §4.1 and §4.2 are ordinary
engineering and can be cleared without a human decision; §4.3 cannot. Until then
`composite_v1` keeps its **diagnostic-only** status by default rather than by
merit, every number measured with it is a lower bound, and no DSP change may be
promoted on the strength of it.

If one metric is to be pursued for registration, the registered evidence points to
**ViSQOL** — full-reference, permissively licensed, and the only candidate whose
construct is close to "how audible is the difference between my rendering and the
professional one". Registering it means pinning an implementation, validating the
alignment policy, and calibrating on singing vocals first (S-E06's own conditions),
and it introduces a dependency the SBOM-parity gate must accept. That is a decision
with cost, so it is put here rather than taken.
