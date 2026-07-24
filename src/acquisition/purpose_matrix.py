"""Source × purpose grant matrix (DT-55 Field 13).

States, for each source type and evaluation purpose, whether use is already granted
by license or needs a human/counsel/spend gate. Purpose-specific rights are kept
distinct (D-014): internal evaluation, public example, model training, and
redistribution are separate permissions.
"""
from __future__ import annotations

from enum import Enum

from src.acquisition.requirements import Purpose


class SourceType(str, Enum):
    PUBLIC_CC_BY = "public_cc_by"                 # VocalSet/vocadito etc.
    OWNER_CONTROLLED = "owner_controlled"          # user's own audio
    SYNTHETIC = "synthetic"                        # self-generated degradations
    COMMISSIONED_DRY_WET = "commissioned_dry_wet"  # paid, needs contract
    MARKETPLACE = "marketplace"                    # licensed stock, per-terms
    PROFESSIONAL_TREATMENT = "professional_treatment"  # paid engineer reference


class GrantStatus(str, Enum):
    GRANTED_BY_LICENSE = "granted_by_license"
    GRANTED_WITH_ATTRIBUTION = "granted_with_attribution"
    NEEDS_COUNSEL = "needs_counsel"
    NEEDS_SPEND_AND_CONTRACT = "needs_spend_and_contract"
    BLOCKED = "blocked"


# Only no-spend, no-contract, license-clear cells are "granted". Everything that
# needs money, a contract, or legal review is explicitly gated (never auto-granted).
_MATRIX: dict[SourceType, dict[Purpose, GrantStatus]] = {
    SourceType.PUBLIC_CC_BY: {
        Purpose.INTERNAL_EVALUATION: GrantStatus.GRANTED_BY_LICENSE,
        Purpose.LISTENING_STUDY: GrantStatus.GRANTED_BY_LICENSE,
        Purpose.PUBLIC_EXAMPLE: GrantStatus.GRANTED_WITH_ATTRIBUTION,
        Purpose.MODEL_TRAINING: GrantStatus.GRANTED_WITH_ATTRIBUTION,
    },
    SourceType.OWNER_CONTROLLED: {
        Purpose.INTERNAL_EVALUATION: GrantStatus.GRANTED_BY_LICENSE,
        Purpose.LISTENING_STUDY: GrantStatus.GRANTED_BY_LICENSE,
        Purpose.PUBLIC_EXAMPLE: GrantStatus.NEEDS_COUNSEL,   # publishing owner audio still reviewed
        Purpose.MODEL_TRAINING: GrantStatus.GRANTED_BY_LICENSE,
    },
    SourceType.SYNTHETIC: {
        Purpose.INTERNAL_EVALUATION: GrantStatus.GRANTED_BY_LICENSE,
        Purpose.LISTENING_STUDY: GrantStatus.GRANTED_BY_LICENSE,
        Purpose.PUBLIC_EXAMPLE: GrantStatus.GRANTED_WITH_ATTRIBUTION,
        Purpose.MODEL_TRAINING: GrantStatus.GRANTED_BY_LICENSE,
    },
    SourceType.COMMISSIONED_DRY_WET: dict.fromkeys(Purpose, GrantStatus.NEEDS_SPEND_AND_CONTRACT),
    SourceType.MARKETPLACE: dict.fromkeys(Purpose, GrantStatus.NEEDS_COUNSEL),
    SourceType.PROFESSIONAL_TREATMENT: dict.fromkeys(Purpose, GrantStatus.NEEDS_SPEND_AND_CONTRACT),
}


def grant_status(source: SourceType, purpose: Purpose) -> GrantStatus:
    return _MATRIX[source].get(purpose, GrantStatus.BLOCKED)


def autonomously_usable(source: SourceType, purpose: Purpose) -> bool:
    """True only when a cell needs no spend, contract, or counsel."""
    return grant_status(source, purpose) in (
        GrantStatus.GRANTED_BY_LICENSE, GrantStatus.GRANTED_WITH_ATTRIBUTION,
    )
