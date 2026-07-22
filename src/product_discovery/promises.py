"""Candidate product promises with explicit falsifiers (DT-53).

A *candidate promise* is a bounded statement of what DrakoTune would do for a
named user doing a named job — paired with the **falsifiers** that would refute
it. Discovery is honest only if every promise can be killed by evidence; a
promise with no falsifier is inadmissible.

Choosing among promises is the human ``product_scope`` decision. This module
only structures the alternatives and lets the validator test each promise's
falsifiers against the (synthetic) discovery record set.
"""

from dataclasses import dataclass, field
from enum import Enum


class PromiseOutcome(str, Enum):
    """Result of testing a promise against the discovery record set."""

    SUPPORTED = "supported"          # no falsifier observed; some support present
    FALSIFIED = "falsified"          # a falsifier condition was observed
    INSUFFICIENT = "insufficient"    # neither support nor falsifier — stay narrow


@dataclass(frozen=True)
class JobStep:
    """One step in the target user's job-to-be-done map."""

    step_id: str
    description: str
    current_pain: str = ""


@dataclass(frozen=True)
class CandidatePromise:
    """A bounded, falsifiable product promise alternative."""

    promise_id: str
    statement: str
    target_user: str
    job: str
    in_scope: tuple[str, ...] = ()
    out_of_scope: tuple[str, ...] = ()
    # A falsifier is a token that, if present in any usable note's pain_points or
    # observed_behaviors, refutes the promise (e.g. "accompaniment_required").
    falsifiers: tuple[str, ...] = ()
    # Tokens that count as positive support for the promise.
    support_signals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.falsifiers:
            raise ValueError(
                f"promise {self.promise_id!r} has no falsifier; an untestable "
                "promise is inadmissible in DT-53 discovery"
            )

    def to_dict(self) -> dict:
        return {
            "promise_id": self.promise_id,
            "statement": self.statement,
            "target_user": self.target_user,
            "job": self.job,
            "in_scope": list(self.in_scope),
            "out_of_scope": list(self.out_of_scope),
            "falsifiers": list(self.falsifiers),
            "support_signals": list(self.support_signals),
        }
