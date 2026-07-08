"""Decision artifacts: objectives, actions, and the processing plan.

These are produced by the (future) decision engine and consumed by the DSP
engine. The DSP engine executes a ProcessingPlan; it does not author one. Until
the decision engine exists (M07/M08), plans may be assembled minimally for
record-keeping only.
"""

from dataclasses import dataclass, field

from src.shared_types.versions import POLICY_VERSION


@dataclass(frozen=True)
class ProcessingObjective:
    """A named goal such as 'reduce_harshness', with priority and confidence."""

    id: str
    goal: str
    priority: int = 0
    confidence: float = 0.0
    constraints: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "priority": self.priority,
            "confidence": self.confidence,
            "constraints": list(self.constraints),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProcessingObjective":
        return cls(
            id=d["id"],
            goal=d["goal"],
            priority=int(d.get("priority", 0)),
            confidence=float(d.get("confidence", 0.0)),
            constraints=tuple(d.get("constraints", ())),
        )


@dataclass(frozen=True)
class ProcessingAction:
    """A single DSP operation selected to serve an objective."""

    id: str
    processor: str
    parameters: dict = field(default_factory=dict)
    strength: float = 1.0
    reason: str = ""
    objective_id: str | None = None
    blocked_actions: tuple[str, ...] = ()
    reversible: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "processor": self.processor,
            "parameters": dict(self.parameters),
            "strength": self.strength,
            "reason": self.reason,
            "objective_id": self.objective_id,
            "blocked_actions": list(self.blocked_actions),
            "reversible": self.reversible,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProcessingAction":
        return cls(
            id=d["id"],
            processor=d["processor"],
            parameters=dict(d.get("parameters", {})),
            strength=float(d.get("strength", 1.0)),
            reason=d.get("reason", ""),
            objective_id=d.get("objective_id"),
            blocked_actions=tuple(d.get("blocked_actions", ())),
            reversible=bool(d.get("reversible", True)),
        )


@dataclass(frozen=True)
class ProcessingPlan:
    """An ordered set of objectives and actions plus what was skipped and why."""

    id: str
    preset_profile: str = "default"
    objectives: tuple[ProcessingObjective, ...] = ()
    actions: tuple[ProcessingAction, ...] = ()
    skipped_processors: tuple[str, ...] = ()
    policy_version: str = POLICY_VERSION

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "preset_profile": self.preset_profile,
            "objectives": [o.to_dict() for o in self.objectives],
            "actions": [a.to_dict() for a in self.actions],
            "skipped_processors": list(self.skipped_processors),
            "policy_version": self.policy_version,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProcessingPlan":
        return cls(
            id=d["id"],
            preset_profile=d.get("preset_profile", "default"),
            objectives=tuple(ProcessingObjective.from_dict(o) for o in d.get("objectives", [])),
            actions=tuple(ProcessingAction.from_dict(a) for a in d.get("actions", [])),
            skipped_processors=tuple(d.get("skipped_processors", ())),
            policy_version=d.get("policy_version", POLICY_VERSION),
        )
