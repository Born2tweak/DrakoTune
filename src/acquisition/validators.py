"""Rights / duplicate / leakage / ingestion validators (DT-55 Field 14).

Fail-closed checks over acquisition records and the rights-clean inventory. A
filename or repo path is never rights evidence; every asset must carry complete
provenance before it may be used.
"""
from __future__ import annotations

from src.acquisition.inventory import RightsCleanAsset

REQUIRED_PROVENANCE = ("source_dataset", "license", "attribution", "sha256", "permitted_use")
REQUIRED_INGESTION = ("asset_id", "source_dataset", "license", "sha256", "permitted_use", "consent_ref")


def rights_complete(asset: RightsCleanAsset) -> list[str]:
    """Missing/empty provenance fields on an inventory asset."""
    issues = []
    for fieldname in REQUIRED_PROVENANCE:
        val = getattr(asset, fieldname, None)
        if not val:
            issues.append(f"missing provenance field '{fieldname}'")
    return issues


def find_duplicates(assets: list[RightsCleanAsset]) -> list[tuple[str, str]]:
    """Asset id pairs sharing a sha256 (content duplicates)."""
    seen: dict[str, str] = {}
    dups = []
    for a in assets:
        if a.sha256 in seen:
            dups.append((seen[a.sha256], a.asset_id))
        else:
            seen[a.sha256] = a.asset_id
    return dups


def leakage_conflicts(
    train_ids: set[str], eval_ids: set[str], asset_group: dict[str, str],
) -> list[str]:
    """Leakage groups (e.g. performer/session) that appear in BOTH splits."""
    train_groups = {asset_group.get(i) for i in train_ids if asset_group.get(i)}
    eval_groups = {asset_group.get(i) for i in eval_ids if asset_group.get(i)}
    return sorted(train_groups & eval_groups)


def ingestion_valid(record: dict) -> list[str]:
    """Required keys for an ingestion record; consent_ref mandatory (Field 11/18)."""
    return [f"missing '{k}'" for k in REQUIRED_INGESTION if not record.get(k)]
