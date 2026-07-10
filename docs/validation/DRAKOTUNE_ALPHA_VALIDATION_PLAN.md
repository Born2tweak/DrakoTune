# DrakoTune Alpha Validation Plan

> How we answer the product question with evidence:
> *"Can deterministic processing make poor raw vocals sound noticeably smoother,
> less harsh, cleaner, and more professionally listenable — without unacceptable
> artifacts?"*
> Derived from `docs/research/PUBLIC_VOCAL_AUDIO_DATASET_RESEARCH.md` (§29) and
> the post-research audit. Status: adopted 2026-07-10. Executed by M22–M24.

## 1. Evaluation corpus (M22)

| Component | Source | Tier | Role |
|---|---|---|---|
| Clean substrates | VocalSet (~20 clips across singers/techniques), Vocadito (all 40) | A | degradation inputs; do-no-harm inputs |
| Real degraded + clean refs | SingVERSE (~100 pairs sampled across its 19 scenarios) | B (verify at download) | reference-based validation on real degradations |
| Paired speech control | VoiceBank-DEMAND (~50 pairs across SNRs) | A | gate/noise calibration sanity (speech caveat recorded) |
| Real amateur vocals | DAMP subset (~50 clips) — after signed agreement | B | realism panel; no-reference eval only |
| Defect gallery | 5–10 Cambridge-MT raw vocal takes | C | manual listening study only, never automated |
| Local vocals | existing `output/headlock_*` source + any owned recordings | P | immediate smoke tests (already legal) |

Corpus is frozen per version (`corpus-v1`) with a manifest; every clip 10–20 s, mono, 44.1 kHz, documented provenance.

## 2. Synthetic degradation grid (seeded, versioned recipes)

Applied to Tier A clean substrates only (outputs = Tier A derived):

| Defect family | Severities | Method (existing deps suffice) |
|---|---|---|
| Broadband/room noise | SNR 20 / 10 / 5 dB × {room tone, HVAC-like, street} (MUSAN/DEMAND beds or synthesized) | numpy mixing |
| Hum | 50/60 Hz + 3 harmonics at −40 / −30 / −20 dBFS | numpy |
| Clipping | 1% / 3% / 8% samples clipped | numpy hard/soft clip |
| Reverb | wet 15% / 30% / 50% × {small room, hall} IRs (OpenAIR / OpenSLR-28) | convolution |
| Harshness | +4 / +8 dB peak 3–5 kHz | pedalboard PeakFilter |
| Sibilance | +6 / +12 dB shelf 5.5–9 kHz | pedalboard |
| Proximity/mud | +6 dB < 250 Hz shelf | pedalboard |
| Low level | −35 / −45 LUFS input | gain |
| Codec | MP3 64 / 96 kbps round-trip | ffmpeg |

Recipes live in `fixtures/degradations/` as code + JSON manifests with RNG seeds; every degraded file is regenerable bit-exact. Honesty rule: results on synthetic defects are reported as such; real-world claims require SingVERSE/DAMP/artist evidence.

## 3. Objective metrics (M23)

- **Always (no reference):** integrated LUFS, LRA-proxy (short-term loudness spread), true peak, crest factor, clipping ratio, noise-floor dBFS, band ratios (rumble/mud/harsh/sibilance/air), centroid — all already implemented.
- **With clean reference (new):** SI-SDR (numpy, ~20 lines); segmental SNR. Optional extras behind `pip install -e ".[eval]"`: ViSQOL (Apache 2.0), DNSMOS (MIT/ONNX), NISQA (MIT) — **developer-only proxies**, never product-facing, never cited as proof of singing quality (speech-trained).
- **Gaming guards:** all comparisons run **after** loudness matching; any metric improvement accompanied by `output_clipping` or new artifacts is a failure, not a pass.

## 4. Loudness matching (mandatory before any comparison)

Both A and B stimuli normalized to **−23 LUFS integrated, true peak ≤ −1.5 dBTP** (attenuate-only where possible; record applied gain). The evaluation harness refuses to emit a listening pair whose post-match LUFS differ by > 0.5 LU. Report both matched and raw loudness deltas.

## 5. Listening-test design (M24)

- **Format:** blinded pairwise A/B, randomized order, forced choice + preference strength (1–5) + artifact checklist + free text. 10% identical catch pairs; several clean-input pairs (expect "no preference").
- **Stimuli:** ~100–150 pairs = 5 defect families × 3 severities × ~8 substrates + ~20 real-world clips.
- **Listeners:** ≥ 8, mix of developer-external artists/engineers/general listeners; listener type recorded; catch-trial failures excluded.
- **Infrastructure:** file exports + a session config JSON + response CSV schema + analysis script. No new UI required; webMUSHRA/Go Listen optional later.
- **Artifact taxonomy (checklist):** pumping, gated breath/word-tail cuts, lisp/dulled sibilance, hollow/comb tone, added noise, distortion, loss of presence/air, robotic/unnatural, timing/latency artifacts, other.

## 6. Success / failure criteria (pre-registered)

**Alpha SUCCESS requires all of:**
1. On defect families the chain targets (rumble/proximity, moderate harshness, inconsistent dynamics, low-level pause noise, low recording level): processed preferred in ≥ 65% of trials, binomial p < 0.05 vs 50%.
2. Do-no-harm: on clean inputs, processed preferred ≤ 55% *and* rated "no difference" plurality; no clean-input clip acquires a checked artifact.
3. No objective regression: true peak ≤ −1 dBTP on all outputs; SI-SDR vs clean reference does not decrease on synthetic pairs; no `output_clipping` warnings.
4. Zero pairs with ≥ 2 listeners reporting the same severe artifact at default settings.

**FAILURE (any):** preference < 55% on a targeted defect family (that family's processing is marked ineffective → M26 backlog); systematic artifact reports (gate/compressor retuning before any new feature); loudness-matching bug discovered post hoc (test void, rerun).

**Statistical plan:** per-family binomial tests + 95% CIs; overall mixed summary; inter-rater agreement (Krippendorff's α) reported; no p-hacking across families without correction (Holm).

## 7. Claims policy

**Permitted if success criteria met:** "reduces low-frequency rumble," "reduces harshness on recordings with elevated 2.5–6 kHz energy," "evens out vocal dynamics," "listeners preferred processed versions of degraded recordings in blinded, loudness-matched tests (on the tested defect types and genres)."

**Still prohibited regardless of results:** "professional quality," "studio-grade," "works for all genres/voices" (corpus is not genre-representative — rap/bedroom gap), any claim about reverb, broadband in-song noise, clipping repair, de-essing (not yet implemented as dedicated processors), any medical/voice-health statement, any claim based solely on signal metrics or speech-trained proxies.

## 8. Reporting format

`reports/evaluations/<corpus-version>/<run-id>/`: `benchmark.json` (per-clip metric records incl. the evaluation-matrix fields: vocal type, genre, register estimate, device, room, defect type+severity, input LUFS, preset, deltas), `listening_results.csv`, `summary.md` (per-defect verdicts, artifacts, pass/fail vs pre-registered criteria, claims unlocked/denied). Committed (no audio).
