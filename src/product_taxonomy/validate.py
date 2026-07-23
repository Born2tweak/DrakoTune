"""Validators for target-strata assignments (DT-54 Field 14 + Field 16).

Covers: schema/vocabulary validation, incompatible-label detection, missing/
unknown handling, version migration, the sensitive-proxy guard, and sparse-
stratum flagging. Everything fails *closed*: an unknown label is a schema error,
a missing dimension is ``unknown`` (never a pass), and a sensitive proxy is
rejected outright.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.product_taxonomy.strata import CoverageEntry, StratumAssignment
from src.product_taxonomy.vocabulary import (
    FORBIDDEN_SENSITIVE_TERMS,
    MULTILABEL_DIMENSIONS,
    TAXONOMY_VERSION,
    UNKNOWN,
    Dimension,
    is_known_label,
    is_sentinel,
)


@dataclass(frozen=True)
class TaxonomyIssue:
    code: str
    detail: str
    dimension: str = ""

    def __str__(self) -> str:  # pragma: no cover - convenience
        where = f" [{self.dimension}]" if self.dimension else ""
        return f"{self.code}{where}: {self.detail}"


# Renames/removals per version. Maps an old value -> new value for a dimension.
# Empty for 1.0.0 (initial). Populate when TAXONOMY_VERSION bumps.
_MIGRATIONS: dict[str, dict[Dimension, dict[str, str]]] = {}


def guard_sensitive(name: str) -> TaxonomyIssue | None:
    """Reject any dimension/label that encodes a sensitive personal category."""
    lowered = name.lower()
    for term in FORBIDDEN_SENSITIVE_TERMS:
        if term in lowered:
            return TaxonomyIssue(
                "sensitive_proxy_rejected",
                f"'{name}' encodes a forbidden sensitive category ('{term}')",
            )
    return None


def validate_assignment(assignment: StratumAssignment) -> list[TaxonomyIssue]:
    """Schema + version + sensitive-proxy validation for one assignment."""
    issues: list[TaxonomyIssue] = []

    if assignment.taxonomy_version != TAXONOMY_VERSION:
        issues.append(TaxonomyIssue(
            "version_mismatch",
            f"assignment version '{assignment.taxonomy_version}' != current "
            f"'{TAXONOMY_VERSION}' — migrate before use",
        ))

    for label in assignment.labels:
        dim = label.dimension
        # Synthetic / unknown labels are schema errors, never silent aliases.
        if not is_known_label(dim, label.value):
            issues.append(TaxonomyIssue(
                "unknown_label", f"'{label.value}' is not in the {dim.value} vocabulary",
                dim.value,
            ))
        if not (0.0 <= label.confidence <= 1.0):
            issues.append(TaxonomyIssue(
                "bad_confidence", f"confidence {label.confidence} out of [0,1]", dim.value,
            ))
        sensitive = guard_sensitive(label.value)
        if sensitive is not None:
            issues.append(sensitive)

    issues.extend(incompatible_labels(assignment))
    return issues


def incompatible_labels(assignment: StratumAssignment) -> list[TaxonomyIssue]:
    """Detect contradictory label combinations within a dimension."""
    issues: list[TaxonomyIssue] = []
    for dim in Dimension:
        values = assignment.values(dim)
        positives = [v for v in values if not is_sentinel(v)]
        # A sentinel must not co-exist with a positive label in the same dimension.
        if positives and any(is_sentinel(v) for v in values):
            issues.append(TaxonomyIssue(
                "sentinel_with_positive",
                f"{dim.value} mixes a positive label with unknown/not_applicable",
                dim.value,
            ))
        # Single-label dimensions may not carry two positive labels.
        if dim not in MULTILABEL_DIMENSIONS and len(positives) > 1:
            issues.append(TaxonomyIssue(
                "multi_label_not_allowed",
                f"{dim.value} is single-label but got {positives}",
                dim.value,
            ))
    return issues


def missing_dimensions(assignment: StratumAssignment) -> tuple[Dimension, ...]:
    """Dimensions with no observed label — caller must treat these as unknown."""
    return tuple(d for d in Dimension if not assignment.values(d))


def resolve_with_unknowns(assignment: StratumAssignment) -> dict[str, tuple[str, ...]]:
    """Materialize every dimension, filling missing ones with UNKNOWN (never a pass)."""
    out: dict[str, tuple[str, ...]] = {}
    for dim in Dimension:
        vals = assignment.values(dim)
        out[dim.value] = vals if vals else (UNKNOWN,)
    return out


def migrate_assignment(
    assignment: StratumAssignment, from_version: str
) -> tuple[StratumAssignment, list[TaxonomyIssue]]:
    """Migrate labels from ``from_version`` to the current TAXONOMY_VERSION.

    An unrecognized source version is a hard error (no silent passthrough).
    """
    from dataclasses import replace

    if from_version == TAXONOMY_VERSION:
        return replace(assignment, taxonomy_version=TAXONOMY_VERSION), []
    if from_version not in _MIGRATIONS:
        return assignment, [TaxonomyIssue(
            "unknown_source_version",
            f"no migration path from '{from_version}' to '{TAXONOMY_VERSION}'",
        )]
    table = _MIGRATIONS[from_version]
    new_labels = []
    for label in assignment.labels:
        mapped = table.get(label.dimension, {}).get(label.value, label.value)
        new_labels.append(replace(label, value=mapped))
    migrated = replace(
        assignment, labels=tuple(new_labels), taxonomy_version=TAXONOMY_VERSION
    )
    return migrated, []


def is_sparse(entry: CoverageEntry, observed_count: int) -> bool:
    """A stratum below its minimum coverage is sparse -> excluded from confirmatory claims."""
    return observed_count < entry.min_coverage
