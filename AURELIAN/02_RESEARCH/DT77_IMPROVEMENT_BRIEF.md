# DT-77 Improvement Brief — Evidence-Led Failure Taxonomy

Seeds for the DT-77 milestone. Each brief is a *candidate experiment*, not a
change. Promotion requires the DT-57→DT-60 preregistered study line; none is
promoted here, and promotion of any audible DSP change is a human-only gate
(`AURELIAN/00_CONTROL/AUTONOMY_POLICY.md`).

**Evidence base:** N-015, N-016, **N-017**; `reports/evaluations/paired-corpus/FINDINGS.md`
F-1, F-4…F-7. All of it is directional, single-artist, lossy-MP3 and does **not**
satisfy DEF-003. It ranks *where to look*; it establishes no perceptual claim.

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
- **C-4 A target with perceptual grounding** — open, and now the binding
  methodological limit. Everything above optimises *composite spectral distance
  to a lossy YouTube wet*. That is not quality, and no amount of further search
  makes it quality. **This is the highest-value remaining method work.**
- **C-5 Processor ordering** — harness built (`--ordering`, predeclared orders
  including the professional order from `docs/research/vocal_chain_research.md`);
  not yet run on the corpus.

---

## Priority order (by measured impact)

1. **A-1 + A-2 together** — engagement and spec range are coupled; each alone
   saturates against the other. This is where the entire measured +46% lives.
2. **A-3** bidirectional tonal objectives — cheap, and it is what four pairs
   actually wanted.
3. **C-4** a perceptually grounded target — without it, further optimisation
   improves a number of unproven meaning.
4. **A-4** dynamics, once per-capability attribution lands.
5. **A-5** sibilance floor (N-014 constraints).
6. **C-3, C-5** corpus recovery and ordering.
7. ~~Track B~~ — withdrawn; no evidence.

## Standing constraints

- Never tune thresholds on this corpus (6–7 valid pairs, one dominant artist,
  lossy MP3, DEF-003 not satisfied) — use it to *size* effects only.
- Artist-held-out splits, predeclared contracts, do-no-harm suite, −0.2 dBFS
  envelope, abstention preserved.
- No perceptual claim follows from any distance measurement here.
- The oracle proves a chain *exists* inside the registry that closes the gap on
  these pairs. It does **not** show the planner can find it from the raw audio
  alone — that is A-1/A-2's burden of proof, on held-out artists.
