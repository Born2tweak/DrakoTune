"""Expert-pilot recruitment & budget groundwork (DT-58, autonomous portion).

Builds only the Automatic half (Field 15): participant criteria + screener +
qualification, fair-rate/budget *formula*, and an end-to-end dry-run on mock data.
It contacts no one, enrolls no one, and authorizes no spending, contract, or consent
(Field 22). Approval scope, base rate, and go/no-go remain human-only.
"""
from src.pilot.costing import FairRate, PilotBudget
from src.pilot.criteria import (
    MIN_YEARS_EXPERIENCE,
    Qualification,
    Role,
    ScreenerResponse,
    qualify,
)
from src.pilot.dryrun import (
    DryRunReport,
    balanced_assignments,
    build_pilot_protocol,
    dry_run,
    simulate_responses,
)

__all__ = [
    "FairRate", "PilotBudget",
    "MIN_YEARS_EXPERIENCE", "Qualification", "Role", "ScreenerResponse", "qualify",
    "DryRunReport", "balanced_assignments", "build_pilot_protocol", "dry_run", "simulate_responses",
]
