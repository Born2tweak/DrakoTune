# Negative Results and Invalidated Assumptions

These results are retained to prevent repetition and survivorship bias.

## N-001 — Objective pass did not imply globally better audio

On the repository’s `harsh.wav` fixture, the v2 pipeline met two target-movement objectives while reporting residual harshness/noise, a +0.0074 rise in sibilant-frame p95, a +5.2135 rise in mud ratio, and -1.2 LU loudness change. Conclusion: target metric movement alone is not a quality verdict.

## N-002 — One listener can satisfy the former sample gate

Eight duplicate rows from one listener on one harshness trial were counted as `n=8` and produced `p=0.0039`, passing the former gate. Conclusion: row count is not independent sample size.

## N-003 — Clean-vocal harm can pass

Eight distinct listeners preferring the original clean vocal over the processed version yielded a processed-preference rate of 0.0 and passed the former do-no-harm rule. Conclusion: “processed not preferred” is not equivalent to “no harm.”

## N-004 — Ties disappear from defect evidence

Unanimous ties omitted a defect result, produced a clean processed-preference rate of 0.0, passed do-no-harm, and yielded agreement 1.0. Conclusion: ties must be modeled and reported explicitly.

## N-005 — Panel disagreement is hidden

Experts unanimously preferring original and general listeners unanimously preferring processed collapsed to a 50% aggregate without a panel interaction result. Conclusion: panel strata cannot be pooled without a prespecified estimand.

## N-006 — Side/order bias is not detected

All respondents choosing side A can pass when processed audio is always assigned to A. Conclusion: assignment balancing and side/order diagnostics are mandatory.

## N-007 — Synthetic benchmark performance is not uniformly positive

Current corpus-v2 benchmark cells include mixed or negative SI-SDR changes and six errored pairs. Conclusion: do not summarize the corpus with a blanket improvement claim.

## N-008 — Synthetic calibration exhibits large false-positive rates

Recorded calibration examples include reverb 41.2%, hum 21.2%, and noise 22.5% false-positive rates. Conclusion: detector thresholds are not launch-calibrated.

## N-009 — Informal owner listening is not independent validation

Existing informal listener records are useful product discovery only. They cannot establish professional preference, target-user benefit, or do-no-harm.

## N-010 — Public availability does not establish usable rights

MedleyDB and much of MUSDB are non-commercial; Cambridge downloads are offered for practice under per-track/term constraints; research code licenses do not grant dataset or model-weight rights. Conclusion: use-purpose rights must be recorded separately.

## N-011 — Speech-enhancement success is not vocal-mixing validity

DeepFilterNet, RNNoise, ViSQOL, NISQA, and related tools target speech/noise or communications domains. Conclusion: they remain candidates only after singing-vocal applicability tests.

## N-012 — Current memory design does not scale comfortably

Historical performance evidence indicates linear memory near 180 MB per audio minute and around 900 MB for five minutes, with two MemoryErrors recorded. Conclusion: desktop scope needs duration limits or streaming/chunking.

## N-013 — Exact environment cannot be reconstructed from project metadata

Dependencies have lower bounds but no lockfile; FFmpeg build options are external. Conclusion: software version plus build/license fingerprint must be evidence metadata.

## Supersession note — N-002..N-006 structurally defended by DT-56 (2026-07-23)

The five listening-analysis exploits above are now rejected or surfaced by the
immutable listening schema (`src/listening/`, `tests/test_listening_protocol.py`):
independent-listener counting (N-002), explicit original-preference (N-003) and
tie (N-004) categories, non-pooled panel breakdown (N-005), and blinded
assignment + side/order diagnostics (N-006). The exploits remain recorded here as
the design rationale; the legacy M24 analyzer that produced them is superseded and
its data stays quarantined/exploratory.

## N-015 — The champion abstains on real rap acapella (engagement gap, not DSP-quality)

2026-07-24 paired-corpus gap analysis (D-029; `reports/evaluations/paired-corpus/FINDINGS.md`, DT-55D). On 7 of 9 processable real rap-acapella raw/wet pairs (lossy MP3, single dominant artist) the current champion applied **0 processing actions**; the diagnosis measured heavy low-mid boxiness (`mud_ratio` 6.6), an audible noise floor (−44.5 dBFS), a dark centroid (2622 Hz), and sub-floor sibilance (p95 0.095 < 0.10 de-ess floor) yet the only objective raised (`reduce_noise`) fired at confidence 0.22 and was marked `report_only`. Conclusion: the owner-perceived quality gap ("subtle improvement, still boxy/unclear/weak-mic/fatiguing", E-OWN-001) is primarily a **decision-engine engagement/calibration** problem — thresholds tuned on synthetic degradations + clean studio singing under-fire on real home-recorded rap — **not** a DSP-quality problem. You cannot perceive a chain that never runs. Highest-leverage fix = DT-77 brief B-1 (recalibrate engagement on real rap-acapella feature distributions, on artist-held-out splits, predeclared). Directional only; no perceptual claim; does not satisfy DEF-003.

