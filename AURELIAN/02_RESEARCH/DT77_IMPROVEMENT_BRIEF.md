# DT-77 Improvement Brief — Evidence-Led Failure Taxonomy

Seeds for the DT-77 milestone. Each brief is a *candidate experiment*, not a
change. Promotion requires the DT-57→DT-60 preregistered study line; none is
promoted here, and promotion of any audible DSP change is a human-only gate
(`AURELIAN/00_CONTROL/AUTONOMY_POLICY.md`).

**Evidence base:** N-015, N-016, **N-017**; `reports/evaluations/paired-corpus/FINDINGS.md`
F-1, F-4…F-7. All of it is directional, single-artist, lossy-MP3 and does **not**
satisfy DEF-003. It ranks *where to look*; it establishes no perceptual claim.

> ## ⚠ N-018 (2026-07-26): the numbers below are measured with a discredited objective
>
> The per-template parameters of the registry-safe search show it won by
> **highpassing a rap vocal at 330 Hz** and **compressing at 20:1** (ratio pinned to
> its maximum), with the low-mid bell left at 0.0 dB — safe to render, destructive
> as audio. CI reproduced the same pathology from the other direction, choosing a
> **+9 dB boost** where the truth was a −8 dB cut and still scoring 47%.
>
> **Retracted:** that ~46% of the champion→wet *quality* gap is recoverable with
> existing processors, and that the planner's specs are what withhold it.
> **Still standing:** that the registry can reduce the composite *distance* — which
> now says more about the metric than the registry.
>
> The objective has since been corrected (admissible bounds, 12 dB preservation
> floor, over-compression guard, adversarial regression tests), and the corpus is
> being re-measured. **Treat every percentage in this section as superseded
> pending that re-run.** Priorities below are ordered by what survives N-018.
>
> **The re-run has landed (F-9, run `20260726-131308-search`, corrected *and*
> repaired guard — see N-019).** Median distance closed **+32.8%**, mean +32.2%,
> bootstrap 95% CI **+20.6% .. +44.1%** (excludes zero), 6 of 7 pairs ≥10%. Every
> winner sits at 12.2–13.4 dB SI-SDR, i.e. hard against a floor that N-019 showed
> also rejects honest treatments — **read +32.8% as a lower bound, not an
> estimate.** Required capability: 4 pairs full chain, 2 tonal+air, 1 tonal. The
> two pairs whose old winners had violated the preservation floor lost the
> compressor entirely once it was enforced.

## The finding that reorganised this brief (N-017)

Three probes measured the same corpus with progressively wider search spaces.
The answer changed each time, and the last change was categorical:

| probe | space searched | verdict |
|---|---|---|
| single point | planner strength 0.7 | 1 engagement gap, 4 missing processor |
| strength sweep | planner strengths 0.2–1.0 | 2 engagement gap, 4 missing processor |
| **registry-safe search** | **`PROCESSORS.safe_ranges`** | **0 missing processor; every pair closes 20.9–57.8%** |

The first two searched the planner's strength mapping — a *proxy* for the
registry. The planner's muddiness treatment caps at a −4.0 dB PeakFilter; the
registry permits **−12..+12 dB**, and permits *boosting*. Under the search
DT-55E actually specifies:

| pair | strength sweep | registry-safe search | smallest sufficient chain |
|---|--:|--:|---|
| P-01 | +43.5% | **+62.1%** | t5_full |
| P-02 | +0.3% | **+20.9%** | t5_full |
| P-05 | −5.6% | **+57.8%** | t5_full |
| P-06 | +8.4% | **+56.3%** | t5_full |
| P-07 | −8.8% | **+33.7%** | t5_full |
| P-09 | +0.7% | **+45.2%** | t3_tonal_air |

Median **+50.7%**, mean **+46.0%**, bootstrap 95% CI **+33.5% .. +56.9%** —
the CI excludes zero. Safety held throughout: −0.2 dBFS ceiling, zero clipping,
SI-SDR ≥ 5 dB against the raw.

**Bottleneck verdict: the planner, not the DSP.** Two planner-level properties
account for the entire measured gap — which processors it engages, and how much
its issue specs permit. Both are Track A. **Track B is withdrawn.**

