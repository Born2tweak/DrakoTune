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