> **Partially superseded by N-016 (2026-07-25).** The *measurement* above stands (86% abstention, confirmed by the oracle run). The *inference* — "therefore engagement is the dominant bottleneck", "primarily a decision-engine problem, not a DSP-quality problem" — was too strong: forcing the existing chain to engage across its full safe range closed ≥10% of the gap on only 2 of 7 valid pairs. Engagement recalibration is necessary but not sufficient. Read N-016 before acting on this entry, and see the renumbered DT-77 tracks (the brief formerly called B-1 is now **A-1**).

## N-014 — Blanket in-range de-essing is net-harmful; the champion's abstention is correct

2026-07-23 reconciliation experiment (`scripts/experiments/exp_2026_07_23_sibilance_deesser.py`, contract + `results.json` under `reports/evaluations/reconcile-2026-07-23/`). Applying the DeEsser at its most aggressive **in-range** setting (`frame_threshold=0.10`, `max_reduction_db=10`) to every champion output reduced the sibilance defect band by 26.1% on the 12 sibilance pairs (passed the predeclared ≥20% bar) but **failed do-no-harm**: SI-SDR regressed on 22/148 non-sibilant clips (median −8.6 dB, worst −42 dB; concentrated in low_level ×12, harshness ×4, codec ×4), and because the treatment ran *after* the executor's −0.2 dBFS ceiling it pushed peaks above unity on hard-clipped inputs (vocadito_16: 0.977 → 1.117) and increased clipping on that clip. Conclusion: the champion's decision-gated abstention from de-essing is **vindicated** — a blanket de-ess trades a small sibilance gain for large fidelity loss and a safety-ceiling breach. Any real sibilance improvement must be (1) gated on reliable per-clip sibilance detection (never applied to low_level/codec/harshness), (2) executed **inside** the output-safety envelope (re-apply the ceiling), and (3) preceded by a separately-validated lowering of the de-ess frame floor, since synthetic sibilance p95 (~0.088) sits below the current 0.10 floor. Verdict: **rejected**; logged as the DT-77 improvement brief seed.

## N-016 — Forcing the existing chain to engage does NOT close the gap on most pairs (N-015's inference was too strong)

2026-07-25 DT-55E oracle sweep (D-029; `reports/evaluations/paired-corpus/FINDINGS.md` F-4/F-5/F-6). N-015 measured that the champion abstains (confirmed: **86% abstention** across valid pairs) and *inferred* that engagement was therefore the dominant bottleneck. The oracle tested that inference by forcing the planner's own treatments to run and sweeping them across the registry's entire safe strength range (3 chains × 5 strengths = 15 candidates per pair), measuring composite distance to the aligned wet target.

**Result: the inference does not hold.** Of 7 valid pairs (2 excluded as `inconclusive_alignment` — 0 measurable phrases), only **2** reached the `engagement_gap` bar (≥10% of the distance closed), 1 landed in the unattributable 2–10% band, and **4** were `missing_processor` (≤2%, two of them monotonically *worse* under any amount of treatment). Median improvement **+0.67%**; mean **+7.05%** with a bootstrap 95% CI of **−3.00% .. +20.45%** — the CI spans zero, so **no aggregate effect is established**.

Two secondary results, both from monotone (therefore non-noise) distance-vs-strength curves:
- **The safe parameter range is binding where the treatment works.** All three pairs that improved were still improving at maximum strength (edge slopes −0.091 / −0.023 / −0.108). At strength 1.0 the muddiness treatment is only a −4.0 dB PeakFilter at 300 Hz. This is a parameter-range limit, not a missing processor — and it was **invisible** at the single fixed strength (0.7) the first probe used.
- **On the other four pairs the existing treatment is the wrong direction** (edge slopes +0.009 … +0.268): the registry offers subtractive low-mid/harshness filtering plus a fixed-threshold gate, and those wet targets do not want subtraction.

Conclusion: the bottleneck is **mixed**, roughly evenly split, and DT-77 priority follows measured per-pair impact rather than the aggregate. Engagement recalibration (A-1) is **necessary but not sufficient** and must be paired with the range question (A-2). New DSP capability (Track B) is now *measurably* necessary for ~4/7 pairs but is **not yet identified**, and the `missing_processor` verdict is provisional: it means "no *searched* configuration got closer", and the NoiseGate spec is strength-invariant so denoising was tested at exactly one threshold. Method gaps (Track C) gate any final Track B verdict. Directional only; no perceptual claim; does not satisfy DEF-003.

> **Superseded in part by N-017 (2026-07-26).** The `missing_processor` verdicts below do NOT hold: they were produced by searching the *planner's* strength mapping rather than the *registry's* declared safe ranges. Under the registry-safe search every one of those pairs closes 20.9–57.8% of the gap, so no missing-capability claim survives and **Track B (new DSP research) is withdrawn**. What still stands from this entry: the 86% abstention measurement, the four-category taxonomy, the range-binding observation (now understood as a *planner spec* cap, not a registry limit), and the F-6 direction observation (also a planner-spec property — the registry can boost).

