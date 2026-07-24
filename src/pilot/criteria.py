"""Participant criteria, screener, and qualification (DT-58, autonomous portion).

Defines who qualifies for the 2-3 person expert-engineer pilot and scores a
screener response. An accessibility need is an accommodation requirement, never a
disqualifier (Field 16). No candidate is contacted; this only defines and tests the
screener logic on mock data (Field 8/22).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from src.listening.schema import Panel


class Role(str, Enum):
    EXPERT_ENGINEER = "expert_engineer"       # target for this pilot (DT-59)
    TRAINED_LISTENER = "trained_listener"
    TARGET_USER = "target_user"

    def to_panel(self) -> Panel:
        return {
            Role.EXPERT_ENGINEER: Panel.EXPERT_ENGINEER,
            Role.TRAINED_LISTENER: Panel.TRAINED_LISTENER,
            Role.TARGET_USER: Panel.TARGET_USER,
        }[self]


@dataclass(frozen=True)
class ScreenerResponse:
    candidate_id: str                 # pseudonymous
    years_mixing_experience: float
    target_genre_familiar: bool       # rap/pop vocal mixing
    calibrated_monitoring: bool       # headphones/monitors + treated space
    passed_audio_check: bool          # can distinguish a reference tone A/B check
    accessibility_needs: tuple[str, ...] = ()


# Minimum qualification for the expert-engineer pilot role. Values are design
# defaults; the owner may adjust before recruitment (human gate).
MIN_YEARS_EXPERIENCE = 3.0


@dataclass(frozen=True)
class Qualification:
    candidate_id: str
    qualified: bool
    reasons: tuple[str, ...]
    accommodations_required: tuple[str, ...]


def qualify(resp: ScreenerResponse, role: Role = Role.EXPERT_ENGINEER) -> Qualification:
    """Score a screener response. Accessibility needs -> accommodation, not exclusion."""
    reasons: list[str] = []
    if role is Role.EXPERT_ENGINEER and resp.years_mixing_experience < MIN_YEARS_EXPERIENCE:
        reasons.append(f"experience {resp.years_mixing_experience}y < {MIN_YEARS_EXPERIENCE}y")
    if not resp.target_genre_familiar:
        reasons.append("not familiar with target-genre vocal mixing")
    if not resp.calibrated_monitoring:
        reasons.append("no calibrated monitoring")
    if not resp.passed_audio_check:
        reasons.append("failed audio discrimination check")
    return Qualification(
        candidate_id=resp.candidate_id,
        qualified=not reasons,
        reasons=tuple(reasons),
        accommodations_required=resp.accessibility_needs,  # accommodate, never disqualify
    )
