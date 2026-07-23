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

## N-014 — Blanket in-range de-essing is net-harmful; the champion's abstention is correct

2026-07-23 reconciliation experiment (`scripts/experiments/exp_2026_07_23_sibilance_deesser.py`, contract + `results.json` under `reports/evaluations/reconcile-2026-07-23/`). Applying the DeEsser at its most aggressive **in-range** setting (`frame_threshold=0.10`, `max_reduction_db=10`) to every champion output reduced the sibilance defect band by 26.1% on the 12 sibilance pairs (passed the predeclared ≥20% bar) but **failed do-no-harm**: SI-SDR regressed on 22/148 non-sibilant clips (median −8.6 dB, worst −42 dB; concentrated in low_level ×12, harshness ×4, codec ×4), and because the treatment ran *after* the executor's −0.2 dBFS ceiling it pushed peaks above unity on hard-clipped inputs (vocadito_16: 0.977 → 1.117) and increased clipping on that clip. Conclusion: the champion's decision-gated abstention from de-essing is **vindicated** — a blanket de-ess trades a small sibilance gain for large fidelity loss and a safety-ceiling breach. Any real sibilance improvement must be (1) gated on reliable per-clip sibilance detection (never applied to low_level/codec/harshness), (2) executed **inside** the output-safety envelope (re-apply the ceiling), and (3) preceded by a separately-validated lowering of the de-ess frame floor, since synthetic sibilance p95 (~0.088) sits below the current 0.10 floor. Verdict: **rejected**; logged as the DT-77 improvement brief seed.