---

## Track A — The planner (the whole measured story)

### A-1 — Engagement: the champion does not act  *(N-015; measurement stands)*

The champion applied **0 actions on 86%** of valid pairs while the diagnosis
measured heavy low-mid boxiness (`mud_ratio` 6.6), an audible noise floor
(−44.5 dBFS) and a dark centroid; `reduce_noise` fired at confidence 0.22 and was
demoted to `report_only`. A chain that never runs cannot be perceived.

**Bounded experiment:** on artist-held-out splits, lower the engagement gate for
mud/low-mid and noise objectives within existing safe ranges; measure gap-to-wet
reduction on aligned phrases plus do-no-harm (peak/clip/SI-SDR). Reject on any
do-no-harm breach or if the gap does not shrink.

### A-2 — Spec range: `_ISSUE_SPECS` is far narrower than the registry  *(N-017)*

Not a safety limit — a **specification** limit. The planner's strength mapping
reaches −4.0 dB where `PeakFilter` safely permits −12 dB, and never boosts where
the registry permits +12 dB. Every pair that improved did so using gains the
current specs cannot author.

**Bounded experiment:** widen the `_ISSUE_SPECS` strength→parameter mapping
toward the registry's declared ranges under preregistration, with the do-no-harm
suite unchanged and an explicit over-treatment (thin/hollow) rejection axis.
Widening what the planner may apply is safety-relevant and must not ship without
DT-78.

### A-3 — Bidirectional tonal correction  *(N-017, supersedes the old F-6 reading)*

F-6 read "any low-mid cut makes these pairs worse" as evidence of a missing
capability. It was evidence of a missing **objective**: the registry's PeakFilter
boosts as readily as it cuts, but no planner objective ever asks it to. Pairs
whose professional reference is *warmer* than the raw need addition, not
subtraction.

### A-4 — Dynamics are implicated  *(N-017)*

5 of 6 pairs required the full chain (tonal EQ + air shelf + gate + compressor);
only 1 was satisfied by tonal + air. Consistent with
`docs/research/underground_vocal_engineering_reference.md` on dynamic
consistency. Per-capability attribution (gate vs compressor) needs the
per-template artifact from the re-run.

### A-5 — Sub-floor sibilance detection  *(N-014 constraints apply)*

Real rap `sibilance_frame_p95 ≈ 0.095` sits below the DeEsser's 0.10 floor, so
de-essing never engages. N-014 proved blanket in-range de-essing is net-harmful:
any change needs per-clip detection gating, execution **inside** the safety
envelope, and a separately validated floor.

---

## Track B — New DSP capability: **withdrawn**

N-016 promoted this on the strength of the `missing_processor` verdicts. N-017
retired those verdicts. **No current evidence supports building dereverberation,
resonance suppression, or harmonic enhancement**, because the existing registry
has not yet been given a planner that uses it. Revisit only if Track A is
implemented and a residual gap survives a full registry-safe search.

---

## Track C — Method (largely complete)

- **C-1 NoiseGate threshold sweep** — done: the gate threshold is now a searched
  parameter (`t4_tonal_air_gate`), not a fixed −42 dB.
- **C-2 Coordinate descent** — done: `src/paired_corpus/search.py`, deterministic,
  registry-bounded, validated by recovering a known in-capability transformation.
- **C-3 Recover or retire the 2 `inconclusive_alignment` pairs** — open; 22% of
  the corpus still contributes nothing.
