"""Metric applicability registry (DT-47).

Registers, for every objective/reference/listening measure, when it is valid and
what it cannot claim. Loudness is comparability, not quality; full-reference
metrics need a valid reference; perceptual thresholds are unset pending a
listening study. An inapplicable input never yields a quality pass.
"""

from src.evaluation.metric_registry.registry import (
    CURRENT_METRICS,
    METRIC_REGISTRY_PATH,
    MetricRegistry,
    load_default_registry,
)
from src.evaluation.metric_registry.schema import (
    METRIC_CARD_SCHEMA,
    METRIC_CARD_SCHEMA_VERSION,
    MetricCard,
    MetricRole,
    ReferenceRequirement,
    ThresholdStatus,
)

__all__ = [
    "MetricCard",
    "MetricRole",
    "ReferenceRequirement",
    "ThresholdStatus",
    "MetricRegistry",
    "load_default_registry",
    "CURRENT_METRICS",
    "METRIC_REGISTRY_PATH",
    "METRIC_CARD_SCHEMA",
    "METRIC_CARD_SCHEMA_VERSION",
]
