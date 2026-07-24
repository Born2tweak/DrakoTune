"""Parameterized acquisition cost model (DT-55 Field 17).

Computes cost/time/storage envelopes for acquisition scenarios. All rates are
INPUTS with no committed value — the owner sets ceilings (Field 22: no spending is
authorized). A scenario that involves any paid source is flagged
``requires_human_authorization`` so cost can never be mistaken for approval.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.acquisition.purpose_matrix import SourceType


@dataclass(frozen=True)
class AcquisitionOption:
    source: SourceType
    quantity: int
    unit_cost: float = 0.0          # currency per asset/clip; 0 for license-clear public/synthetic
    minutes_per_unit: float = 0.5
    mb_per_unit: float = 5.0
    label: str = ""

    @property
    def cost(self) -> float:
        return self.quantity * self.unit_cost

    @property
    def minutes(self) -> float:
        return self.quantity * self.minutes_per_unit

    @property
    def storage_mb(self) -> float:
        return self.quantity * self.mb_per_unit


@dataclass(frozen=True)
class Scenario:
    name: str
    options: tuple[AcquisitionOption, ...]
    contingency: float = 0.15       # fraction added to cost as contingency

    def base_cost(self) -> float:
        return sum(o.cost for o in self.options)

    def total_cost(self) -> float:
        return round(self.base_cost() * (1 + self.contingency), 2)

    def total_minutes(self) -> float:
        return sum(o.minutes for o in self.options)

    def total_storage_mb(self) -> float:
        return sum(o.storage_mb for o in self.options)

    @property
    def requires_human_authorization(self) -> bool:
        """Any nonzero cost, or any paid/contract source, needs owner + counsel."""
        paid = {SourceType.COMMISSIONED_DRY_WET, SourceType.MARKETPLACE,
                SourceType.PROFESSIONAL_TREATMENT}
        return self.base_cost() > 0 or any(o.source in paid for o in self.options)

    def summary(self) -> dict:
        return {
            "name": self.name,
            "base_cost": round(self.base_cost(), 2),
            "total_cost_with_contingency": self.total_cost(),
            "total_minutes": self.total_minutes(),
            "total_storage_mb": self.total_storage_mb(),
            "requires_human_authorization": self.requires_human_authorization,
        }
