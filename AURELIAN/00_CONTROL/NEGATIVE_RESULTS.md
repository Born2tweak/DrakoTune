# Negative Results and Invalidated Assumptions

These results are retained to prevent repetition and survivorship bias.

## N-001 — Objective pass did not imply globally better audio

On the repository’s `harsh.wav` fixture, the v2 pipeline met two target-movement objectives while reporting residual harshness/noise, a +0.0074 rise in sibilant-frame p95, a +5.2135 rise in mud ratio, and -1.2 LU loudness change. Conclusion: target metric movement alone is not a quality verdict.

## N-002 — One listener can satisfy the former sample gate

Eight duplicate rows from one listener on one harshness trial were counted as `n=8` and produced `p=0.0039`, passing the former gate. Conclusion: row count is not independent sample size.

## N-003 — Clean-vocal harm can pass

Eight distinct listeners preferring the original clean vocal over the processed version yielded a processed-preference rate of 0.0 and passed the former do-no-harm rule. Conclusion: “processed not preferred” is not equivalent to “no harm.”

## N-004 — Ties disappear from defect evidence

Unanimous ties omitted a defect result, produced a clean processed-preference rate of 0.0, passed do-no-harm, and yielded agreement 1.0. Conclusion: ties must be modeled and reported explicitly.

## N-005 — Panel disagreement is hidden

Experts unanimously preferring original and general listeners unanimously preferring processed collapsed to a 50% aggregate without a panel interaction result. Conclusion: panel strata cannot be pooled without a prespecified estimand.

## N-006 — Side/order bias is not detected

All respondents choosing side A can pass when processed audio is always assigned to A. Conclusion: assignment balancing and side/order diagnostics are mandatory.

## N-007 — Synthetic benchmark performance is not uniformly positive

Current corpus-v2 benchmark cells include mixed or negative SI-SDR changes and six errored pairs. Conclusion: do not summarize the corpus with a blanket improvement claim.

## N-008 — Synthetic calibration exhibits large false-positive rates

Recorded calibration examples include reverb 41.2%, hum 21.2%, and noise 22.5% false-positive rates. Conclusion: detector thresholds are not launch-calibrated.

## N-009 — Informal owner listening is not independent validation

Existing informal listener records are useful product discovery only. They cannot establish professional preference, target-user benefit, or do-no-harm.

## N-010 — Public availability does not establish usable rights

MedleyDB and much of MUSDB are non-commercial; Cambridge downloads are offered for practice under per-track/term constraints; research code licenses do not grant dataset or model-weight rights. Conclusion: use-purpose rights must be recorded separately.

## N-011 — Speech-enhancement success is not vocal-mixing validity

DeepFilterNet, RNNoise, ViSQOL, NISQA, and related tools target speech/noise or communications domains. Conclusion: they remain candidates only after singing-vocal applicability tests.

## N-012 — Current memory design does not scale comfortably

Historical performance evidence indicates linear memory near 180 MB per audio minute and around 900 MB for five minutes, with two MemoryErrors recorded. Conclusion: desktop scope needs duration limits or streaming/chunking.

## N-013 — Exact environment cannot be reconstructed from project metadata

Dependencies have lower bounds but no lockfile; FFmpeg build options are external. Conclusion: software version plus build/license fingerprint must be evidence metadata.
