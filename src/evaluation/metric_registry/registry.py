"""Metric registry: load cards, enforce completeness and applicability (DT-47).

The registry is the single lookup for "is this measurement valid here, and what
may it claim?". An unregistered metric is observation-only; an inapplicable
input never yields a quality pass.
"""

import json
from pathlib import Path

from src.evaluation.metric_registry.schema import MetricCard, ThresholdStatus

# The metrics currently emitted by the diagnostics/evaluation layer. The
# completeness test asserts the registry has a reviewed card for each.
CURRENT_METRICS: tuple[str, ...] = (
    # signal safety
    "clipping_ratio", "clip_flag_ratio", "dc_offset", "peak_dbfs", "true_peak_dbtp",
    "headroom_db", "headroom_min_db", "silence_percentage", "silence_frame_dbfs",
    "duration_seconds",
    # loudness / comparability
    "rms_dbfs", "integrated_lufs", "level_high_lufs", "level_low_lufs",
    "advisory_integrated_lufs",
    # defect evidence (spectral)
    "harshness_ratio", "mud_ratio", "sibilance_frame_p95", "sibilance_ratio",
    "rumble_fraction", "noise_floor_dbfs", "air_ratio", "centroid_hz",
    "envelope_floor_ratio", "decay_db_per_s", "hum_base_hz", "hum_contrast",
    "hum_harmonic_count", "plosive_rate_per_min",
    # dynamics
    "consistency_cv", "crest_factor_db", "dynamic_range_db",
    "advisory_crest_factor_db", "advisory_dynamic_range_db",
    # full-reference (valid only with a clean, aligned reference)
    "si_sdr", "segmental_snr",
)

METRIC_REGISTRY_PATH = (
    Path(__file__).resolve().parents[3]
    / "AURELIAN"
    / "07_DATA_AND_PROVENANCE"
    / "metric_registry"
    / "metric_cards.json"
)


class MetricRegistry:
    """A set of metric cards with completeness and applicability lookup."""

    def __init__(self, cards: list[MetricCard] | None = None) -> None:
        self._cards: dict[str, MetricCard] = {}
        for c in cards or []:
            self._cards[c.metric_id] = c

    def get(self, metric_id: str) -> MetricCard | None:
        return self._cards.get(metric_id)

    def is_registered(self, metric_id: str) -> bool:
        return metric_id in self._cards

    def all(self) -> tuple[MetricCard, ...]:
        return tuple(self._cards.values())

    def missing_cards(self, required: tuple[str, ...] = CURRENT_METRICS) -> tuple[str, ...]:
        return tuple(m for m in required if m not in self._cards)

    def unset_threshold_metrics(self) -> tuple[str, ...]:
        return tuple(
            c.metric_id
            for c in self._cards.values()
            if c.threshold_status is ThresholdStatus.UNSET
        )

    def can_support_quality_verdict(self, metric_id: str) -> bool:
        card = self._cards.get(metric_id)
        return bool(card and card.can_support_quality_verdict())

    def to_list(self) -> list[dict]:
        return [c.to_dict() for c in self._cards.values()]

    @classmethod
    def from_json_file(cls, path: str | Path = METRIC_REGISTRY_PATH) -> "MetricRegistry":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([MetricCard.from_dict(c) for c in data["cards"]])


def load_default_registry() -> MetricRegistry:
    return MetricRegistry.from_json_file()
