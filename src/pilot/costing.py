"""Fair-rate and pilot budget model (DT-58, autonomous portion).

Implements D-017's *formula* — compensation at or above a platform-recommended base
with a professional premium — but never sets the base rate or authorizes spend
(Field 22). The base rate and final ceiling are human inputs; any budget flags
``requires_human_authorization``.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FairRate:
    base_hourly: float           # human-set: platform-recommended floor (currency/hour)
    professional_premium: float  # human-set: multiplier >= 1.0 for qualified engineers

    def hourly(self) -> float:
        return round(self.base_hourly * max(self.professional_premium, 1.0), 2)

    def per_participant(self, task_hours: float) -> float:
        return round(self.hourly() * task_hours, 2)


@dataclass(frozen=True)
class PilotBudget:
    n_participants: int          # 2-3 for the expert pilot
    task_hours: float            # estimated session duration incl. setup
    rate: FairRate
    platform_fee_frac: float = 0.20
    contingency_frac: float = 0.20

    def participant_cost(self) -> float:
        return round(self.rate.per_participant(self.task_hours) * self.n_participants, 2)

    def total(self) -> float:
        base = self.participant_cost()
        return round(base * (1 + self.platform_fee_frac + self.contingency_frac), 2)

    @property
    def requires_human_authorization(self) -> bool:
        return True  # ALL real compensation needs owner + (payment) counsel sign-off

    def summary(self) -> dict:
        return {
            "n_participants": self.n_participants,
            "task_hours": self.task_hours,
            "hourly_rate": self.rate.hourly(),
            "participant_cost": self.participant_cost(),
            "total_with_fees_contingency": self.total(),
            "requires_human_authorization": True,
        }
