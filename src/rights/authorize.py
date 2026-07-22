"""Fail-closed purpose authorization (DT-49).

``authorize(store, graph, asset_id, purpose, at_time)`` resolves a single
question: *may this asset be used for this purpose at this time?* and returns an
explicit :class:`Authorization` whose ``permission`` is one of the canonical
:class:`~src.evaluation.semantics.enums.RightsPermission` states.

Invariants (DT-49 Field 13/16):

- **Unknown fails closed.** No applicable grant → ``UNKNOWN`` → not authorized.
- **Most-restrictive wins.** A conflicting ``allowed`` + ``prohibited`` pair
  resolves to ``PROHIBITED``. A withdrawal blocks. An expired grant blocks
  unless a still-valid grant independently allows the purpose.
- **Conditions gate.** A ``conditional`` grant authorizes only when every named
  condition is in the caller-supplied ``satisfied_conditions`` set; otherwise it
  resolves to ``CONDITIONAL`` (not authorized) and lists the unmet conditions.
- **Aliases are honored.** A grant on the asset's provenance ``group_id`` (which
  links aliases of one person/work) applies to the asset.

``authorized`` is ``True`` only when the resolved permission is ``ALLOWED``.
"""

from dataclasses import dataclass, field

from src.evaluation.semantics.enums import RightsPermission
from src.provenance.graph import ProvenanceGraph
from src.rights.consent_store import ConsentStore
from src.rights.grants import RightsGrant
from src.rights.purposes import Purpose


@dataclass(frozen=True)
class Authorization:
    """The resolved answer to one authorization question."""

    subject_id: str
    purpose: Purpose
    at_time: str
    permission: RightsPermission
    authorized: bool
    reasons: tuple[str, ...] = ()
    unmet_conditions: tuple[str, ...] = ()
    grant_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "subject_id": self.subject_id,
            "purpose": self.purpose.value,
            "at_time": self.at_time,
            "permission": self.permission.value,
            "authorized": self.authorized,
            "reasons": list(self.reasons),
            "unmet_conditions": list(self.unmet_conditions),
            "grant_ids": list(self.grant_ids),
        }


def _subject_ids_for_asset(graph: ProvenanceGraph | None, asset_id: str) -> tuple[str, ...]:
    """The IDs a grant could be attached to for this asset: the asset itself and
    its provenance ``group_id`` (so an alias/group grant is honored)."""
    ids = [asset_id]
    if graph is not None:
        try:
            node = graph.node(asset_id)
        except KeyError:
            node = None
        if node is not None and node.group_id:
            ids.append(node.group_id)
    return tuple(dict.fromkeys(ids))


def authorize(
    store: ConsentStore,
    graph: ProvenanceGraph | None,
    asset_id: str,
    purpose: Purpose,
    at_time: str,
    *,
    satisfied_conditions: frozenset[str] | set[str] | None = None,
) -> Authorization:
    """Resolve whether ``asset_id`` may be used for ``purpose`` at ``at_time``."""
    satisfied = frozenset(satisfied_conditions or ())
    subject_ids = _subject_ids_for_asset(graph, asset_id)

    applicable: list[RightsGrant] = []
    for sid in subject_ids:
        for g in store.grants_for(sid):
            if g.covers(purpose):
                applicable.append(g)

    if not applicable:
        return Authorization(
            subject_id=asset_id,
            purpose=purpose,
            at_time=at_time,
            permission=RightsPermission.UNKNOWN,
            authorized=False,
            reasons=("rights_not_authorized: no grant covers this asset+purpose (fail closed)",),
        )

    prohibited: list[str] = []
    withdrawn: list[str] = []
    expired: list[str] = []
    allowed: list[str] = []
    conditional_unmet: list[str] = []
    unmet_conditions: set[str] = set()

    for g in applicable:
        if g.status.value == "withdrawn":
            withdrawn.append(g.grant_id)
            continue
        if g.status.value in ("superseded", "quarantined"):
            # A superseded/quarantined grant cannot authorize; treat as absent
            # but record it did not contribute a permission.
            continue
        if g.status.value == "expired" or g.is_expired_at(at_time):
            expired.append(g.grant_id)
            continue
        # status active (or draft treated as non-authorizing) ---------------
        if g.status.value == "draft":
            # A draft grant never authorizes (human must activate).
            conditional_unmet.append(g.grant_id)
            unmet_conditions.add("grant_not_active")
            continue
        if g.permission is RightsPermission.PROHIBITED:
            prohibited.append(g.grant_id)
        elif g.permission is RightsPermission.CONDITIONAL:
            missing = tuple(c for c in g.conditions if c not in satisfied)
            if missing:
                conditional_unmet.append(g.grant_id)
                unmet_conditions.update(missing)
            else:
                allowed.append(g.grant_id)
        elif g.permission is RightsPermission.ALLOWED:
            allowed.append(g.grant_id)

    # Most-restrictive-wins resolution ------------------------------------
    if prohibited:
        return Authorization(
            subject_id=asset_id, purpose=purpose, at_time=at_time,
            permission=RightsPermission.PROHIBITED, authorized=False,
            reasons=("prohibited grant present (most-restrictive-wins over any allow)",),
            grant_ids=tuple(prohibited),
        )
    if withdrawn and not allowed:
        return Authorization(
            subject_id=asset_id, purpose=purpose, at_time=at_time,
            permission=RightsPermission.WITHDRAWN, authorized=False,
            reasons=("rights_expired_or_withdrawn: consent withdrawn for this purpose",),
            grant_ids=tuple(withdrawn),
        )
    if allowed:
        # A still-valid allow authorizes even if another grant expired.
        return Authorization(
            subject_id=asset_id, purpose=purpose, at_time=at_time,
            permission=RightsPermission.ALLOWED, authorized=True,
            reasons=("authorized by an active, unexpired grant for this purpose",),
            grant_ids=tuple(allowed),
        )
    if conditional_unmet:
        return Authorization(
            subject_id=asset_id, purpose=purpose, at_time=at_time,
            permission=RightsPermission.CONDITIONAL, authorized=False,
            reasons=("conditional grant with unmet conditions (fail closed)",),
            unmet_conditions=tuple(sorted(unmet_conditions)),
            grant_ids=tuple(conditional_unmet),
        )
    if expired:
        return Authorization(
            subject_id=asset_id, purpose=purpose, at_time=at_time,
            permission=RightsPermission.EXPIRED, authorized=False,
            reasons=("rights_expired_or_withdrawn: all covering grants have expired",),
            grant_ids=tuple(expired),
        )
    # Only non-authorizing states (e.g. superseded) contributed.
    return Authorization(
        subject_id=asset_id, purpose=purpose, at_time=at_time,
        permission=RightsPermission.UNKNOWN, authorized=False,
        reasons=("rights_not_authorized: no active grant authorizes this purpose (fail closed)",),
    )
