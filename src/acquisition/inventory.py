"""Rights-clean audio inventory + coverage-gap analysis (DT-55).

Records only assets whose rights are already clean: synthetic (self-generated),
owner-controlled, or license-verified public (CC BY 4.0). Each carries full
provenance so a filename is never treated as rights evidence. Coverage is mapped to
DT-54 launch strata to expose the gap acquisition must fill.

Source of truth is Python + a JSON snapshot (no YAML runtime dependency). Provenance
values mirror ``fixtures/audio_real/PROVENANCE.yaml`` and the corpus manifests.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.acquisition.requirements import CorpusRequirement, launch_requirements


@dataclass(frozen=True)
class RightsCleanAsset:
    asset_id: str
    source_dataset: str
    license: str
    attribution: str
    acquisition_date: str
    sha256: str
    permitted_use: tuple[str, ...]           # e.g. ("internal_evaluation","public_example","model_training")
    # Observable coverage against DT-54 dimensions (best-effort labels).
    genre: str = "unknown"
    language: str = "unknown"
    recording_condition: str = "unknown"
    count: int = 1                            # a dataset row may represent many clips

    def covers(self, dimension: str, value: str) -> bool:
        return getattr(self, dimension, "unknown") == value


# The current rights-clean inventory. VocalSet + vocadito are CC BY 4.0 clean
# *singing* — NOT rap/pop and NOT home/plosive/sibilant conditions — so they
# contribute ~0 to the launch-critical strata (the gap DT-55 must fill).
CURRENT_INVENTORY: tuple[RightsCleanAsset, ...] = (
    RightsCleanAsset(
        "vocalset_ci", "VocalSet", "CC BY 4.0",
        "Wilkins, Seetharaman, Wahl, Pardo, ISMIR 2018", "2026-07-11",
        "43ac20d7132dc9dc0ae6b93a65dce141c881b40a6cd6e2d556af61daabdacaf9",
        ("internal_evaluation", "public_example", "model_training"),
        genre="sung_sustained", language="english", recording_condition="studio_treated",
        count=40,
    ),
    RightsCleanAsset(
        "vocadito_ci", "vocadito", "CC BY 4.0",
        "Bittner et al., ISMIR-LBD 2021", "2026-07-11",
        "701ef8e73891b2408c8095b4afd3f5d8a0fa9e201b89085789642cf1ae764c01",
        ("internal_evaluation", "public_example", "model_training"),
        genre="unknown", language="multilingual_code_switch", recording_condition="unknown",
        count=40,
    ),
)


@dataclass(frozen=True)
class CoverageGap:
    dimension: str
    value: str
    target: int
    have: int

    @property
    def gap(self) -> int:
        return max(self.target - self.have, 0)

    @property
    def satisfied(self) -> bool:
        return self.have >= self.target


def coverage_gaps(
    inventory: tuple[RightsCleanAsset, ...] = CURRENT_INVENTORY,
    requirements: tuple[CorpusRequirement, ...] | None = None,
) -> list[CoverageGap]:
    """Per launch stratum: target vs available rights-clean count."""
    reqs = requirements or launch_requirements()
    gaps = []
    for req in reqs:
        have = sum(a.count for a in inventory if a.covers(req.dimension, req.value))
        gaps.append(CoverageGap(req.dimension, req.value, req.target_count, have))
    return gaps


def total_gap(inventory: tuple[RightsCleanAsset, ...] = CURRENT_INVENTORY) -> int:
    return sum(g.gap for g in coverage_gaps(inventory))
