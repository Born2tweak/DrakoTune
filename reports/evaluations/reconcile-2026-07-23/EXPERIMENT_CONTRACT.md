# DSP Experiment Contract — sibilance de-essing (predeclared)

**Predeclared:** 2026-07-23, BEFORE any candidate render (D0). Thresholds below are
fixed; results are judged against them, not vice-versa. Objective-only; no
perceptual claim (guardrail 1). Bounded reconciliation spike — NOT a DT-80 promotion.

## Selected defect
Sibilance (band 5.5–12 kHz), family `sibilance` in corpus-v1. Chosen because the
committed benchmark shows the champion (v2) barely changes the sibilance defect
band (Δdefect-band ≈ +0.001 at moderate), and inspection shows the champion emits
**0 actions** on sibilance samples (safe abstention).

## Hypothesis
The champion under-treats synthetic sibilance because (a) measured
`sibilance_frame_p95 ≈ 0.088` sits below the DeEsser's minimum in-range
`frame_threshold` (0.10), and (b) de-essing is otherwise only added as a
post-compression guard, which does not fire when no compressor is planned. A
bounded, in-range de-esser applied directly should be tested for whether it
reduces the measured sibilance band without harming other content.

## Treatment (bounded, within EXISTING safe ranges)
Apply `src/dsp_engine/deesser.de_ess` to the champion output at the most aggressive
in-range setting: `frame_threshold = 0.10`, `max_reduction_db = 10.0`
(safe ranges: frame_threshold ∈ [0.10, 0.50], max_reduction_db ∈ [2, 10]).
No range is widened. Original files never overwritten.

## Metrics
- **Primary:** relative reduction of the loudness-matched sibilance defect-band
  ratio on sibilance samples: `1 − (defect_band_out_candidate / defect_band_out_champion)`.
- **Secondary safety:** output_peak, output_clipping_ratio, SI-SDR (preservation
  indicator — NOT a quality score), segmental SNR.

## Predeclared thresholds
- **Improvement (promote-worthy):** ≥ 20% relative sibilance-band reduction on
  sibilance samples (mean).
- **Regression tolerance (do-no-harm):** on every NON-sibilance family and on the
  3 clean CC-BY real clips, candidate must keep `output_clipping_ratio == 0`,
  `output_peak ≤ 0.977` (−0.2 dBFS ceiling), and `SI-SDR_out_candidate ≥
  SI-SDR_out_champion − 0.5 dB`.
- **Abstention condition:** if the treatment acts on < 1% of frames (near-transparent)
  it is reported as correctly-abstained, not a failure.
- **Rejection condition:** improvement < 20% OR any do-no-harm breach.

## Outcome lanes (predeclared, per correction #6)
- **Engineering promotion:** only if the objectively-defined sibilance band passes
  the improvement threshold AND all do-no-harm holds. (De-essing is tonal, so even
  then it would normally graduate to an evaluation candidate — noted.)
- **Evaluation candidate:** measurable sibilance reduction that changes tonal
  character; may proceed to a future listening study, cannot become champion on
  metrics alone.
- **Negative / deferred result:** improvement below threshold within existing
  ranges → documented in NEGATIVE_RESULTS with a concrete improvement brief.

## Rollback
Experiment is non-destructive: it renders to `reports/evaluations/reconcile-2026-07-23/`
and changes no production code or champion behavior. Nothing to roll back unless a
change is later promoted via a separate PR.

## Audio provenance (validated before running)
Real clips: `fixtures/audio_real/PROVENANCE.yaml` (3× CC BY 4.0, checksummed).
Synthetic corpus: `data/derived/corpus-v1/` (self-generated from the same CC-BY sources).
