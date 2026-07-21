"""Generate the reviewed metric-applicability registry (DT-47).

Constructs one card per current metric from category templates plus
metric-specific overrides, then writes the canonical JSON registry. Run:

    python scripts/build_metric_registry.py

Honesty rules encoded here:
- Loudness/level metrics are `comparability`, never quality (loudness-as-quality
  is a prohibited interpretation).
- Defect/perception metrics carry **no** perceptual threshold — status `unset`
  pending a listening study — so they cannot produce a quality pass.
- Only true-peak carries an evidence-backed ceiling (a safety standard).
"""

import json
from pathlib import Path

from src.evaluation.metric_registry.registry import CURRENT_METRICS, METRIC_REGISTRY_PATH
from src.evaluation.metric_registry.schema import (
    METRIC_CARD_SCHEMA_VERSION,
    MetricCard,
    MetricRole,
    ReferenceRequirement,
    ThresholdStatus,
)

_NOT_QUALITY = ("not_a_musical_quality_verdict",)
_LOUDNESS_PROHIBIT = ("loudness_is_not_quality", "louder_is_not_better")
_METRIC_MOVE_PROHIBIT = (
    "metric_movement_is_not_perceived_improvement",
    "requires_independent_listening_validation",
)

# metric_id -> (role, unit, direction, extra overrides dict)
_SPEC: dict[str, tuple[MetricRole, str, int, dict]] = {
    # --- signal safety ---
    "clipping_ratio": (MetricRole.SIGNAL_SAFETY, "ratio", -1, {
        "meaningful_threshold": 0.001, "threshold_status": ThresholdStatus.OPERATIONAL,
        "failure_modes": ("intersample_peaks_missed",), "prohibited_interpretations": _NOT_QUALITY}),
    "clip_flag_ratio": (MetricRole.SIGNAL_SAFETY, "ratio", -1, {"prohibited_interpretations": _NOT_QUALITY}),
    "dc_offset": (MetricRole.SIGNAL_SAFETY, "amplitude", -1, {"prohibited_interpretations": _NOT_QUALITY}),
    "peak_dbfs": (MetricRole.SIGNAL_SAFETY, "dBFS", 0, {"prohibited_interpretations": _NOT_QUALITY}),
    "true_peak_dbtp": (MetricRole.SIGNAL_SAFETY, "dBTP", 0, {
        "meaningful_threshold": -1.0, "threshold_status": ThresholdStatus.EVIDENCE_BACKED,
        "threshold_evidence": "ITU-R BS.1770-4 true-peak; common -1 dBTP delivery ceiling",
        "prohibited_interpretations": _NOT_QUALITY}),
    "headroom_db": (MetricRole.SIGNAL_SAFETY, "dB", 1, {"prohibited_interpretations": _NOT_QUALITY}),
    "headroom_min_db": (MetricRole.SIGNAL_SAFETY, "dB", 1, {"prohibited_interpretations": _NOT_QUALITY}),
    "silence_percentage": (MetricRole.DESCRIPTIVE, "percent", 0, {}),
    "silence_frame_dbfs": (MetricRole.DESCRIPTIVE, "dBFS", 0, {}),
    "duration_seconds": (MetricRole.DESCRIPTIVE, "seconds", 0, {}),
    # --- loudness / comparability ---
    "rms_dbfs": (MetricRole.COMPARABILITY, "dBFS", 0, {"prohibited_interpretations": _LOUDNESS_PROHIBIT}),
    "integrated_lufs": (MetricRole.COMPARABILITY, "LUFS", 0, {
        "threshold_status": ThresholdStatus.OPERATIONAL,
        "prohibited_interpretations": _LOUDNESS_PROHIBIT,
        "uncertainty_method": "bs1770_gated"}),
    "level_high_lufs": (MetricRole.COMPARABILITY, "LUFS", 0, {"prohibited_interpretations": _LOUDNESS_PROHIBIT}),
    "level_low_lufs": (MetricRole.COMPARABILITY, "LUFS", 0, {"prohibited_interpretations": _LOUDNESS_PROHIBIT}),
    "advisory_integrated_lufs": (MetricRole.COMPARABILITY, "LUFS", 0, {"prohibited_interpretations": _LOUDNESS_PROHIBIT}),
    # --- defect evidence (perceptual thresholds unset) ---
    "harshness_ratio": (MetricRole.DEFECT_EVIDENCE, "ratio", -1, {"prohibited_interpretations": _METRIC_MOVE_PROHIBIT}),
    "mud_ratio": (MetricRole.DEFECT_EVIDENCE, "ratio", -1, {"prohibited_interpretations": _METRIC_MOVE_PROHIBIT}),
    "sibilance_frame_p95": (MetricRole.DEFECT_EVIDENCE, "ratio", -1, {"prohibited_interpretations": _METRIC_MOVE_PROHIBIT}),
    "sibilance_ratio": (MetricRole.DEFECT_EVIDENCE, "ratio", -1, {"prohibited_interpretations": _METRIC_MOVE_PROHIBIT}),
    "rumble_fraction": (MetricRole.DEFECT_EVIDENCE, "fraction", -1, {"prohibited_interpretations": _METRIC_MOVE_PROHIBIT}),
    "noise_floor_dbfs": (MetricRole.DEFECT_EVIDENCE, "dBFS", -1, {"prohibited_interpretations": _METRIC_MOVE_PROHIBIT}),
    "air_ratio": (MetricRole.DEFECT_EVIDENCE, "ratio", 1, {"prohibited_interpretations": _METRIC_MOVE_PROHIBIT}),
    "envelope_floor_ratio": (MetricRole.DEFECT_EVIDENCE, "ratio", -1, {"prohibited_interpretations": _METRIC_MOVE_PROHIBIT}),
    "decay_db_per_s": (MetricRole.DEFECT_EVIDENCE, "dB/s", 1, {
        "prohibited_interpretations": ("reverb_is_advisory_not_removable",) + _METRIC_MOVE_PROHIBIT}),
    "hum_contrast": (MetricRole.DEFECT_EVIDENCE, "dB", -1, {"prohibited_interpretations": _METRIC_MOVE_PROHIBIT}),
    "plosive_rate_per_min": (MetricRole.DEFECT_EVIDENCE, "per_min", -1, {"prohibited_interpretations": _METRIC_MOVE_PROHIBIT}),
    "consistency_cv": (MetricRole.DEFECT_EVIDENCE, "cv", -1, {"prohibited_interpretations": _METRIC_MOVE_PROHIBIT}),
    # --- descriptive ---
    "centroid_hz": (MetricRole.DESCRIPTIVE, "Hz", 0, {}),
    "hum_base_hz": (MetricRole.DESCRIPTIVE, "Hz", 0, {}),
    "hum_harmonic_count": (MetricRole.DESCRIPTIVE, "count", 0, {}),
    "crest_factor_db": (MetricRole.DESCRIPTIVE, "dB", 0, {"prohibited_interpretations": _NOT_QUALITY}),
    "dynamic_range_db": (MetricRole.DESCRIPTIVE, "dB", 0, {"prohibited_interpretations": _NOT_QUALITY}),
    "advisory_crest_factor_db": (MetricRole.DESCRIPTIVE, "dB", 0, {"prohibited_interpretations": _NOT_QUALITY}),
    "advisory_dynamic_range_db": (MetricRole.DESCRIPTIVE, "dB", 0, {"prohibited_interpretations": _NOT_QUALITY}),
    # --- full-reference (valid only with clean, aligned reference) ---
    "si_sdr": (MetricRole.REFERENCE, "dB", 1, {
        "reference_requirement": ReferenceRequirement.ALIGNED_PAIR,
        "failure_modes": ("silent_reference_nan", "misalignment_biases_score"),
        "prohibited_interpretations": ("not_perceptual_quality", "valid_only_with_valid_reference"),
        "license": "first_party_impl_of_le_roux_2019"}),
    "segmental_snr": (MetricRole.REFERENCE, "dB", 1, {
        "reference_requirement": ReferenceRequirement.ALIGNED_PAIR,
        "failure_modes": ("silent_frames_excluded", "misalignment_biases_score"),
        "prohibited_interpretations": ("not_perceptual_quality", "valid_only_with_valid_reference")}),
}


def build_cards() -> list[MetricCard]:
    cards: list[MetricCard] = []
    for metric_id in CURRENT_METRICS:
        role, unit, direction, extra = _SPEC[metric_id]
        cards.append(MetricCard(metric_id=metric_id, role=role, unit=unit, direction=direction, **extra))
    return cards


def main() -> None:
    missing = [m for m in CURRENT_METRICS if m not in _SPEC]
    if missing:
        raise SystemExit(f"no card spec for: {missing}")
    cards = build_cards()
    payload = {
        "schema": "drakotune.metric_registry",
        "schema_version": METRIC_CARD_SCHEMA_VERSION,
        "generated_for_milestone": "DT-47",
        "note": (
            "Reviewed metric applicability cards. Loudness/level metrics are "
            "comparability only; defect/perception thresholds are intentionally "
            "unset pending a listening study; only true-peak carries an "
            "evidence-backed safety ceiling."
        ),
        "cards": [c.to_dict() for c in cards],
    }
    out = Path(METRIC_REGISTRY_PATH)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(cards)} cards to {out}")


if __name__ == "__main__":
    main()
