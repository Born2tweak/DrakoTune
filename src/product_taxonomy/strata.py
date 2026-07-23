"""Stratum labels, multilabel assignments, and the priority/coverage matrix (DT-54).

Immutable value types (frozen dataclasses) per the project's immutability rule.
Nothing here decides which strata are launch-critical — that is the Q-014 human
gate. ``RECOMMENDED_COVERAGE`` is a *proposal* for the owner + audio lead to
accept, amend, or reject; it carries no claim authority until they sign off.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from src.product_taxonomy.vocabulary import Dimension


class Priority(str, Enum):
    """Launch priority of a stratum. Only a human may set LAUNCH_CRITICAL (Q-014)."""

    LAUNCH_CRITICAL = "launch_critical"
    SECONDARY = "secondary"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass(frozen=True)
class StratumLabel:
    """One observed (dimension, value) with confidence in [0, 1]."""

    dimension: Dimension
    value: str
    confidence: float = 1.0

    def is_low_confidence(self, threshold: float = 0.5) -> bool:
        return self.confidence < threshold


@dataclass(frozen=True)
class StratumAssignment:
    """Multilabel assignment for one audio asset across all dimensions.

    ``labels`` may hold several entries for a MULTILABEL dimension. A dimension
    with no entry is treated as ``unknown`` by the validator, never as a pass.
    """

    asset_id: str
    labels: tuple[StratumLabel, ...] = ()
    taxonomy_version: str = ""

    def values(self, dimension: Dimension) -> tuple[str, ...]:
        return tuple(l.value for l in self.labels if l.dimension == dimension)


@dataclass(frozen=True)
class CoverageEntry:
    """Coverage rule for one launch stratum.

    ``leakage_group`` names the grouping key (e.g. singer/session) that must not
    be split across train/eval — grouped-split leakage control for DT-63.
    """

    dimension: Dimension
    value: str
    priority: Priority
    min_coverage: int
    leakage_group: str
    rationale: str = ""

    def counts_for_confirmatory(self) -> bool:
        """Only launch-critical strata with a real minimum count anchor claims."""
        return self.priority is Priority.LAUNCH_CRITICAL and self.min_coverage > 0


# Standard leakage grouping: never split the same performer/session across splits.
DEFAULT_LEAKAGE_GROUP = "performer_session"

# RECOMMENDED (non-binding) coverage proposal for the Q-014 human decision.
# The owner + audio lead set the final LAUNCH_CRITICAL set; this is a starting
# point grounded in the D-A promise (dry rap/pop lead vocal, English-first).
RECOMMENDED_COVERAGE: tuple[CoverageEntry, ...] = (
    CoverageEntry(Dimension.GENRE, "rap", Priority.LAUNCH_CRITICAL, 12,
                  DEFAULT_LEAKAGE_GROUP, "Core D-A target."),
    CoverageEntry(Dimension.GENRE, "melodic_rap", Priority.LAUNCH_CRITICAL, 12,
                  DEFAULT_LEAKAGE_GROUP, "Dominant contemporary style; sung+rapped."),
    CoverageEntry(Dimension.GENRE, "pop", Priority.LAUNCH_CRITICAL, 12,
                  DEFAULT_LEAKAGE_GROUP, "Core D-A target."),
    CoverageEntry(Dimension.GENRE, "sung_rap", Priority.SECONDARY, 6,
                  DEFAULT_LEAKAGE_GROUP, "Overlaps melodic_rap; secondary at launch."),
    CoverageEntry(Dimension.VOCAL_PRESENTATION, "spoken_rapped", Priority.LAUNCH_CRITICAL, 12,
                  DEFAULT_LEAKAGE_GROUP, "Primary rap delivery."),
    CoverageEntry(Dimension.VOCAL_PRESENTATION, "melodic", Priority.LAUNCH_CRITICAL, 12,
                  DEFAULT_LEAKAGE_GROUP, "Primary pop/melodic-rap delivery."),
    CoverageEntry(Dimension.VOCAL_PRESENTATION, "ad_lib", Priority.SECONDARY, 6,
                  DEFAULT_LEAKAGE_GROUP, "Common but layered; harder to evaluate in isolation."),
    CoverageEntry(Dimension.VOCAL_PRESENTATION, "layered_stacked", Priority.OUT_OF_SCOPE, 0,
                  DEFAULT_LEAKAGE_GROUP, "Not a single dry lead vocal (D-A out of scope)."),
    CoverageEntry(Dimension.LANGUAGE, "english", Priority.LAUNCH_CRITICAL, 18,
                  DEFAULT_LEAKAGE_GROUP, "English-first launch."),
    CoverageEntry(Dimension.LANGUAGE, "spanish", Priority.SECONDARY, 6,
                  DEFAULT_LEAKAGE_GROUP, "Large rap/pop share; secondary at launch."),
    CoverageEntry(Dimension.LANGUAGE, "multilingual_code_switch", Priority.SECONDARY, 6,
                  DEFAULT_LEAKAGE_GROUP, "Explicit label so it is never mislabeled as one language."),
    CoverageEntry(Dimension.RECORDING_CONDITION, "home_untreated", Priority.LAUNCH_CRITICAL, 12,
                  DEFAULT_LEAKAGE_GROUP, "The core non-engineer user's condition."),
    CoverageEntry(Dimension.RECORDING_CONDITION, "studio_treated", Priority.SECONDARY, 6,
                  DEFAULT_LEAKAGE_GROUP, "Cleaner baseline; less defect-relevant."),
    CoverageEntry(Dimension.RECORDING_CONDITION, "plosive_prone", Priority.LAUNCH_CRITICAL, 8,
                  DEFAULT_LEAKAGE_GROUP, "Defect-relevant; common in home capture."),
    CoverageEntry(Dimension.RECORDING_CONDITION, "sibilant_prone", Priority.LAUNCH_CRITICAL, 8,
                  DEFAULT_LEAKAGE_GROUP, "Defect-relevant (see N-014 de-ess finding)."),
)
