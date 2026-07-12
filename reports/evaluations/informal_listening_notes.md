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
