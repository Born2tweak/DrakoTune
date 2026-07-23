"""Versioned target-strata vocabulary (DT-54, autonomous portion).

The vocabulary is the single source of truth for the *observable* strata the
product's evaluation is allowed to name. Every dimension is an observable audio /
performance / language / recording property — never a demographic or otherwise
sensitive personal category (Field 18/22). ``UNKNOWN`` and ``NOT_APPLICABLE`` are
first-class values in every dimension: a stratum that cannot be observed is never
silently forced into a positive label.

Bump ``TAXONOMY_VERSION`` and add a migration in ``validate.migrate_assignment``
whenever a label is renamed or removed; unknown labels are schema errors, never
silent aliases.
"""
from __future__ import annotations

from enum import Enum

TAXONOMY_VERSION = "1.0.0"

# Sentinels present in EVERY dimension.
UNKNOWN = "unknown"
NOT_APPLICABLE = "not_applicable"


class Dimension(str, Enum):
    """The four observable stratification axes (D-A scope: dry lead vocal)."""

    GENRE = "genre"
    VOCAL_PRESENTATION = "vocal_presentation"
    LANGUAGE = "language"
    RECORDING_CONDITION = "recording_condition"


# Observable labels per dimension. Sentinels (UNKNOWN/NOT_APPLICABLE) are always
# valid and are appended by ``labels_for`` rather than duplicated here.
_LABELS: dict[Dimension, tuple[str, ...]] = {
    # Genre stays inside the D-A rap/pop family; ambiguous input -> UNKNOWN.
    Dimension.GENRE: (
        "rap",
        "melodic_rap",
        "sung_rap",
        "pop",
        "rap_pop_hybrid",
    ),
    # Observable performance style. MULTILABEL: a take can be rapped + ad_lib.
    Dimension.VOCAL_PRESENTATION: (
        "spoken_rapped",
        "sung_sustained",
        "melodic",
        "belted",
        "falsetto",
        "whisper",
        "layered_stacked",
        "ad_lib",
        "harmony",
    ),
    # Self-reported / script-derived only; never inferred from voice timbre.
    Dimension.LANGUAGE: (
        "english",
        "spanish",
        "multilingual_code_switch",
        "other",
    ),
    # Observable capture conditions (defect-relevant), not environment guesses.
    # MULTILABEL: home_untreated + plosive_prone + low_snr can co-occur.
    Dimension.RECORDING_CONDITION: (
        "studio_treated",
        "home_untreated",
        "mobile_device",
        "plosive_prone",
        "sibilant_prone",
        "room_reflective",
        "low_snr",
        "clipped_input",
    ),
}

# Dimensions where more than one positive label may co-occur on one take.
MULTILABEL_DIMENSIONS: frozenset[Dimension] = frozenset(
    {Dimension.VOCAL_PRESENTATION, Dimension.RECORDING_CONDITION}
)

# Sensitive categories that must NEVER become dimensions or labels (Field 18/22).
# Used by the validator's sensitive-proxy guard.
FORBIDDEN_SENSITIVE_TERMS: frozenset[str] = frozenset({
    "gender", "sex", "age", "race", "ethnicity", "ethnic", "nationality",
    "accent", "religion", "orientation", "disability", "skin", "gender_identity",
})


def labels_for(dimension: Dimension) -> tuple[str, ...]:
    """Positive observable labels plus the two universal sentinels."""
    return _LABELS[dimension] + (UNKNOWN, NOT_APPLICABLE)


def is_known_label(dimension: Dimension, value: str) -> bool:
    return value in labels_for(dimension)


def is_sentinel(value: str) -> bool:
    return value in (UNKNOWN, NOT_APPLICABLE)
