"""Consent withdrawal / grant-expiry simulation (DT-55 Field 14).

Simulates what must happen to a plan (not real data) when a consent is withdrawn or
a grant expires: the asset's purposes are revoked, dependent claims are suspended,
and a deletion *plan* is produced. Mirrors the DT-49 rights posture — withdrawal
yields a plan, never an autonomous deletion of real data (that is human-only).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WithdrawalOutcome:
    asset_id: str
    revoked_purposes: tuple[str, ...]
    dependent_claims_suspended: bool
    deletion_plan: str
    requires_human_action: bool = True


def simulate_withdrawal(
    asset_id: str, granted_purposes: tuple[str, ...], claims_using_asset: tuple[str, ...] = (),
) -> WithdrawalOutcome:
    """All purposes revoked; any dependent claim suspended; deletion planned."""
    return WithdrawalOutcome(
        asset_id=asset_id,
        revoked_purposes=granted_purposes,
        dependent_claims_suspended=bool(claims_using_asset),
        deletion_plan=(
            f"Plan deletion of {asset_id} and derived artifacts; suspend claims "
            f"{list(claims_using_asset)}. Real deletion is human-executed (DT-49 posture)."
        ),
        requires_human_action=True,
    )


def simulate_expiry(asset_id: str, granted_purposes: tuple[str, ...], expired: bool) -> WithdrawalOutcome:
    """An expired grant behaves like a withdrawal for all purposes."""
    if not expired:
        return WithdrawalOutcome(asset_id, (), False, "grant valid; no action", False)
    return simulate_withdrawal(asset_id, granted_purposes)
