"""Withdrawal propagation and deletion simulation (DT-49).

When consent is withdrawn for a subject (an asset, or a ``group_id`` linking a
person's aliases), the effect must propagate through the provenance derivation
graph to every downstream derivative, result, and claim — and to *nothing else*.

:func:`plan_withdrawal` produces a :class:`WithdrawalPlan`: the exact set of
affected nodes, the claims that must be suspended, and the deletions that *would*
be performed. It is a **simulation** — ``executed`` is always ``False``. Real
deletion authority is a human gate (DT-49 Field 15), so this module never
deletes anything; it enumerates a recoverable plan for a human to approve.

:func:`suspend_affected_claims` applies the claim half of a plan to a
:class:`~src.evaluation.semantics.claims.ClaimQuarantineRegistry` by quarantining
the affected claims — the reversible enforcement the claim layer already
supports.
"""

from dataclasses import dataclass, field

from src.evaluation.semantics.claims import ClaimQuarantineRegistry
from src.provenance.graph import ProvenanceGraph
from src.provenance.ids import NodeType
from src.provenance.nodes import ProvenanceNode


@dataclass(frozen=True)
class WithdrawalEvent:
    """A request to withdraw consent for a subject at a time."""

    event_id: str
    subject_id: str
    requested_at: str
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "subject_id": self.subject_id,
            "requested_at": self.requested_at,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class WithdrawalPlan:
    """The enumerated (but not executed) consequences of a withdrawal."""

    subject_id: str
    seed_ids: tuple[str, ...]
    withdrawn_at: str
    affected_assets: tuple[str, ...]
    affected_results: tuple[str, ...]
    affected_claims: tuple[str, ...]
    claim_suspensions: tuple[str, ...]
    simulated_deletions: tuple[str, ...]
    preserved_node_count: int
    executed: bool = False  # DT-49 never executes deletion; human-gated

    def to_dict(self) -> dict:
        return {
            "subject_id": self.subject_id,
            "seed_ids": list(self.seed_ids),
            "withdrawn_at": self.withdrawn_at,
            "affected_assets": list(self.affected_assets),
            "affected_results": list(self.affected_results),
            "affected_claims": list(self.affected_claims),
            "claim_suspensions": list(self.claim_suspensions),
            "simulated_deletions": list(self.simulated_deletions),
            "preserved_node_count": self.preserved_node_count,
            "executed": self.executed,
        }


def _children_index(graph: ProvenanceGraph) -> dict[str, list[str]]:
    """Map each node ID to the IDs that list it as a parent (its children)."""
    children: dict[str, list[str]] = {}
    for node in graph.nodes():
        for pid in node.parents:
            children.setdefault(pid, []).append(node.node_id)
    return children


def _seed_ids(graph: ProvenanceGraph, subject_id: str) -> tuple[str, ...]:
    """Resolve a subject to concrete graph seed nodes.

    If ``subject_id`` is a ``group_id`` (aliases of one person/work), every group
    member is a seed — so withdrawing on the group reaches a re-identified alias.
    If it is a node ID, that node is the seed.
    """
    members = graph.group_members(subject_id)
    if members:
        return members
    try:
        graph.node(subject_id)
    except KeyError:
        return ()
    return (subject_id,)


def plan_withdrawal(
    graph: ProvenanceGraph,
    subject_id: str,
    at_time: str,
    *,
    claim_registry: ClaimQuarantineRegistry | None = None,
    reason: str = "",
) -> WithdrawalPlan:
    """Enumerate every descendant affected by withdrawing ``subject_id``.

    Traversal follows child edges transitively from the seed set. A node is
    *affected* iff it is a seed or descends from one; every other node is
    preserved. This is what guarantees "no unrelated deletion" (Field 13).
    """
    seeds = _seed_ids(graph, subject_id)
    children = _children_index(graph)

    affected: set[str] = set()
    stack = list(seeds)
    while stack:
        nid = stack.pop()
        if nid in affected:
            continue
        affected.add(nid)
        for child in children.get(nid, ()):
            if child not in affected:
                stack.append(child)

    def _typed(ids: set[str], node_type: NodeType) -> tuple[str, ...]:
        out = []
        for nid in ids:
            try:
                node = graph.node(nid)
            except KeyError:
                continue
            if node.node_type is node_type:
                out.append(nid)
        return tuple(sorted(out))

    affected_assets = tuple(sorted(
        nid for nid in affected
        if _node_type(graph, nid) in (NodeType.ASSET, NodeType.DERIVED, NodeType.TAKE)
    ))
    affected_results = _typed(affected, NodeType.RESULT)
    graph_affected_claims = set(_typed(affected, NodeType.CLAIM))

    # Registry claims whose supporting_results intersect affected results.
    registry_affected_claims: set[str] = set()
    if claim_registry is not None:
        affected_result_set = set(affected_results) | affected  # results or any affected id
        for claim in claim_registry.all():
            if set(claim.supporting_results) & affected_result_set:
                registry_affected_claims.add(claim.claim_id)

    affected_claims = tuple(sorted(graph_affected_claims | registry_affected_claims))

    # Deletions we *would* perform: the affected data-bearing nodes (never
    # results/claims, which are suspended, and never unrelated nodes).
    simulated_deletions = affected_assets

    preserved = len(graph.nodes()) - len(affected)

    return WithdrawalPlan(
        subject_id=subject_id,
        seed_ids=tuple(sorted(seeds)),
        withdrawn_at=at_time,
        affected_assets=affected_assets,
        affected_results=affected_results,
        affected_claims=affected_claims,
        claim_suspensions=affected_claims,
        simulated_deletions=simulated_deletions,
        preserved_node_count=preserved,
    )


def _node_type(graph: ProvenanceGraph, nid: str) -> NodeType | None:
    try:
        return graph.node(nid).node_type
    except KeyError:
        return None


def suspend_affected_claims(
    registry: ClaimQuarantineRegistry, plan: WithdrawalPlan
) -> tuple[str, ...]:
    """Quarantine every claim named in ``plan.claim_suspensions``.

    Returns the IDs actually suspended. Idempotent-safe (quarantine merges
    reasons). This is the reversible enforcement DT-49 authorizes; it does not
    delete or retract, only suspends pending human review.
    """
    suspended: list[str] = []
    reason = (f"rights_withdrawn:{plan.subject_id}",)
    for cid in plan.claim_suspensions:
        try:
            registry.get(cid)
        except KeyError:
            continue
        registry.quarantine(cid, reason)
        suspended.append(cid)
    return tuple(suspended)
