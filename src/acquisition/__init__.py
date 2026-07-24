"""Rights-clean corpus acquisition plan (DT-55, autonomous portion).

Builds only the Automatic half of the contract (Field 15): map corpus requirements
to DT-54 launch strata, inventory rights-clean assets with full provenance, expose
coverage gaps, validate rights/duplicates/leakage/ingestion, state the source ×
purpose grant matrix, and cost acquisition scenarios parametrically. It acquires
nothing and authorizes no spending, outreach, contract, or legal terms (Field 22).
"""
from src.acquisition.costing import AcquisitionOption, Scenario
from src.acquisition.inventory import (
    CURRENT_INVENTORY,
    CoverageGap,
    RightsCleanAsset,
    coverage_gaps,
    total_gap,
)
from src.acquisition.purpose_matrix import (
    GrantStatus,
    SourceType,
    autonomously_usable,
    grant_status,
)
from src.acquisition.requirements import (
    CorpusRequirement,
    Purpose,
    launch_requirements,
    total_target,
)
from src.acquisition.validators import (
    find_duplicates,
    ingestion_valid,
    leakage_conflicts,
    rights_complete,
)
from src.acquisition.withdrawal import WithdrawalOutcome, simulate_expiry, simulate_withdrawal

__all__ = [
    "AcquisitionOption", "Scenario",
    "CURRENT_INVENTORY", "CoverageGap", "RightsCleanAsset", "coverage_gaps", "total_gap",
    "GrantStatus", "SourceType", "autonomously_usable", "grant_status",
    "CorpusRequirement", "Purpose", "launch_requirements", "total_target",
    "find_duplicates", "ingestion_valid", "leakage_conflicts", "rights_complete",
    "WithdrawalOutcome", "simulate_expiry", "simulate_withdrawal",
]