**Process lesson:** the same probe, run at one fixed parameter point, produced a different taxonomy (1 engagement / 4 missing / 2 data-limited) than the swept probe. A single-point oracle cannot distinguish "the registry lacks the capability" from "the registry was not asked hard enough". Never classify a capability as missing from one operating point.

**Tooling defect fixed alongside:** the first classifier attributed pairs with **zero** measurable aligned phrases (infinite distance) to a tuning gap — absence of evidence acting as evidence. Now gated to `inconclusive_alignment` and excluded from every aggregate (`src/paired_corpus/oracle.py`, `tests/test_oracle_probe.py`, 29 tests covering every classification path and both boundaries).

## N-017 — The `missing_processor` verdicts were an artifact of the search space, not evidence of missing capability

2026-07-26 DT-55E Track C (`src/paired_corpus/search.py`; run `20260725-102806-search`). N-016 concluded that 4 of 7 valid pairs were `missing_processor` — "the existing registry cannot get closer at any allowed setting" — and that new DSP capability was therefore *measurably necessary*. **That conclusion was wrong, and the cause was the search space.**

Both earlier probes searched the **planner's strength mapping**, not the **processor registry**. The planner's muddiness treatment caps at a −4.0 dB PeakFilter at strength 1.0; `PROCESSORS["PeakFilter"]` declares a safe range of **−12..+12 dB**. The registry also permits *boosting*, so N-016's F-6 claim that "the registry offers only subtractive treatments" described the planner's specs, not the processors available to it.

Running the search DT-55E actually specifies — deterministic coordinate descent inside `PROCESSORS.safe_ranges`, `clamp_params` enforced, −0.2 dBFS ceiling, zero clipping, and an SI-SDR ≥ 5 dB preservation floor against the raw — every one of those four pairs moved:

| pair | N-016 strength sweep | registry-safe search | smallest sufficient chain |
|---|--:|--:|---|
| P-01 | +43.5% | **+62.1%** | t5_full |
| P-02 | +0.3% (missing_processor) | **+20.9%** | t5_full |
| P-05 | −5.6% (missing_processor) | **+57.8%** | t5_full |
| P-06 | +8.4% | **+56.3%** | t5_full |
| P-07 | −8.8% (missing_processor) | **+33.7%** | t5_full |
| P-09 | +0.7% (missing_processor) | **+45.2%** | t3_tonal_air |

Median distance closed vs the champion **+50.7%**, mean **+46.0%**, bootstrap 95% CI **+33.5% .. +56.9%** — the CI **excludes zero**, where N-016's aggregate CI spanned it.

Conclusions:
1. **No `missing_processor` verdict survives.** The existing registry closes a large fraction of the measured champion→wet gap on every searchable pair. **Track B (new DSP research) is not justified by current evidence** and is withdrawn from the near-term queue.
2. **The bottleneck is the planner, not the DSP.** Two planner-level properties account for the whole measured gap: which processors it engages (N-015: 86% abstention) and how much its issue specs permit (this entry). Both are Track A.
3. 5 of 6 pairs needed the full chain (tonal EQ + air + gate + compressor); 1 needed only tonal + air. Dynamics processing is implicated, consistent with `docs/research/underground_vocal_engineering_reference.md` on dynamic consistency.

