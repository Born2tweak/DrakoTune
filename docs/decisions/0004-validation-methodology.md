# ADR 0004 — Validation methodology: loudness-matched blinded A/B with pre-registered criteria

- **Status:** accepted (2026-07-10)
- **Context:** DrakoTune's core claims ("smoother, less harsh, cleaner, more listenable") are perceptual. Signal metrics cannot prove them; unmatched loudness biases listeners toward the louder version; developer listening is unblinded and biased. No listening evidence exists yet (M17 completion note; post-research audit Track A).
- **Decision:**
  1. **Loudness matching is mandatory** before any A/B comparison, human or metric: both stimuli at −23 LUFS integrated, true peak ≤ −1.5 dBTP, pairs rejected if post-match difference > 0.5 LU.
  2. **Perceptual claims require blinded pairwise A/B tests** with randomized order, ≥ 10% identical catch trials, clean-input do-no-harm pairs, ≥ 8 non-developer listeners, and **pre-registered** success criteria (validation plan §6) fixed before data collection.
  3. **Metric roles are fixed:** EBU R128/true-peak/band-ratios/crest = diagnosis + regression; SI-SDR/segmental SNR = reference-based fidelity on paired data; DNSMOS/NISQA/ViSQOL = optional developer-only proxies, labeled speech-trained, never product-facing, never cited as proof of singing quality; MUSHRA reserved for later formal benchmarking.
  4. **Every listening response is logged** in a versioned schema (no PII, no audio) as the seed of the future preference dataset.
- **Consequences:** claims lag capability (correct for credibility); a small tooling investment (M23/M24) before any further DSP tuning (M26).
- **Superseded if:** a validated singing-quality metric with published human correlation on recorded vocals emerges — it may then supplement, not replace, listening.