- **C-4 A target with perceptual grounding** — open, and still the binding
  methodological limit. Everything above optimises *composite spectral distance
  to a lossy YouTube wet*. That is not quality, and no amount of further search
  makes it quality. **This is the highest-value remaining method work.**

  Progress (N-019, 2026-07-26): the adversarial rule is now executable —
  `src/paired_corpus/objective_audit.py` scores any candidate objective against a
  catalogue of destructive treatments plus an objective-independent honest
  reference. Its first finding reassigns credit for the N-018 fix: the
  *preservation guards* admit a 20:1 compressor (16 dB SI-SDR), a gate set above
  the performance floor (43 dB) and a +12 dB shelf (26 dB), because SI-SDR is
  scale-invariant and none of them decorrelates the waveform. The **admissible
  bounds** are what excludes destruction. The same floor rejects an honest −4 dB
  low-mid cut with gentle compression (11.1 dB), so **every gap-closure number
  measured under it is a lower bound, not an estimate.** C-4 still needs a target
  with real perceptual grounding; the audit only says an objective is not
  *obviously* invalid.

  Extended into a fail-closed certification battery (N-020, N-021):
  `objective_certification.py` checks determinism, identity-optimum, monotonicity,
  level invariance, non-degeneracy, honest-reference validity, gaming resistance
  against a registry-GENERATED pathology catalogue, and constraint-admits-honest.
  `PERCEPTUAL_ALIGNMENT` is permanently UNTESTABLE while DEF-003 stands, so
  production certification is unreachable by construction — nothing here can be
  called perceptually valid.

  **Top engineering blocker is now the preservation constraint, not the distance
  (N-021).** On a surrogate whose degradation the registry inverts exactly, the
  correct answer measures 92 dB from the target and 11.5–11.9 dB from the raw, and
  the 12 dB floor rejects it on every seed: SI-SDR against the raw punishes
  correction, so no threshold value fixes it. Four candidate objectives
  (`composite_v1`, `logmel_l1`, `mfcc_l1`, `mrstft_log`) exist and none is
  selected — against a provably optimal reference all four resist all 147 admitted
  pathologies, so gaming resistance does not separate them.
- **C-5 Processor ordering** — harness built (`--ordering`, predeclared orders
  including the professional order from `docs/research/vocal_chain_research.md`);
  not yet run on the corpus.

---

## Priority order (by measured impact)

0. **C-4 — a target that cannot be won by a bad answer. BLOCKING.** N-018 showed
   the objective was gameable, so nothing measured with it supports a capability,
   calibration or quality conclusion. The first correction has landed (admissible
   bounds + preservation guards + adversarial tests); the open part is a target
   with genuine *perceptual* grounding rather than spectral-distance-plus-guards.
   Everything below is contingent on this.
1. ~~**Re-measure the corpus** under the corrected objective~~ — **done (F-9).**
   Median **+32.8%**, CI +20.6%..+44.1%, 6/7 pairs ≥10%, every winner admissible on
   the full signal. Every number is a **lower bound**: the preservation floor is
   binding on all 7 winners and N-019 showed it also rejects honest treatments.
2. **A-1 + A-2 together** — engagement and spec range are coupled; each alone
   saturates against the other. Both direction *and* a floor on size now survive:
   the champion abstained on 6 of 7 pairs while an admissible chain inside the
   registry closed a median 32.8% of the distance it left on the table.
3. **A-3** bidirectional tonal objectives — the registry can boost and no planner
   objective asks it to. Cheap and independent of the metric question. F-9
   strengthens this: winning chains *boost* the low-mid on 2 pairs (+3.0, +4.5 dB)
   and cut it on 2 others, so direction is genuinely pair-dependent.
4. **A-4** dynamics — **partly confirmed as an artifact.** The two pairs whose old
   winners had violated the preservation floor stopped needing the compressor at
   all once it was enforced (required capability t5_full → t3_tonal_air). 4 of 7
   pairs still require it. Treat dynamics as implicated on some pairs, not on the
   corpus.
5. **A-5** sibilance floor (N-014 constraints).
6. **C-3, C-5** corpus recovery and ordering.
7. ~~Track B~~ — withdrawn; no evidence, and now less than none.

## Standing constraints

- Never tune thresholds on this corpus (6–7 valid pairs, one dominant artist,
  lossy MP3, DEF-003 not satisfied) — use it to *size* effects only.
- Artist-held-out splits, predeclared contracts, do-no-harm suite, −0.2 dBFS
  envelope, abstention preserved.
- No perceptual claim follows from any distance measurement here.
- The oracle proves a chain *exists* inside the registry that closes the gap on
  these pairs. It does **not** show the planner can find it from the raw audio
  alone — that is A-1/A-2's burden of proof, on held-out artists.