**Process lesson (second instance of the same error).** N-016 already recorded "never classify a capability as missing from one operating point". The deeper rule: **a negative capability claim is only as strong as the space searched, and the space must be the one the component actually declares.** Both prior probes measured a *proxy* for the registry (the planner's mapping) and reported the proxy's limits as the registry's.

Standing limits unchanged: diagnostic only; distance is not perceptual quality; lossy single-artist corpus; does not satisfy DEF-003; promotion of any audible DSP change remains a human-only gate.

**Evidence provenance caveat:** the detailed per-template artifacts of run `20260725-102806-search` were lost when the process was stopped (it wrote its JSON only at completion, and the machine's sleep cycles had stretched it past 12 h wall on one pair). The per-pair numbers above are from that run's captured stdout. The runner now checkpoints each pair to `partial_results.jsonl`; a re-run regenerates the full reproducible artifact.

## N-018 — The oracle's composite distance is gameable; N-017's gap-closure numbers do not represent recoverable quality

2026-07-26, run `20260726-061954-search` (per-template detail; the earlier run reported only summary lines). N-017 reported that the registry-safe search closes 20.9–57.8% of the champion→wet distance and concluded that the bottleneck is the planner rather than the DSP. **The per-template parameters show the objective is being gamed, and that conclusion does not follow.**

The winning chain on the best-aligned pair (P-01, +62.1%):

| slot | chosen | why it is not a quality solution |
|---|---|---|
| `HighpassFilter` | **330 Hz** (t1–t4), 240 Hz (t5) | removes the entire chest/body region of a rap vocal; inside the registry's 20–500 Hz safe range but destructive by any professional standard |
| low-mid `PeakFilter` | **0.0 dB — unused** | the search never used the treatment the whole low-mid hypothesis is about; it got its low-mid reduction from the brutal highpass instead |
| mid `PeakFilter` | +6.0 dB @ 8.5 kHz, Q 2.4 | a narrow high-frequency boost, not the 2.5–5 kHz resonance control the defect model predicts |
| `NoiseGate` | **−15.75 dB** | far above any sane vocal gate; would chop word tails and breaths |
| `Compressor` | **ratio 20.0 — at the maximum bound**, threshold −10.5 | crushes crest; `docs/research/underground_vocal_engineering_reference.md` puts the professional range at 3:1–4:1 |
| SI-SDR | **5.4–6.6 dB** | barely above the 5 dB floor — the preservation floor was the *binding* constraint, i.e. it is set far too low to prevent destruction |

The ablation makes the mechanism explicit: t1 = t2 = t3 = **1.747** (adding a mid bell and an air shelf bought *nothing*), t4 = 1.713 (gate), t5 = **1.074**. Essentially all of the headline improvement came from a maximum-ratio compressor plus an aggressive highpass — the two cheapest ways to move `crest_db` and `tilt_db_per_oct`, which are 2 of the composite's 5 axes.

**What is retracted:** N-017's inference that ~46% of the champion→wet *quality* gap is recoverable with existing processors, and that the planner's specs are what withhold it. A steep highpass and a 20:1 compressor are not what the planner's specs are missing.

**What still stands:** the narrow, literal statement that the registry can *reduce the composite distance* substantially — which is now understood to say more about the metric than about the registry. N-016's `missing_processor` verdicts remain retired: they were measured on the same flawed metric in a narrower space, so they carry no information either way.

**Root cause.** The objective is a 5-axis composite (3 band-energy ratios ×10, `crest_db`, `tilt_db_per_oct`) with a 5 dB SI-SDR floor. Two of five axes are directly purchasable by destruction, the band ratios are purchasable by filtering away whole regions, and the preservation floor is permissive enough to allow it. **No conclusion about capability, calibration, or quality can be drawn from an objective that a destructive chain wins.**

**Consequence for the roadmap:** DT-77 Track C-4 (a target with perceptual grounding) is not "the highest-value remaining method work" — it is a **precondition** for every other number in this thread. Nothing downstream of the oracle should be believed until the objective refuses destructive solutions.

**Process lesson (third instance in this thread).** Each time the search space widened, the previous conclusion turned out to be an artifact of the measurement rather than a fact about the system: a fixed point (N-016), then the planner's mapping (N-017), now the objective itself (N-018). The recurring error is treating *whatever the harness optimises* as a proxy for quality without first proving the harness cannot be won by an obviously bad answer. **A new objective must be adversarially tested — by constructing a deliberately destructive candidate and requiring it to lose — before any result measured with it is reported.**

## N-019 — The post-N-018 preservation guards do not exclude destruction, and reject an honest treatment

2026-07-26, `src/paired_corpus/objective_audit.py` + `tests/test_objective_audit.py`.
N-018's fix added admissible bounds, a 12 dB SI-SDR floor, an over-compression
guard and adversarial regression tests. Making the adversarial rule *executable* —
an audit that renders a catalogue of destructive candidates against any objective —
showed that the credit for the fix belongs almost entirely to the bounds.

On a pair whose wet is a known −8 dB low-mid cut, measured with the full-signal
guards:

| candidate | SI-SDR | crest | admitted by the guards? |
|---|--:|--:|---|
| `crush` — compressor 20:1 | **16.1 dB** | 9.9 dB | **yes** |
| `gate_chop` — gate at −15.75 dB | **42.8 dB** | 10.0 dB | **yes** |
| `tilt_hack` — +12 dB high shelf | **26.2 dB** | 11.0 dB | **yes** |
| `body_removal` — 330 Hz highpass | −0.6 dB | 12.2 dB | no |
| `wrong_direction_boost` — +9 dB where the truth was a cut | 7.4 dB | 10.1 dB | no |
| **honest recovery** — −4 dB @ 350 Hz + 2.5:1 | **11.1 dB** | 13.0 dB | **no (floor)** |

**Mechanism.** SI-SDR is scale-invariant and correlation-based. A compressor, a
gate and a shelf all leave the waveform highly correlated with the raw, so they
score *well* on it — a preservation floor does not measure whether a treatment is
acceptable, only whether the signal was replaced. The crest guard does not catch
them either (9.9–11.0 dB, above the 8 dB floor). Only the **admissible parameter
bounds** keep these out of the corpus search.

**Two consequences that change how the numbers must be read.**

1. "The guards prevent destructive solutions" is false and must not be written.
   The bounds prevent them. Any objective reused outside this bounded search — a
   planner objective, a promotion criterion, a different harness — inherits none
   of that protection.
2. The 12 dB floor rejects a treatment squarely inside documented professional
   practice (−4 dB low-mid cut plus gentle compression, 11.1 dB). It is
   over-inclusive as well as under-inclusive, so **measured gap closure under it
   is a lower bound on what an admissible chain can reach, not an estimate of it.**

**Also fixed in the same pass (harness-integrity defects, same family):**

- The floor was *scored* during the search on one centred 30 s window and only
  *reported* on the full signal. Two winners of run `20260726-064149-search`
  passed the window and then reported **7.3 dB and 4.9 dB** against a floor
  declared at 12 dB — 2 of 7 pairs in that aggregate did not satisfy the contract
  they were published under. The estimate is now the minimum over five evenly
  spaced windows, and the winner is re-checked on the full signal with a
  `contract_violation` verdict when it fails.
- The generated report's method text was hand-written and still described the
  pre-N-018 contract while the code enforced the corrected one. Method text is now
  generated from the enforced constants and pinned by tests.
- Rows for excluded pairs were never flushed to the run's recovery log, so a
  rebuilt report lost the `inconclusive_alignment` accounting — absence reading as
  "never attempted", the error N-016 exists to prevent.

**What does NOT follow.** Passing the audit does not make an objective
perceptually valid; it makes it not obviously invalid. On synthetic surrogates
none of the six pathologies beats the honest candidate even under the *bare*
distance, so a synthetic pass certifies nothing — the verdict belongs to
(objective, pair). Q-016 remains open and DT-77 C-4 remains BLOCKING.

## N-020 — Candidate objectives cannot be ranked without a metric-independent honest reference

2026-07-26, `src/paired_corpus/objectives.py` + `objective_certification.py`.
Q-016 asks what an automated search may legitimately optimise. The obvious next
step was to build richer candidates — a frequency-resolved log-mel distance, a
cepstral (timbre-shape) distance, a multi-resolution STFT distance, all
level-invariant by per-phrase RMS normalisation — and rank them by how well they
resist the generated pathology catalogue. **That comparison does not work, and the
reason generalises.**

First pass, four candidates over four pairs, "destructive candidates that the
guards admit and that outscore the honest reference":

| candidate | beaten / scored |
|---|--:|
| `composite_v1` (in use) | **1 / 145** |
| `mfcc_l1` | 22 / 145 |
| `logmel_l1` | **80 / 145** |
| `mrstft_log` | **80 / 145** |

Read naively this says the crude 5-axis metric already in use is far harder to game
than any richer one. It says no such thing. Measuring the reference itself:

| candidate | untreated raw | honest reference | reference better than doing nothing? |
|---|--:|--:|---|
| `composite_v1` | 8.7701 | 8.2195 | yes |
| `mfcc_l1` | 21.8962 | 20.1768 | yes |
| `logmel_l1` | 2.8775 | **2.8819** | **no** |
| `mrstft_log` | 2.0703 | **2.2600** | **no** |

Under the two full-spectrum metrics the honest chain scores **worse than leaving
the audio alone**, because the surrogate's raw carries a room comb no registry
processor can undo and those metrics are dominated by that irreducible term. Once
the reference loses to no-op, *every near-no-op candidate "beats" it* — the 80/145
figure counts DeEsser and Compressor variants that barely change the signal, not
exploits. The gaming verdict was measuring the reference, not the objective.

**What follows.**

- A single fixed honest reference cannot rank objectives against one another. A
  chain that is a competent answer under one metric can be worse than no-op under
  another, and each metric needs a reference defensible *in its own terms*.
- Adding a gate to the reference did not fix it (identical totals), so the problem
  is not a missing processor in the reference chain — it is that no admissible
  chain approaches the wet under a full-spectrum metric on this surrogate.
- **Nothing is selected.** Q-016 stays open. `composite_v1` keeps its diagnostic
  status by default, not by merit — it has not been shown to be better, only to be
  auditable with the reference that exists.

**Encoded so it cannot recur silently:** the battery now checks
`HONEST_REFERENCE_VALID` (does the reference beat no-op under this objective?) and,
when it does not, reports `GAMING_RESISTANCE` as **UNTESTABLE rather than FAIL** —
the objective has not been shown to be bad, it has not been shown to be anything.
On the four pairs tried, `logmel_l1` and `mrstft_log` are untestable on every one.

**Process lesson (fourth instance).** The pattern is now unmistakable: a fixed
point (N-016), the planner's mapping (N-017), the objective (N-018), the guard's
estimator and the report's own method text (N-019), and now the *reference* a
verdict is measured against. Each time, the harness's own component was the thing
being measured. Before believing any comparative verdict, measure the baseline it
is relative to — including the one that looks too obvious to check.

## N-021 — The preservation floor is anti-correlated with correctness

2026-07-26, `src/paired_corpus/surrogates.py::make_invertible_pair` +
`tests/test_objective_certification.py`.

N-020 blocked objective comparison on the absence of a metric-independent honest
reference. The fix is a surrogate whose degradation the registry can invert
**exactly**: the wet is the clean signal, the raw is the clean signal through three
registry filters, and the inverse is the same filters with negated gains — a chain
inside the admissible search space. On that pair the honest answer is provably
optimal, so a gaming verdict no longer depends on how good the reference happened
to be.

It cleared N-020 and immediately exposed something larger.

| seed | exact inverse → SI-SDR vs the TARGET | → SI-SDR vs the RAW | admitted by the 12 dB floor? |
|---|--:|--:|---|
| 101 | 92.41 dB | 11.53 dB | **no** |
| 103 | 92.55 dB | 11.62 dB | **no** |
| 107 | 92.97 dB | 11.76 dB | **no** |
| 211 | 92.90 dB | 11.92 dB | **no** |

The mathematically correct answer — 92 dB from the target, i.e. essentially exact
— is **rejected on every seed**.

**Mechanism, and why it is not a threshold complaint.** The preservation floor
measures SI-SDR against the **raw**. The better a treatment corrects the raw, the
further it is from the raw. A constraint of that shape does not merely have the
wrong value; it points the wrong way, penalising exactly the treatments the search
is supposed to find. Lowering the number trades one failure for the other N-019
already recorded: at 5 dB it admitted a 20:1 compressor.

**Consequences.**

- F-9's reading is confirmed and strengthened. Every winner sat at 12.2–13.4 dB
  because the search was pressed against a constraint that punishes correction.
  **+32.8% is a lower bound, and the constraint is why.**
- A preservation constraint must be measured against something other than the
  untreated input — the performance content that must survive, not the input's
  waveform. Specifying that is Q-016 work.

**On ranking the candidates:** with a provably optimal reference, all four
candidate objectives resist all 147 admitted pathologies (0 beaten). Gaming
resistance therefore does **not** discriminate between them on ground truth, and
nothing is selected. What the invertible pair did discriminate is a defect in one
candidate: `mrstft_log` scored the exact inverse *worse than the untreated raw*
because log-magnitude distance is dominated by near-silent frames. Both
log-magnitude candidates now floor magnitudes 80 dB below each segment's own peak.

**Process lesson (fifth and sixth instances, both inside this battery).** The
`LEVEL_INVARIANCE` check scaled candidates up into clipping and then reported every
metric as level-sensitive — it was measuring its own distortion; positive gain is
now capped at available headroom. And the first cross-objective comparison ranked
references rather than objectives (N-020). **A measurement harness is not exempt
from the discipline it enforces; every baseline, guard and check inside it is
itself a measurement that can be wrong.**

## N-022 — Pitch preservation cannot serve as a guard; envelope retention can

2026-07-26, `src/paired_corpus/preservation.py` + `tests/test_preservation.py`.
N-021 left one engineering blocker: a preservation constraint has to be measured
against the performance that must survive rather than against the untreated input.
The obvious formulation — keep pitch and timing — was measured before being built,
and half of it failed.

| candidate treatment | pitch-contour correlation | voiced-frame retention |
|---|--:|--:|
| exact inverse of the degradation (the correct answer) | **0.897** | 1.000 |
| honest chain, noisy surrogate | 0.756–0.841 | 1.000 |
| `crush` — compressor 20:1 | **1.000** | 1.000 |
| `gate_chop` — gate above the performance floor | 0.594–0.654 | **0.75–0.79** |
| `tilt_hack` — +12 dB shelf | 0.620–0.760 | 1.000 |

**Pitch correlation is rejected as a guard component.** It scores a flawless 1.000
for the worst dynamics pathology — compression genuinely does not move pitch, so
pitch can never see it — while the *correct* answer scores lower than most
pathologies, because the tonal change that makes an answer correct is what disturbs
the tracker. Including it would rebuild N-021's anti-correlation in a new form. It
is recorded here so the idea is not re-proposed as new. (It is also slow: ~3.5 s of
YIN per 8 s of audio, unusable inside a search.)

**Voiced-frame retention is kept.** It admits the exact inverse (1.000 on all four
seeds, where the SI-SDR floor rejects it), admits honest treatments the floor also
rejects, and rejects the gating the floor *admitted* at 43 dB SI-SDR. Cost is
~60 ms per evaluation, so it can run inside a search.

**Carried limitation, stated rather than discovered later:** neither retention nor
the crest guards stop extreme compression. Rejecting that stays the objective's job,
and against a provably optimal reference the objective does reject it.

**Result.** With the constraint replaced, all four candidate objectives are
**structurally sound** on the invertible pairs — every property the battery can
check mechanically passes, for the first time in this thread. On noisy surrogates
`composite_v1` and `mfcc_l1` are still beaten by one admitted pathology (a `Limiter`
at its bound), so the result is not uniform across material.

`certified_for_production` remains **False** for every candidate, because
`PERCEPTUAL_ALIGNMENT` is untestable while DEF-003 stands. **Nothing is wired in and
nothing is promoted:** replacing the admissibility rule changes every number the
corpus has produced, which is Q-016's decision to take, not a refactor to slip in.

---

## F-10 — the engine exposed 7 of ~20 installed plugins (2026-07-28, DT-94)

Not a negative result about the product's *quality*; a negative result about the
**inventory**, recorded because three weeks of work proceeded without anyone stating it.

pedalboard 0.9.23 was already a declared dependency and already installed. It ships
roughly twenty plugins. The registry exposed **nine processors built from seven of
them** (Gain, Highpass, Peak, HighShelf, Compressor, NoiseGate, Limiter, plus the
array DeEsser and a composite HumNotch).

Never exposed, despite being installed, licence-cleared under the existing hosted-only
posture (ADR-0001), and requiring no new dependency: `Reverb`, `Delay`, `Distortion`,
`Clipping`, `Chorus`, `PitchShift`, `LowShelfFilter`, `LowpassFilter`, `Convolution`,
`Bitcrush`, `Phaser`, and `Mix` (parallel routing).

Consequence for prior conclusions: **N-016's `missing_processor` verdict and DT-77's
Track B ("new DSP is measurably necessary but unidentified") were both computed over a
search space that omitted every space, saturation, and parallel-routing capability the
project already had.** Those verdicts are not wrong about what the *searched* chains
achieved; they are uninformative about what the *installed* library can achieve. This is
the same failure the N-016..N-022 sequence kept finding — a conclusion that describes the
harness rather than the system — appearing one level further out, in the registry itself.

**What was NOT concluded:** that exposing these primitives improves anything. A plugin
is a raw material. `Distortion` is not tasteful saturation, `Reverb` is a generic
algorithmic room and not a plate, `Chorus` is not a mono-compatible doubler, `Mix` is not
parallel compression, and `PitchShift` is transposition with no pitch detection or
correction in it at all. Turning primitives into production processors is DT-96; the
honest-naming rule is enforced by test (`tests/test_modes.py`), not by convention.

Second defect found while building the channel contract: the executor's array-processor
path collapsed any 2-D buffer to channel 0 (`processed[:, 0]` then `reshape(-1, 1)`), and
`src/dsp/preprocess.py` normalises inputs to mono. The engine was mono **by accident, not
by contract**, and any width, doubling or panned send built before DT-94 would have been
silently discarded before export. Fixed: array processors now map per channel, buffers
are canonical `(samples, channels)`, and `mono_compatibility()` fails closed on a widened
signal that cancels when summed.

## F-11 — mode distinctness, measured (2026-07-28, DT-95)

Prior state: two preset labels (`adaptive`, `polished`) whose entire difference was one
gentle glue compressor. Measured on a real raw rap acapella (D-029, local-only), the three
new authored chains separate by **-9.1 to -13.8 dB level-matched RMS difference** at both
Balanced and Bold, and differ structurally at every intensity. All 12 mode x intensity
renders pass hard technical safety (finite, within ceiling, duration preserved, not gated
away, mono-compatible).

Level matching is load-bearing in that measurement: without it a pure gain change reads as
a large difference. A test asserts a 0.5x copy scores *below* the distinctness floor.

**Standing limits, unchanged.** Distinctness is a *difference* measure. It establishes
that the modes are not the same thing; it establishes nothing about any of them sounding
good, and no perceptual claim follows. DEF-003 still bars public quality claims (D-030
re-scoped it to bar exactly that and no longer to bar implementation). Bold-by-default is
a creative default the owner chose, not evidence.

One honest shortcoming visible in the renders: every chain leaves the material quieter
(-3.7 to -8.3 dB) because the output stage is attenuate-only by design. That is correct
for safety and wrong for auditioning — an A/B where one side is quieter is not a fair
comparison. Loudness-matched audition is a DT-97 requirement, tracked there, not a
property of these chains.

## F-12 — the attenuate-only output stage was penalising correct chains (2026-07-28, DT-96)

The M09 executor applied an attenuate-only ceiling on the stated principle that a
makeup limiter "would boost quiet material and inflate loudness, violating never assume
louder is better". That principle is correct for *evaluation* and wrong for *export*.

Measured consequence: every DT-95 mode render came back **3.7-8.3 dB quieter than its
source**, at inconsistent levels between modes. Any chain that cut anything — which is
every corrective chain — handed the user a quiet file. A vocal that is correct but quiet
reads as worse, so the guard meant to prevent inflated results was silently penalising
the treatments it was protecting.

Fix: three separate intents (`gain_staging.py`). RAW is unchanged level and remains the
only thing evaluation measures. AUDITION is left alone because fair comparison is done by
loudness-matching the *pair* (ADR 0004), not by pushing each side to a target. EXPORT
makes up to an intended peak. Only boosting is capped (12 dB); attenuation always applies
in full; the hard ceiling still runs last in every stage. After the fix all six
mode x intensity renders land at -1 dBFS instead of scattered between -3.7 and -8.3 dB.

**The generalisable error:** one rule was serving two purposes with opposite requirements.
It was never wrong as stated — it was applied at a stage where its rationale did not hold.

## F-13 — capability existed, the product did not have it (2026-07-28, DT-96/97)

DT-94 and DT-95 were reported as delivering graph routing, stereo contracts, eight
primitives and three distinct modes. All of that was true and none of it was reachable by
a user: every path ran through `scripts/v3_render_check.py` and `scripts/v3_render_modes.py`.
The orchestration layer, application service, web job layer, HTTP API, CLI and batch
runner had no notion of a mode.

Recorded because it is a distinct failure mode from the N-016..N-022 family. Those were
measurement artifacts — a conclusion describing the harness rather than the system. This
one is the inverse: working code with no route to the user, where the demo *is* the harness.
"Verified by a script" and "shipped" are not the same claim, and the render scripts made
the first look like the second.

Closed by wiring every route (`tests/test_v3_integration.py` pins both the
application/CLI route and the browser route, plus that a V2 request is unaffected).

## F-14 — macro controls, and the rule that keeps them honest (2026-07-28, DT-97)

The workstation exposes six ordinary-language controls (Repair, Smoothness, Body, Clarity,
Presence, Space). The design constraint worth recording: **a macro may only adjust
processors the selected chain already contains, and never adds a capability.**

Consequence, deliberately kept visible: Natural has no send, so Space cannot do anything
there. Rather than silently doing nothing — a control that appears to work and does not is
worse than an absent one — `apply_macros` reports it as `inert` and the inspector shows it.

Centre (50) is exactly the authored chain, so the modes remain the reference point, and
the source graph is never mutated so a revision stays reproducible from mode + macro
values alone. Nothing here optimises against a distance objective, so the Q-016 gaming
concerns do not apply to this layer.

## F-15 — consistent peak is not consistent loudness (2026-07-28, DT-97 corrective)

F-12 closed with "all six mode x intensity renders land at -1 dBFS instead of scattered
between -3.7 and -8.3 dB". That sentence is true and was read — by an external reviewer,
reasonably — as evidence that the modes now deliver a consistent level. It is not.

Measured with `src/evaluation/delivery_metrics.py` on the DT-97 product renders:

| render                  | peak dBFS | true peak | integrated LUFS | crest dB |
|-------------------------|-----------|-----------|-----------------|----------|
| natural_bold            |   -1.00   |   -1.00   |     -13.65      |  13.02   |
| natural_balanced        |   -1.00   |   -0.98   |     -13.68      |  13.06   |
| rescue_bold             |   -1.00   |   -1.00   |     -14.64      |  14.13   |
| rescue_balanced         |   -1.00   |   -1.00   |     -14.93      |  14.48   |
| modern_rap_bold         |   -1.00   |   -0.99   |     -15.97      |  15.47   |
| modern_rap_balanced     |   -1.00   |   -1.00   |     -17.15      |  16.73   |

The peaks are identical to two decimal places. The integrated loudness spans **3.50 LU**.
Modern Rap balanced is audibly quieter than Natural despite both peaking at -1 dBFS,
because peak describes one sample and loudness describes the programme. The crest column
shows why: the spread is dynamics, not an error.

Second observation from the same instrument: the 12 dB makeup cap is not hypothetical. A
1 s 300 Hz test tone through Rescue/Bold left the signal 14.2 dB below target, the cap
engaged, and the delivered file peaked at **-2.22 dBFS**. So even the peak claim holds
only while the cap stays disengaged — which nothing previously reported.

**The generalisable error:** a fix was verified with the same single statistic that
motivated it. Peak was the symptom, peak was the remedy, peak was the proof — and the
measurement that would have distinguished "levels are consistent" from "peaks are
consistent" was simply not taken. This is the N-016 family pattern (a conclusion
describing the harness) in its cheapest form: not a wrong measurement, an absent one.

Corrective, all descriptive: `delivery_metrics.py` reports sample peak, 4x-oversampled
true peak, integrated LUFS, crest factor, clipping count, and for stereo the channel
correlation and mono fold-down delta. It is wired into the job payload and the
workstation inspector, and `gain_staging` (including `makeup_clamped`) is now reported
rather than inferred.

Explicitly NOT done: these are not combined into a score, and no threshold is asserted on
any of them. `certified_for_production` remains unreachable while DEF-003 stands
(`objective_certification.PERCEPTUAL_ALIGNMENT` is UNTESTABLE by construction), so a
quality verdict built from these numbers would be exactly the unsupported claim the
certification battery exists to refuse. `tests/test_delivery_metrics.py` pins the payload
against acquiring a score/grade/verdict key.

One defect found in this module by its own tests: total L/R cancellation produced a
`None` fold-down delta, because the implementation guarded `mono_level <= 0` as
unmeasurable. The single most severe stereo failure would have been reported as missing
data. Fixed to floor at -120 dB — absence of evidence must not read as evidence of
absence (N-016).

## F-16 — an explicit selection was silently substituted (2026-07-28, DT-97 corrective)

`webapp/jobs.py` coerced an unrecognised mode to `None` and rendered the V2 chain, so
`mode=modrn_rap` produced a completed job reporting `mode: null`. The user asked for one
thing, received another, and nothing in the response said so. The application service had
raised a typed error for the same input since DT-96; only the web layer swallowed it.

Now `UnknownModeError` carries the available list and the API answers 400 with it.
Omitting `mode` remains a valid V2 request — absence is not an error, only an explicit
unknown value is. Recorded because the failure was invisible by construction: every
signal that something went wrong had been removed by the fallback that handled it.
