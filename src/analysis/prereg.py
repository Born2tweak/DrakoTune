"""Immutable statistical preregistration plan + analysis lock (DT-57).

A preregistration is a *frozen* contract written BEFORE confirmatory data exists.
This module makes that structural: a ``PreregistrationPlan`` is a frozen dataclass,
and ``freeze()`` computes a content hash (the *analysis lock*). Any post-hoc change
— swapping an endpoint, loosening an exclusion, adding an interim look — changes the
hash, so a later analysis can prove it ran the frozen plan (guards against post-hoc
metric substitution / p-hacking / selective exclusion / early stopping).

The plan SEPARATES objective endpoints (measured DSP metrics, no listeners) from
perceptual endpoints (listener preference), per the project's honesty rule. Human
sign-off is required only for the threshold/design VALUES: those are held in
``PendingHumanChoice`` fields, and ``freeze()`` refuses to lock while any remain
unset. Selecting final sample size needs pilot variance (Field 8, out of scope
here) — the power harness (``power.py``) computes it as a function, it is not set.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum

PREREG_SCHEMA_VERSION = "1.0.0"


class EndpointKind(str, Enum):
    OBJECTIVE = "objective"      # measured DSP metric; no listeners; not perceptual
    PERCEPTUAL = "perceptual"    # listener preference/judgement


class Direction(str, Enum):
    SUPERIORITY = "superiority"          # processed preferred over original (DT-67)
    NON_INFERIORITY = "non_inferiority"  # do-no-harm on clean input (DT-66)


# Sentinel for a value only a human may set (threshold / alpha / power / margin).
PENDING = "__PENDING_HUMAN_SIGNOFF__"


@dataclass(frozen=True)
class Hypothesis:
    """A single testable hypothesis with an explicit null."""

    endpoint_id: str
    description: str
    null_hypothesis: str            # H0 stated so it can be rejected, never "no effect assumed true"
    alternative: str
    direction: Direction
    kind: EndpointKind
    # Values a human must set; PENDING until then.
    min_effect_threshold: str = PENDING   # e.g. processed-preference margin over 0.5
    alpha: str = PENDING
    is_primary: bool = False

    def unset_choices(self) -> list[str]:
        out = []
        if self.min_effect_threshold == PENDING:
            out.append(f"{self.endpoint_id}.min_effect_threshold")
        if self.alpha == PENDING:
            out.append(f"{self.endpoint_id}.alpha")
        return out


@dataclass(frozen=True)
class ExclusionRule:
    """A prespecified exclusion. Prespecification is what stops selective exclusion."""

    rule_id: str
    applies_to: str          # "listener" | "response" | "trial"
    condition: str
    action: str              # "exclude" | "quarantine" | "abstain"


@dataclass(frozen=True)
class PreregistrationPlan:
    """A frozen analysis plan. Freeze BEFORE confirmatory data collection."""

    plan_id: str
    version: str
    population: str                       # supported-input + launch-strata definition
    estimand: str                         # what is being estimated, at what unit (listener cluster)
    hypotheses: tuple[Hypothesis, ...]
    exclusions: tuple[ExclusionRule, ...]
    multiplicity_method: str              # e.g. "holm" across primary endpoints
    missing_data_policy: str              # e.g. "report dropout; sensitivity: worst-case + complete-case"
    stopping_rule: str                    # e.g. "fixed-N, no interim analyses" (prevents early stopping)
    invalid_response_policy: str          # forged/duplicate/ambiguous -> quarantine (DT-56)
    tie_policy: str                       # ties are a reported category, never dropped (N-004)
    sensitivity_analyses: tuple[str, ...] = ()
    schema_version: str = PREREG_SCHEMA_VERSION
    randomization: str = "blinded A/B side + play order balanced (DT-56 Assignment)"

    # ---- lock / freeze ----

    def unset_choices(self) -> list[str]:
        """Every human-only value still PENDING. freeze() refuses while non-empty."""
        out: list[str] = []
        for h in self.hypotheses:
            out.extend(h.unset_choices())
        return out

    def canonical_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, default=str)

    def content_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def freeze(self) -> str:
        """Return the analysis-lock hash, refusing while human choices are unset.

        A frozen plan's hash is recomputable; an analysis run records it, so any
        divergence from the preregistered plan is detectable.
        """
        pending = self.unset_choices()
        if pending:
            raise ValueError(
                "cannot freeze: human sign-off required for " + ", ".join(pending)
            )
        return self.content_hash()

    def primary_endpoints(self) -> tuple[Hypothesis, ...]:
        return tuple(h for h in self.hypotheses if h.is_primary)


def matches_lock(plan: PreregistrationPlan, recorded_hash: str) -> bool:
    """True iff `plan` still hashes to a previously recorded analysis lock.

    Used by an analysis run to prove it executed the frozen plan (post-hoc guard).
    Only valid on a fully-signed plan; PENDING values never produce a lock.
    """
    if plan.unset_choices():
        return False
    return plan.content_hash() == recorded_hash
