"""DT-54 — target-strata taxonomy framework (autonomous portion).

Field 14 (vocabulary/schema, incompatible-label, missing/unknown, version
migration) and Field 16 adversarial cases (ambiguous genre, multilingual
code-switch, layered/ad-lib vocal, synthetic label, tiny subgroup, sensitive
proxy). No scope decision is made; the launch-critical selection is Q-014 (human).
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.product_taxonomy import (
    RECOMMENDED_COVERAGE,
    Dimension,
    Priority,
    StratumAssignment,
    StratumLabel,
    TAXONOMY_VERSION,
    UNKNOWN,
    guard_sensitive,
    incompatible_labels,
    is_known_label,
    is_sparse,
    labels_for,
    migrate_assignment,
    missing_dimensions,
    resolve_with_unknowns,
    validate_assignment,
)


def _asn(*labels: StratumLabel, version: str = TAXONOMY_VERSION) -> StratumAssignment:
    return StratumAssignment("asset-1", tuple(labels), version)


# --- Field 14: vocabulary / schema ---

def test_every_dimension_has_sentinels():
    for dim in Dimension:
        assert UNKNOWN in labels_for(dim)
        assert "not_applicable" in labels_for(dim)


def test_valid_assignment_has_no_issues():
    asn = _asn(
        StratumLabel(Dimension.GENRE, "rap"),
        StratumLabel(Dimension.LANGUAGE, "english"),
        StratumLabel(Dimension.VOCAL_PRESENTATION, "spoken_rapped"),
        StratumLabel(Dimension.RECORDING_CONDITION, "home_untreated"),
    )
    assert validate_assignment(asn) == []


def test_synthetic_label_is_a_schema_error():
    """Field 16: a fabricated label must never be silently accepted."""
    asn = _asn(StratumLabel(Dimension.GENRE, "vaporwave_trap_9000"))
    codes = {i.code for i in validate_assignment(asn)}
    assert "unknown_label" in codes


def test_confidence_out_of_range_flagged():
    asn = _asn(StratumLabel(Dimension.GENRE, "rap", confidence=1.4))
    assert any(i.code == "bad_confidence" for i in validate_assignment(asn))


# --- Field 14: incompatible labels ---

def test_single_label_dimension_rejects_two_positives():
    """Field 16: ambiguous genre must not be forced into two positive labels."""
    asn = _asn(
        StratumLabel(Dimension.GENRE, "rap"),
        StratumLabel(Dimension.GENRE, "pop"),
    )
    assert any(i.code == "multi_label_not_allowed" for i in incompatible_labels(asn))


def test_ambiguous_genre_resolves_to_unknown_not_a_guess():
    """Field 16: ambiguous genre -> a single UNKNOWN, which is valid."""
    asn = _asn(StratumLabel(Dimension.GENRE, UNKNOWN))
    assert validate_assignment(asn) == []


def test_multilabel_presentation_allows_rapped_plus_adlib():
    """Field 16: layered/ad-lib vocal -> multiple presentation labels are allowed."""
    asn = _asn(
        StratumLabel(Dimension.VOCAL_PRESENTATION, "spoken_rapped"),
        StratumLabel(Dimension.VOCAL_PRESENTATION, "ad_lib"),
    )
    assert validate_assignment(asn) == []


def test_sentinel_mixed_with_positive_is_incompatible():
    asn = _asn(
        StratumLabel(Dimension.RECORDING_CONDITION, "home_untreated"),
        StratumLabel(Dimension.RECORDING_CONDITION, UNKNOWN),
    )
    assert any(i.code == "sentinel_with_positive" for i in incompatible_labels(asn))


def test_multilingual_code_switch_is_a_first_class_label():
    """Field 16: code-switch is its own label, never mislabeled as one language."""
    assert is_known_label(Dimension.LANGUAGE, "multilingual_code_switch")
    asn = _asn(StratumLabel(Dimension.LANGUAGE, "multilingual_code_switch"))
    assert validate_assignment(asn) == []


# --- Field 14: missing / unknown ---

def test_missing_dimensions_reported_and_resolved_as_unknown():
    asn = _asn(StratumLabel(Dimension.GENRE, "pop"))
    missing = missing_dimensions(asn)
    assert Dimension.LANGUAGE in missing
    resolved = resolve_with_unknowns(asn)
    assert resolved["language"] == (UNKNOWN,)  # never a silent pass
    assert resolved["genre"] == ("pop",)


# --- Field 14: version migration ---

def test_same_version_migration_is_identity():
    asn = _asn(StratumLabel(Dimension.GENRE, "rap"))
    migrated, issues = migrate_assignment(asn, TAXONOMY_VERSION)
    assert issues == []
    assert migrated.taxonomy_version == TAXONOMY_VERSION


def test_unknown_source_version_is_hard_error():
    asn = _asn(StratumLabel(Dimension.GENRE, "rap"), version="0.9.0")
    _, issues = migrate_assignment(asn, "0.9.0")
    assert any(i.code == "unknown_source_version" for i in issues)


def test_version_mismatch_flagged_by_validator():
    asn = _asn(StratumLabel(Dimension.GENRE, "rap"), version="0.9.0")
    assert any(i.code == "version_mismatch" for i in validate_assignment(asn))


# --- Field 16 / Field 18+22: sensitive-proxy guard ---

@pytest.mark.parametrize("bad", ["gender", "singer_age", "ethnicity_group", "accent_region"])
def test_sensitive_categories_rejected(bad):
    assert guard_sensitive(bad) is not None


def test_sensitive_label_value_rejected_in_assignment():
    asn = _asn(StratumLabel(Dimension.RECORDING_CONDITION, "male_gender_proxy"))
    codes = {i.code for i in validate_assignment(asn)}
    # unknown_label (not in vocab) AND sensitive_proxy_rejected both fire.
    assert "sensitive_proxy_rejected" in codes


# --- Field 13/16: sparse (tiny-subgroup) handling ---

def test_tiny_subgroup_is_sparse_and_excluded_from_confirmatory():
    entry = next(e for e in RECOMMENDED_COVERAGE if e.priority is Priority.LAUNCH_CRITICAL)
    assert is_sparse(entry, entry.min_coverage - 1) is True
    assert is_sparse(entry, entry.min_coverage) is False


def test_out_of_scope_stratum_never_anchors_claims():
    oos = next(e for e in RECOMMENDED_COVERAGE if e.priority is Priority.OUT_OF_SCOPE)
    assert oos.counts_for_confirmatory() is False


def test_recommended_coverage_declares_leakage_groups():
    assert all(e.leakage_group for e in RECOMMENDED_COVERAGE)


def test_recommended_coverage_uses_only_known_labels():
    for e in RECOMMENDED_COVERAGE:
        assert is_known_label(e.dimension, e.value)
