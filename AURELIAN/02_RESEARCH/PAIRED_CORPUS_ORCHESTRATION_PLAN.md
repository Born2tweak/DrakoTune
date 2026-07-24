# Paired Raw/Wet Corpus — Orchestration Plan (DT-55A…H)

**Date:** 2026-07-24 · **Status:** authoritative execution plan for any agent.
**Goal:** use paired raw→wet vocal references to close the measured gap between the
current champion and professional processing — *harshness/fatigue, clarity,
weak-mic coloration, cohesion* (owner listening evidence, E-OWN-001).
**Prime directive:** every step is either **[SAFE-NOW]** (no rights exposure, run
immediately) or **[GATED:H1-D]** (touches the private corpus; blocked until the
H1-D rights ruling). An agent executes all [SAFE-NOW] steps in order and stops at
gates. Existing guardrails hold: no perceptual claim from metrics, −0.2 dBFS
ceiling, abstention, originals read-only, artist-level anti-leakage.

---

## 0. The rights ruling this plan is built around (H1-D)

The candidate corpus (`…\Codex\2026-07-24\can\outputs\Juice_WRLD_Acapella_Playlist\`,
31 MP3s, 115 MB) is **commercial copyrighted recordings** obtained from YouTube
(video IDs in filenames), including one item labeled **LEAKED** and one
**AI-isolated**. Under D-026 (authorized-non-private posture: synthetic + owner +
*license-verified* public only) and the fail-closed ingestion rule
(`src/acquisition/validators.py: consent_ref` required), **none of it may be
ingested, processed, rendered, or feature-extracted by DrakoTune** until the owner
+ counsel record decision **H1-D** (see `control/CONSOLIDATED_HUMAN_DECISION_H1_STUDY.md`).

Non-negotiable regardless of H1-D:
- File 06 (**LEAKED** XO Tour Llif3) → `rejected` permanently. Leaked material is
  never used.
- File 11 (AI-isolated Ransom) → `rejected` as a *wet target* (source-separation
  artifacts make it an invalid professional reference).
- Nothing from this corpus is redistributed, committed to git, uploaded, used in
  any public example, demo, claim, or model training. If H1-D approves anything,
  it is at most **local, internal, evaluation-only**, with a documented deletion
  path. The clean alternative is already priced: DT-55's `commissioned_dry_wet`
  scenario produces an equivalent corpus with full rights.

**What IS permitted before H1-D:** filename/byte-level registration (checksums,
sizes, durations from container metadata) into a **local, gitignored** manifest
under `data/restricted/` — provenance bookkeeping, not use.

## 0.1 Known inventory (from listing + checksum, no audio decoded)

| Pair | Raw | Wet | Class (expected) |
|---|---|---|---|
| P01 Rockstar In His Prime | 03 | 04 | candidate_exact |
| P02 Lucid Dreams | 07 | 08 "OFFICIAL" | candidate_exact |
| P03 Empty | 14 | 15 | candidate_exact |
| P04 Flaws and Sins | 16 | 17 | candidate_exact |
| P05 Candles | 20 | 21 "Official" | candidate_exact |
| P06 Stay High | 18 | 19 | probable |
| P07 All Girls Are The Same | 24 | 25 | probable |
| P08 Wasted | 12 | 13 | probable |
| P09 Ransom | 10 | 09 | probable (11 rejected) |
| P10 GO (Kid LAROI) | 22 | 23 "DIY" | probable_low_quality (DIY = karaoke-style extraction) |
| — XO Tour Llif3 | 05 | 06 LEAKED | **rejected** (leaked wet) |
| Unpaired raw | 01, 26, 27(=28 dup), 29, 30, 31 | — | unpaired_reference |
| Unpaired wet | 02 Hate Me | — | unpaired_reference |

**Structural facts every later step must respect:**
1. **~10 candidate pairs, ~8 of them one artist (Juice WRLD).** This corpus can
   mostly teach "the chain used on one voice." Artist-held-out validation is
   only 3 single-pair artists (Tecca, LAROI, ±Uzi-raw-only) → generalization
   evidence from this corpus alone is weak *by construction*; say so in every report.
2. **All lossy MP3**; wet uploads likely carry codec + full-mix-master artifacts.
   Delta profiles are "YouTube-wet minus YouTube-raw," not "pro chain minus mic
   feed." Treat deltas as *directional guidance*, never as exact targets.
3. #27/#28 byte-identical → the duplicate validator must catch this (it does:
   `find_duplicates` by sha256).

---

## 1. Program map (who does what, in what order)

```
DT-55A  Private corpus registration + rights classification     [SAFE-NOW: manifest only] [GATED:H1-D: ingestion]
DT-55B  Pair verification + phrase alignment engine              [SAFE-NOW: build+test on surrogates] [GATED:H1-D: run on real]
DT-55C  Raw→wet transformation delta profiling                   [SAFE-NOW: build+test on surrogates] [GATED:H1-D: run on real]
DT-55D  Champion gap analysis (raw → champion → wet)             [GATED:H1-D]
DT-55E  Oracle bounded DSP fitting (wet as teacher)              [SAFE-NOW: harness on surrogates] [GATED:H1-D: real fits]
DT-55F  Experiment line E1..E8 (harshness → cohesion)            [SAFE-NOW: contracts + surrogate runs] [GATED:H1-D/owner-listen]
DT-55G  Artist-held-out validation                               [GATED:H1-D]
DT-55H  Randomized loudness-matched owner review                 [GATED: owner listening]
```

The surrogate trick that makes most of this SAFE-NOW: we can **manufacture exact
ground-truth pairs** from rights-clean audio — take CC-BY/owner clips, degrade
them into a synthetic "raw" (add the corpus-v1 degradation recipes: noise, room,
proximity, clipping, sibilance), and render a synthetic "wet" through a *known*
reference chain (denoise→EQ→compress→de-ess→limit with logged parameters). Every
DT-55B/C/E component is then testable against known answers before it ever
touches gated audio.

---

## 2. DT-55A — Registration + rights classification

**[SAFE-NOW]** `scripts/register_private_corpus.py`:
- Input: a folder path (never committed). Output: `data/restricted/private_corpus_manifest.json`
  (gitignored) with per-file: filename, bytes, sha256, mtime, parsed artist/title/
  role(raw|wet) from filename, candidate pair id, and `rights_class`.
- `rights_class` vocabulary: `blocked_pending_H1D` (default) · `rejected_leaked`
  (file 06) · `rejected_ai_isolated_wet` (file 11) · `duplicate` (file 28).
- Duplicate detection via sha256 (must flag 27/28). No audio decode. Never copies
  audio into the repo tree.
- Registers the corpus in the rights machinery as **quarantined**: an entry in the
  manifest mirrors `src/acquisition` ingestion fields with `consent_ref: null` so
  `ingestion_valid()` fails — the pipeline is *proven* to refuse it.

**[GATED:H1-D]** flipping any file's class to `approved_local_internal_eval` +
adding the H1-D decision reference as its `consent_ref`.

**Tests:** manifest schema; leaked/AI files always classified rejected even if
H1-D approves the rest; `ingestion_valid` fails on `consent_ref: null`.

## 3. DT-55B — Pair verification + alignment engine (`src/paired_corpus/`)

**[SAFE-NOW]** Build modules (all pure, testable on surrogates):

- `pairing.py` — `PairCandidate(pair_id, raw_ref, wet_ref)`; classification
  `verified_exact_pair | partially_matchable | incorrect_pair | unusable` from:
  duration ratio (|Δ|/max < 0.08 after silence-trim), global envelope
  cross-correlation peak (>0.6 after alignment), and voiced-segment count
  agreement. **Filenames never prove pairing**; classification requires signal
  evidence + (for real corpus) one human confirmation flag.
- `alignment.py` — resample to 44.1k mono analysis copies (originals untouched);
  trim edge silence for matching only; global offset via FFT cross-correlation;
  phrase segmentation (energy-gated, min 350 ms, hyst.); per-phrase local
  re-alignment (±120 ms search); phrase verdicts `aligned | edited | unmatched`
  (unmatched/edited excluded from deltas). Store `AlignmentMap(pair_id,
  global_offset_ms, phrases[…])`.
- `surrogates.py` — the ground-truth pair factory: clean CC-BY clip → synthetic
  raw (corpus-v1 degradation recipes) + synthetic wet (known logged chain).
  Provides `make_surrogate_pair(seed)` used by every test.

**Tests (Field-14/16 style):** exact pair classifies exact; shifted copy recovers
its known offset ±5 ms; different-song pair → `incorrect_pair`; edited-phrase
surrogate → that phrase `edited`, others `aligned`; duration-mismatch → not
`verified_exact`.

**[GATED:H1-D]** running `pairing`/`alignment` on the real manifest.

## 4. DT-55C — Raw→wet delta profiling (`src/paired_corpus/deltas.py`)

**[SAFE-NOW]** Per aligned phrase and per pair, compute raw→wet deltas reusing
existing measurement code (do not re-implement): integrated/short-term loudness +
phrase-consistency (`src/diagnostics/loudness.py`), peak/true-peak/crest
(`safety.py`), spectral tilt / low-mid (250–500) / boxiness (300–700) /
harsh (2.5–5k) / sibilance (5.5–12k) / air (10k+) band energies (`spectral.py`
+ benchmark band logic), noise floor, transient density (crest per phrase),
dynamic-range distribution, harmonic-density proxy (spectral flatness in voiced
frames). Output `TransformProfile(pair_id, phrase_deltas[], pair_summary)` +
cluster summaries by (artist, delivery, condition) — **never one averaged
"studio curve"**; keep per-cluster target *ranges*.

**Tests:** on surrogates the recovered deltas must match the known chain's
documented effect signs (e.g. wet has lower crest, reduced 300–500 energy,
bounded true peak) within tolerance.

**MP3 caveat handling:** deltas above ~16 kHz are codec-unreliable → excluded;
every profile carries `source_quality: lossy_mp3` and a "directional guidance
only" limitation string.

## 5. DT-55D — Champion gap analysis **[GATED:H1-D]**

For each verified pair: render raw → current champion (`analyze_and_plan` →
`render_plan`), then measure the *remaining* gap champion→wet on every DT-55C
axis. Deliverable: `reports/evaluations/paired-corpus/<runid>/gap_report.md`
ranking gap axes by magnitude × phrase-consistency — this replaces guesswork
about "what to fix first" with measured evidence. Expected top gaps per E-OWN-001:
harsh 2.5–5k dynamics, phrase-level leveling, low-mid masking, noise/room
coloration.

## 6. DT-55E — Oracle bounded fitting (`src/paired_corpus/oracle.py`)

The two-layer strategy (do **not** train an end-to-end model on ~10 lossy pairs):

- **Oracle layer [SAFE-NOW harness]:** given (raw, wet-target), search *within
  the existing processor registry's safe ranges only* (`clamp_params` enforced;
  chain order fixed; de-ess inside the safety envelope per N-014) for the
  parameter set minimizing a multi-objective distance to the wet target:
  weighted phrase-loudness-consistency + band-energy deltas + crest delta,
  with hard penalties for clipping, ceiling breach, SI-SDR collapse
  (preservation floor), and processing-intensity (prefer minimal chains).
  Coordinate-descent over ≤ 6 params, deterministic seed, budgeted iterations.
  Output per pair: `OracleFit(params, achieved_distance, residual_gap_axes)`.
- **Automatic layer:** compare oracle fits across pairs; extract *bounded
  adaptive rules* (input-feature → parameter) only where fits agree across ≥ 3
  pairs from ≥ 2 artists; encode as planner-rule candidates (never auto-promote).

**The diagnostic payoff:** oracle residuals split the quality gap into
(a) parameter selection fixable now, (b) missing module interaction, (c) missing
processors (dereverb/resonance-suppression/harmonic-enhancement are NOT in the
registry today → they become DT-77 improvement briefs), (d) information the raw
recording never captured → **abstain**, don't fabricate.

**Tests [SAFE-NOW]:** on a surrogate whose wet chain lies *inside* the registry's
capability, the oracle must recover near-target (distance below threshold); on a
surrogate wet chain using an effect the registry lacks (e.g. heavy reverb), the
oracle must report a large residual on the right axis — proving the
(a)-vs-(c) discrimination works.

## 7. DT-55F — Experiment line (each = predeclared contract, then run)

Order fixed by E-OWN-001 + expected gap report. Every experiment follows the
`reports/evaluations/reconcile-2026-07-23/EXPERIMENT_CONTRACT.md` template:
hypothesis, target defect, parameter bounds, primary metric, safety metrics,
regression tolerance, affected/unaffected subsets, abstention + rejection
conditions, rollback — **predeclared before rendering**.

| # | Experiment | Core mechanism to test |
|---|---|---|
| E1 | Harshness/fatigue | frequency-selective *dynamic* 2.5–5k attenuation (phrase-adaptive, not a static cut) |
| E2 | Phrase-level leveling | inter-phrase gain riding before compression |
| E3 | Low-mid clarity | adaptive 250–700 cut sized per phrase masking measure |
| E4 | Weak-mic/room coloration | resonance suppression + noise-floor mgmt (new module candidates → DT-77 briefs if outside registry) |
| E5 | Plosive/sibilance | detection-gated, inside safety envelope (N-014 lessons) |
| E6 | Bounded harmonic enhancement | *only after* E1–E4 stable; strict artifact penalties |
| E7 | Tonal cohesion / mastering-lite | cross-stage coordination: each stage re-measures after the previous |
| E8 | Ambience matching | optional, last, only on cleaned output |

[SAFE-NOW]: contracts + surrogate dry-runs for E1–E3. [GATED]: real-pair runs
(H1-D) and any perceptual promotion (owner listening, DT-55H).

## 8. DT-55G — Splits & anti-leakage **[policy fixed now]**

Partition **by artist**, all tracks of an artist in one partition. Honest layout
for *this* corpus: Juice WRLD pairs = development; Tecca + LAROI (+ any later
additions) = untouched holdout; leave-one-pair-out within development.
**Mandatory caveat in every report:** holdout is tiny and single-pair-per-artist —
results indicate transfer, they do not prove generalization (that needs the
commissioned corpus / DT-62). `leakage_conflicts` (already built) enforces the
split; phrases never cross partitions.

## 9. DT-55H — Owner review protocol **[GATED: owner listening]**

Reuse DT-56 verbatim: blinded `Assignment` (A/B/C/D = raw / champion / candidate /
wet reference; sides randomized, loudness-matched via `ab_export`), responses in
the immutable schema, per-axis ratings (harshness, clarity, body, mic-quality,
consistency, naturalness, cohesion, closeness-to-wet, overall) — not just
"better?". Owner = exploratory evidence (N-009 rule); promotion to *evaluation
candidate* allowed, champion promotion still requires the DT-57→60 study line.

## 10. Evidence, claims, and honesty rails

- Owner listening 2026-07-24 recorded as **E-OWN-001** (exploratory):
  *subtle, clearly-audible improvement over raw; far below studio; fatiguing;
  insufficient clarity/cohesion; retains weak-mic character.* No public or
  confirmatory claim; "studio quality" stays quarantined.
- Every artifact from gated audio lives under gitignored paths
  (`data/restricted/`, `reports/` entries reference metrics only, never bundle
  audio). Nothing from the private corpus is ever pushed.
- Scorecard/deficiency updates only with evidence; DEF-003 stays gated (this
  corpus does NOT satisfy it — rights + representativeness both fail).

## 11. Execution checklist for the next agent

1. [SAFE-NOW] DT-55A manifest script + tests → run on the folder → verify 31
   files, 1 dup, 2 rejected, rest `blocked_pending_H1D`.
2. [SAFE-NOW] `src/paired_corpus/` surrogates → pairing → alignment → deltas →
   oracle harness, each with its test batch green before the next.
3. [SAFE-NOW] E1–E3 contracts + surrogate dry-runs; extend registry only via
   DT-77 briefs for missing modules (dereverb, resonance suppression, harmonic
   enhancement).
4. Full suite + drift check green → commit → push → CI green (per milestone).
5. **STOP** at: H1-D ruling (real-corpus processing), any spend (commissioned
   corpus), owner listening session. Update
   `control/CONSOLIDATED_HUMAN_DECISION_H1_STUDY.md` if new human choices emerge.
