# DT-77 Improvement Brief — Evidence-Led Failure Taxonomy

Seeds for the DT-77 milestone (Evidence-Led Failure Taxonomy and Improvement
Brief). Each brief is a *candidate experiment*, not a change. Promotion requires
the DT-57→DT-60 preregistered study line; none is promoted here. DT-77's own
contract excludes code changes and confirmatory retuning — this file is the
prioritized taxonomy DT-78 preregisters *from*.

**Evidence base:** `reports/evaluations/paired-corpus/FINDINGS.md` F-1, F-4, F-5,
F-6; N-015, N-016; DT-55D gap analysis + DT-55E oracle sweep (2026-07-25, D-029).
All of it is directional, single-artist, lossy-MP3 and does **not** satisfy
DEF-003. It ranks *where to look*; it establishes no perceptual claim.

## The measured split (this is what sets priority)

The oracle forced the planner's own treatments to engage and swept them across
the registry's entire safe strength range. Over 7 valid pairs (2 excluded as
`inconclusive_alignment`):

| bucket | pairs | improvement | what it means for engineering |
|---|--:|---|---|
| recoverable with existing DSP | **3** | +43.5%, +10.9%, +8.4% | engagement + range work pays measurably |
| unrecoverable with existing DSP | **4** | ≤ +0.7% (2 negative) | new capability is *measurably* necessary |

Aggregate mean +7.05% with a bootstrap 95% CI of **−3.00% .. +20.45%** — the CI
spans zero. **No aggregate effect is established.** The priority below is driven
by the per-pair split, not by the aggregate.

Bottleneck verdict: **mixed**. Roughly half the corpus is limited by engagement
and allowed range, half by absent capability. Neither dominates at n = 7.

---

## Track A — Calibration and range (cheap, measurable now)

*Justification: 3/7 pairs, up to +43.5% closed using only processors that already
exist and are already safety-validated.*

### A-1 — Planner under-engages on real rap acapella  *(from F-1 / N-015)*

**Evidence:** the champion applied **0 actions on 86%** of valid pairs while the
diagnosis measured heavy low-mid boxiness (`mud_ratio` 6.6), an audible noise
floor (−44.5 dBFS) and a dark centroid — `reduce_noise` fired at confidence 0.22
and was demoted to `report_only`.

**Hypothesis:** confidence/threshold gating calibrated on synthetic degradations
and clean studio *singing* under-fires on real home-recorded *rap*.

**Bounded experiment:** on artist-held-out splits, lower the engagement gate for
mud/low-mid and noise objectives *within existing safe ranges*; measure gap-to-wet
reduction on aligned phrases plus do-no-harm (peak/clip/SI-SDR). Reject on any
do-no-harm breach or if the gap does not shrink.

**Necessary but not sufficient — F-4.** Engagement alone left 4/7 pairs at ≤0.7%.

### A-2 — The safe parameter range is binding  *(NEW; from F-5)*

**Evidence:** distance-vs-strength is monotone on every pair. On all three pairs
where forcing helped, distance was **still falling at maximum strength**
(edge slopes −0.091 / −0.023 / −0.108) — the optimum lies outside what the
planner may apply. At strength 1.0 the muddiness treatment is a **−4.0 dB**
PeakFilter at 300 Hz; the wet targets want more.

**Why this matters:** a parameter-range ceiling is far cheaper to address than a
missing processor, and it was **invisible** at the single fixed strength the first
probe used. It also means A-1 alone would saturate.

**Bounded experiment:** extend the muddiness/harshness gain range in a
preregistered step, with the do-no-harm suite and the −0.2 dBFS envelope
unchanged, and an explicit over-cut (thin/hollow) rejection axis. Range extension
is a **safety-relevant** change: it must not ship without the DT-78 preregistration.

### A-3 — Sub-floor sibilance detection  *(from F-1 + N-014)*

Real rap `sibilance_frame_p95 ≈ 0.095` sits below the DeEsser's 0.10 in-range
floor, so de-essing never engages. N-014 already proved blanket in-range de-essing
is net-harmful: any change needs per-clip detection gating, execution **inside**
the safety envelope, and a separately validated floor.

---

## Track B — DSP research (expensive, now *measurably* necessary)

*Justification: 4/7 pairs cannot be moved toward their wet target by any searched
configuration of the existing registry — two got monotonically **worse**.*

### B-1 — Non-subtractive tonal matching  *(from F-6)*

**Evidence:** on those four pairs every amount of low-mid cut increases distance
(edge slopes +0.009 … +0.268). The registry offers subtractive low-mid/harshness
filtering and a fixed-threshold gate; these targets do not want subtraction.
Weak supporting signal: improvement vs. measured wet−raw low-mid delta gives
**r = −0.479, n = 7** — consistent with "subtraction helps only when the wet has
less low-mid than the raw", but underpowered. **Hypothesis, not finding.**

**Direction:** target-informed tonal shaping (bidirectional, bounded) rather than
one-way corrective cuts.

### B-2 — Missing modules (still deferred)

Dereverberation, resonance suppression and bounded harmonic enhancement remain
outside the registry. F-6 makes "some new capability is needed" evidence-backed;
it does **not** identify *which* module. Do not start building until the method
gaps below are closed — otherwise Track B risks solving the wrong problem.

---

## Track C — Close the method gaps first (blocks any final Track B verdict)

The `missing_processor` verdicts mean "no *searched* configuration got closer",
which is weaker than "no configuration exists". Before Track B is funded:

- **C-1** Sweep the `NoiseGate` threshold. Its spec is strength-**invariant**
  (fixed −42 dB), so the current probe tested denoising at exactly one setting.
- **C-2** Implement the coordinate descent over ≤6 params that the orchestration
  plan specifies for DT-55E; the 3-chain × 5-strength grid is a coarse proxy.
- **C-3** Recover the 2 `inconclusive_alignment` pairs (0 measurable phrases) or
  retire them; 22% of the corpus currently contributes nothing.
- **C-4** Replace the composite spectral distance with a target that has some
  perceptual grounding, or stop treating distance reduction as improvement.

---

## Priority order (by measured impact, per instruction "mixed → measured impact")

1. **A-1 + A-2 together** — engagement and range are coupled; A-1 alone saturates
   at the range ceiling (F-5). Largest measured headroom, existing processors.
2. **C-1, C-2** — cheap, and they gate whether Track B is real.
3. **A-3** sibilance floor (N-014 constraints apply).
4. **C-3, C-4** — corpus and metric validity.
5. **B-1** non-subtractive tonal matching — only after C-1/C-2 confirm the
   residual survives a real parameter search.
6. **B-2** new modules — last, and only if B-1 is insufficient.

## Standing constraints

- Never tune thresholds on this corpus (n = 7 valid, one dominant artist,
  lossy MP3, DEF-003 not satisfied) — use it to *size* effects only.
- Artist-held-out splits, predeclared contracts, do-no-harm suite, −0.2 dBFS
  envelope, abstention preserved.
- No perceptual claim follows from any distance measurement here.
