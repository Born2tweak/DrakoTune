"""Corpus requirements mapped to the accepted DT-54 launch strata (DT-55).

Each launch-critical stratum (D-028) becomes a costed acquisition requirement with
a target count and an intended evaluation purpose. Targets derive from DT-54's
coverage matrix (``min_coverage``). No asset is acquired here (Field 8/22): this
only states *what* rights-clean evidence each stratum needs.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.product_taxonomy import RECOMMENDED_COVERAGE, Dimension, Priority


class Purpose(str, Enum):
    """Distinct rights purposes (mirrors src.rights purposes vocabulary)."""

    INTERNAL_EVALUATION = "internal_evaluation"
    LISTENING_STUDY = "listening_study"
    PUBLIC_EXAMPLE = "public_example"
    MODEL_TRAINING = "model_training"


@dataclass(frozen=True)
class CorpusRequirement:
    dimension: str
    value: str
    target_count: int
    purpose: Purpose
    leakage_group: str
    rationale: str = ""


def launch_requirements(
    purpose: Purpose = Purpose.LISTENING_STUDY,
) -> tuple[CorpusRequirement, ...]:
    """One requirement per launch-critical DT-54 stratum, target = its min_coverage."""
    reqs = []
    for entry in RECOMMENDED_COVERAGE:
        if entry.priority is Priority.LAUNCH_CRITICAL:
            reqs.append(CorpusRequirement(
                entry.dimension.value, entry.value, entry.min_coverage,
                purpose, entry.leakage_group, entry.rationale,
            ))
    return tuple(reqs)


def total_target(purpose: Purpose = Purpose.LISTENING_STUDY) -> int:
    """Sum of per-stratum targets (an upper envelope, not a distinct-asset count)."""
    return sum(r.target_count for r in launch_requirements(purpose))
