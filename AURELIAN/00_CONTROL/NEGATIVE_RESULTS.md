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
