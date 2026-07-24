"""DT-55 — rights-clean acquisition plan (autonomous portion).

Field 14 (template/schema completeness, purpose matrix, expiry/withdrawal) and
Field 16 adversarial (marketplace terms insufficient, split rights, training grant
refused, withdrawal after publication). Nothing is acquired; no spend authorized.
"""
from __future__ import annotations

from dataclasses import replace

from src.acquisition import (
    AcquisitionOption,
    CURRENT_INVENTORY,
    GrantStatus,
    Purpose,
    Scenario,
    SourceType,
    autonomously_usable,
    coverage_gaps,
    find_duplicates,
    grant_status,
    ingestion_valid,
    launch_requirements,
    leakage_conflicts,
    rights_complete,
    simulate_expiry,
    simulate_withdrawal,
    total_gap,
)


# --- requirements mapped to accepted DT-54 strata ---

def test_requirements_cover_launch_strata():
    reqs = launch_requirements()
    dims = {r.dimension for r in reqs}
    assert {"genre", "vocal_presentation", "language", "recording_condition"} <= dims
    assert all(r.target_count > 0 for r in reqs)


def test_coverage_gap_is_large_for_rap_pop_home_conditions():
    """CC-BY singing sets do not cover rap/pop home-recorded strata -> real gap."""
    gaps = {(g.dimension, g.value): g for g in coverage_gaps()}
    assert gaps[("genre", "rap")].gap > 0            # no rap in VocalSet/vocadito
    assert gaps[("recording_condition", "home_untreated")].gap > 0
    assert total_gap() > 0


# --- provenance / rights validators ---

def test_inventory_assets_have_complete_rights():
    for asset in CURRENT_INVENTORY:
        assert rights_complete(asset) == []


def test_missing_provenance_is_flagged():
    bad = replace(CURRENT_INVENTORY[0], sha256="", attribution="")
    issues = rights_complete(bad)
    assert any("sha256" in i for i in issues) and any("attribution" in i for i in issues)


def test_duplicate_detection_by_checksum():
    dup = replace(CURRENT_INVENTORY[1], asset_id="clone", sha256=CURRENT_INVENTORY[0].sha256)
    assert find_duplicates([CURRENT_INVENTORY[0], dup]) == [("vocalset_ci", "clone")]


def test_leakage_conflict_detected():
    groups = {"a1": "singerX", "a2": "singerX", "a3": "singerY"}
    assert leakage_conflicts({"a1"}, {"a2"}, groups) == ["singerX"]   # same performer both splits
    assert leakage_conflicts({"a1"}, {"a3"}, groups) == []


def test_ingestion_requires_consent_ref():
    incomplete = {"asset_id": "x", "source_dataset": "s", "license": "CC BY 4.0",
                  "sha256": "abc", "permitted_use": ["internal_evaluation"]}
    assert any("consent_ref" in i for i in ingestion_valid(incomplete))


# --- purpose matrix (Field 16: split/refused grants) ---

def test_public_cc_by_is_autonomously_usable_for_eval():
    assert autonomously_usable(SourceType.PUBLIC_CC_BY, Purpose.LISTENING_STUDY)
    assert grant_status(SourceType.PUBLIC_CC_BY, Purpose.PUBLIC_EXAMPLE) is GrantStatus.GRANTED_WITH_ATTRIBUTION


def test_commissioned_and_marketplace_need_human_gates():
    assert not autonomously_usable(SourceType.COMMISSIONED_DRY_WET, Purpose.LISTENING_STUDY)
    assert grant_status(SourceType.MARKETPLACE, Purpose.MODEL_TRAINING) is GrantStatus.NEEDS_COUNSEL
    assert grant_status(SourceType.PROFESSIONAL_TREATMENT, Purpose.INTERNAL_EVALUATION) is GrantStatus.NEEDS_SPEND_AND_CONTRACT


# --- costing: no spend authorized ---

def test_free_scenario_needs_no_authorization():
    free = Scenario("public_only", (
        AcquisitionOption(SourceType.PUBLIC_CC_BY, quantity=40, unit_cost=0.0),
        AcquisitionOption(SourceType.SYNTHETIC, quantity=160, unit_cost=0.0),
    ))
    assert free.requires_human_authorization is False
    assert free.base_cost() == 0.0


def test_paid_scenario_flags_human_authorization():
    paid = Scenario("commissioned", (
        AcquisitionOption(SourceType.COMMISSIONED_DRY_WET, quantity=30, unit_cost=50.0),
    ))
    s = paid.summary()
    assert s["requires_human_authorization"] is True
    assert s["total_cost_with_contingency"] > s["base_cost"]  # contingency added


# --- withdrawal / expiry simulation (Field 16: withdrawal after publication) ---

def test_withdrawal_after_publication_suspends_claims_and_plans_deletion():
    out = simulate_withdrawal("asset1", ("public_example",), claims_using_asset=("C-042",))
    assert out.dependent_claims_suspended is True
    assert out.requires_human_action is True
    assert "human-executed" in out.deletion_plan


def test_valid_grant_expiry_is_noop():
    out = simulate_expiry("asset1", ("internal_evaluation",), expired=False)
    assert out.requires_human_action is False and out.revoked_purposes == ()
