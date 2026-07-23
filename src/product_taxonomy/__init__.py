"""Target-genre and recording-strata taxonomy (DT-54, autonomous portion).

DT-54's *decision* — which strata are launch-critical (Q-014), adding any
sensitive category, or materially changing the target population — is a human-only
``product_scope`` gate (contract Field 15). This package builds only the
**autonomous framework** the contract marks *Automatic*: a versioned, observable
stratum vocabulary with unknown/not-applicable and multilabel/uncertainty
handling, a priority/coverage matrix with leakage groups, and validators for
schema, incompatible labels, missing/unknown values, version migration, sparse
strata, and sensitive-proxy rejection.

Nothing here infers demographics or decides scope. ``RECOMMENDED_COVERAGE`` is a
non-binding proposal for the owner + audio lead; it carries no claim authority
until they accept it.
"""
from src.product_taxonomy.strata import (
    RECOMMENDED_COVERAGE,
    CoverageEntry,
    Priority,
    StratumAssignment,
    StratumLabel,
)
from src.product_taxonomy.validate import (
    TaxonomyIssue,
    guard_sensitive,
    incompatible_labels,
    is_sparse,
    migrate_assignment,
    missing_dimensions,
    resolve_with_unknowns,
    validate_assignment,
)
from src.product_taxonomy.vocabulary import (
    MULTILABEL_DIMENSIONS,
    NOT_APPLICABLE,
    TAXONOMY_VERSION,
    UNKNOWN,
    Dimension,
    is_known_label,
    is_sentinel,
    labels_for,
)

__all__ = [
    "RECOMMENDED_COVERAGE",
    "CoverageEntry",
    "Priority",
    "StratumAssignment",
    "StratumLabel",
    "TaxonomyIssue",
    "guard_sensitive",
    "incompatible_labels",
    "is_sparse",
    "migrate_assignment",
    "missing_dimensions",
    "resolve_with_unknowns",
    "validate_assignment",
    "MULTILABEL_DIMENSIONS",
    "NOT_APPLICABLE",
    "TAXONOMY_VERSION",
    "UNKNOWN",
    "Dimension",
    "is_known_label",
    "is_sentinel",
    "labels_for",
]
