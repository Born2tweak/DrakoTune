"""Rights, consent, and withdrawal enforcement (DT-49).

DT-45 defined the *vocabulary* (``RightsPermission``, ``GrantStatus``) and DT-46
built the identity/provenance graph. DT-49 builds the **enforcement** layer on
top of them:

- purpose-specific rights grants (:mod:`src.rights.grants`);
- a fail-closed ``authorize(subject, purpose, at_time)`` decision
  (:mod:`src.rights.authorize`);
- a protected consent-store *interface* with a synthetic in-memory
  implementation (:mod:`src.rights.consent_store`);
- withdrawal propagation through the derivation graph to assets, derivatives,
  results, and claims, as a **deletion/retract simulation** that never performs
  real deletion (:mod:`src.rights.withdrawal`).

Scope boundary (DT-49 contract, Field 15): everything in this package is
*automatic* — graph, authorization, withdrawal-plan, and security validation on
synthetic fixtures. The **human-only** steps (consent/contract language,
retention/privacy obligations, real deletion authority, legal rights
interpretation) are deliberately NOT implemented here; the consent store is an
interface, and withdrawal produces a plan, never a deletion.
"""

from src.rights.authorize import Authorization, authorize
from src.rights.consent_store import ConsentStore, InMemoryConsentStore
from src.rights.grants import RightsGrant
from src.rights.purposes import Purpose
from src.rights.withdrawal import (
    WithdrawalEvent,
    WithdrawalPlan,
    plan_withdrawal,
    suspend_affected_claims,
)

__all__ = [
    "Authorization",
    "authorize",
    "ConsentStore",
    "InMemoryConsentStore",
    "RightsGrant",
    "Purpose",
    "WithdrawalEvent",
    "WithdrawalPlan",
    "plan_withdrawal",
    "suspend_affected_claims",
]
