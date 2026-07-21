# G — Enhancement and Assessment Models Report

**As of:** 2026-07-21  
**Sources:** S-C01–S-C04, S-E05–S-E06.

## Candidate posture

| Candidate | Potential role | Current disposition |
|---|---|---|
| DeepFilterNet | Noise-reduction challenger | Sandbox only; speech domain, 48 kHz assumptions, singing/weights/data review needed. |
| RNNoise | Lightweight denoising challenger | Sandbox only; speech/noise domain and artifact tests required. |
| Demucs | Optional context/separation experiment | Defer; repository archived, maintenance and separation artifacts are material. |
| ViSQOL | Full-reference observation for legitimate clean-reference tasks | Observation only; validate domain and alignment. |
| NISQA | Exploratory speech-quality observation | Reject for production gate: non-commercial weights and communications domain. |
| PEAQ | Controlled codec/device impairment observation | Not an overall vocal-mix score. |

## Gate sequence

License/terms → input and reference applicability → deterministic harness → singing-vocal adversarial set → collateral-artifact analysis → independent listening → resource budget → rollback. A candidate that fails an early gate does not proceed merely because a later demo sounds promising.

## Decision

No new model belongs in the production runtime before the evidence system is rebuilt. Candidate outputs must never overwrite originals and must be labeled with exact code, weights, data-card, and runtime identities.

## Component-level evidence audit

| Candidate | Primary domain/input | Component-rights evidence | Main applicability risk | Gate/recheck |
|---|---|---|---|---|
| S-C01 DeepFilterNet | 48 kHz speech enhancement/noise suppression | Official repository identifies Apache-2.0/MIT code posture; weights/data must still be recorded separately. | Singing tone, breath, sustained harmonics, ad-libs, and music bleed may create artifacts outside speech evaluation. | Sandbox singing-vocal artifact set before any preference test. |
| S-C02 Demucs | Music source separation | Official repository is MIT and archived as of 2025-01-01. | Separation artifacts, maintenance/compatibility risk, and full-song context differ from isolated lead cleanup. | Defer unless product scope needs context/separation and maintenance is adopted. |
| S-C03 RNNoise | Lightweight real-time speech denoising | BSD-3-Clause repository. | Speech/noise model may suppress vocal texture, breaths, doubles, and tonal material. | Challenger only with singing-specific do-no-harm study. |
| S-C04 NISQA | Speech-quality prediction for communications | Code MIT; model weights recorded as CC BY-NC-SA 4.0. | Non-commercial weights and speech-communications construct are incompatible with a commercial general vocal-quality gate. | Observation-only research; reject as production criterion. |
| S-E06 ViSQOL | Full-reference speech/audio similarity | Apache-2.0 implementation and official documentation. | Requires a legitimate aligned reference; score meaning may not transfer to creative processing. | Register only on known-reference repair tasks. |
| S-E05 PEAQ | Full-reference perceptual impairment | ITU standard defines method and limitations. | Creative dry/wet transformation violates the implied device-under-test comparison. | No overall mix score; consider codec-like fixtures only. |

## Negative-transfer test set

Any speech-derived enhancer must be challenged with sung vowels, falsetto, fry, breaths, consonants, stacked doubles, pitch correction, reverb tails, clipped consonants, quiet entrances, music bleed, and language/voice diversity. A noise score gain with identity/timbre/artifact harm is a failed candidate.
