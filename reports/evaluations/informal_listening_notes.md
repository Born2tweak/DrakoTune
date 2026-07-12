# Informal listening notes (unblinded — NOT claim evidence)

> Single-listener, unblinded impressions. Logged per PILOT.md: genuine findings
> feed the research/backlog registers, never ad-hoc threshold tweaks. Claimable
> results come only from the blinded M24 protocol.

## 2026-07-11 — project owner, via webapp (loudness-matched previews)

- **Material:** local vocal clips described as "super harsh, super highs,
  painful in the ear."
- **Positive:** clear audible difference; processing "increases the quality to
  where it doesn't hurt the ears"; sense of "space of air" between listener
  and audio while intelligibility is preserved; easier to listen to overall.
  Comparison used the M27 loudness-matched players (louder-wins bias excluded).
- **Negative / open:** output "still peaked a little bit" — residual peaking
  audible. Candidate explanations to investigate before any tuning:
  1. residual narrow harsh resonances outside the static 3.5 kHz cut
     (would point at dynamic EQ / resonance suppression — M28 candidate,
     needs per-clip spectral evidence first);
  2. transient level peaks near the −1 dBFS output ceiling (check crest
     factor / short-term peak stats on these exact clips);
  3. sibilant peaks (detector only reaches 50% strong-recall — known gap).
- **Action items:** obtain the exact clips tested → run them through
  `scripts/benchmark.py`-style before/after measurement to localize the
  residual peaks in frequency/time; then decide which M28 candidate (if any)
  the evidence supports. Recruit listeners for the prepared blinded session
  (`data/derived/listening/20260711-140616-s20260711/`) to convert this
  impression into a claimable per-defect verdict.

**Status of claims:** unchanged. This note licenses no marketing language;
it prioritizes backlog only.

## 2026-07-11 — objective follow-up on the tested pairs (3 full-length before/after files)

Measured loudness-matched (−23 LUFS) with the M23 stack. Findings:

1. **Suspect #2 (transient ceiling) EXCLUDED.** Raw after-file peaks sit at
   −0.5 to −2.2 dBFS with ~0.000% of samples within 0.5 dB of peak and crest
   factors 14.5–16.2 dB — nothing is slamming the output ceiling.
2. **Suspect #3 (sibilance) CONFIRMED as the main residual.** On all three
   processed files the sibilance diagnosis *still fires post-processing*
   (frame-p95 0.29–0.40, threshold 0.18; confidences 0.27–0.52). The 30
   loudest HF frames are dominated by 5–8 kHz content in pairs 0 and 2;
   HF energy in those hottest moments is +2.5 to +5.2 dB relative to the
   matched before. The static −3.5 dB sibilance PeakFilter is not enough
   for this material.
3. **Suspect #1 (other resonances) PARTIAL.** Pair 1's hottest frames cluster
   at 2–3 kHz (18/30) — a presence-band peak the 3.5 kHz cut doesn't center
   on. One-pair evidence; watch, don't act yet.
4. **Interesting balance effect:** at matched loudness the processed files are
   brighter overall (air band +3.9 to +5.0 dB, mud −0.6/−1.1 dB on two pairs)
   — consistent with the listener's *liked* "space of air." The brightness is
   part of the win; the sibilant *frames* are the residual problem. This
   argues for **frame-level dynamic sibilance control (a real de-esser)**,
   not a static HF cut that would kill the air along with the esses.

**Gate consequence:** the de-esser (M28 candidate list) now has (a) a
user-reported residual failure on real material, (b) objective post-processing
detector confirmation on 3/3 files, and (c) a localized frequency signature.
Remaining before implementation: the lisp-artifact gate design and a blinded
per-defect listening check per the standing evidence policy.

## 2026-07-11 — M30 resolution check on the same three files

Reprocessed the three `before` files with the M30 chain (dynamic DeEsser after
the compressor + post-compression self-gating guard):

| file | old-output sib p95 | new-output sib p95 | detector on output |
|---|--:|--:|---|
| before.wav | 0.3987 | 0.1988 | 0.05 conf (negligible) |
| before (1).wav | 0.3343 | 0.1686 | silent |
| before (2).wav | 0.2926 | 0.1620 | silent |

Mechanism finding: on 2/3 files the sibilance only emerged **after
compression** (input diagnosis could not see it) — hence the guard and the
order change (de-ess after compressor, matching
docs/research/vocal_chain_research.md). Perceptual confirmation (does the
"peaked" impression disappear without lisping?) still requires ears — next
webapp listen + the blinded M24 session.

## 2026-07-11 — independent cross-validation ("Music By Mattie" free vocal analyzer, before(2)/after(2))

Third-party analyzer reports on the same pair (its "after" identified by peak
−2.2 dB, matching our measured −2.16 dBFS). Treated as convergent signal, not
ground truth (free marketing tool, "scored against 3,054 Billboard hits,"
methodology unpublished). Points of agreement with our measurements:

1. **Input not harsh/sibilant — agreed.** Before(2): harshness 5.3% (below
   its hit range 5.9–13.1%), sibilance 3.0% (in range). Matches DrakoTune's
   input diagnosis, which fired neither issue on before(2).
2. **Residual sibilance spikes on the old output — independently confirmed.**
   Its #3 fix for the after file: "592 sibilance spikes around **6250 Hz**" —
   the exact band we localized (5–8 kHz, hottest frames) and the defect M30's
   de-esser now removes. (These PDFs predate M30.)
3. **Harshness moved INTO its hit zone after processing** (5.3% → 7.2%,
   range 5.9–13.1) — consistent with our matched-loudness +1.6 dB harsh-band
   delta reading as added presence rather than pain.
4. **NEW FINDING — slight over-compression on the output.** Its short-term
   dynamics measure: 16.4 dB (input, "right in the pocket," hits cluster
   15–17 dB) → 14.9 dB (output, "more compressed than 90% of hit vocals").
   Recommends easing off (3–6 dB gain reduction target). DrakoTune's
   dynamics objective fired on input consistency-CV and compressed material
   whose short-term dynamics were already hit-typical. **Backlog (M31
   candidate): dynamics objective should consider a target window (e.g.,
   crest/short-term-dynamics floor ~15 dB) and reduce or skip compression
   when input is already in range; add an over-compression check to
   evaluation warnings.**
5. Its remaining wishes ("more 2–5 kHz presence," "more air above 8 kHz,"
   "more body below 500 Hz") are **enhancement**, which DrakoTune
   deliberately does not do yet (cleanup-first scope).

Both DrakoTune and the external tool agree the processing preserved hit-range
loudness (−15.2 → −16.7 LUFS) and sibilance percentage while the *transient*
sibilant spikes were the real defect — which is precisely the frame-level
metric distinction M26/M30 were built on.
