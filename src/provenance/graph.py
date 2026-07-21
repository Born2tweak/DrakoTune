"""Provenance graph with integrity validation (DT-46).

The graph holds identity nodes and their derivation/membership edges (a node's
``parents``) plus append-only corrections. Its validator enforces:

- no duplicate node IDs and only well-formed IDs;
- no broken provenance edges (a parent must exist in the graph);
- required lineage per node type (e.g. a take needs a session) — *active* nodes
  only; legacy nodes are exempt but reported as explicit unknowns;
- no cyclic derivation;
- duplicate-content detection (same fingerprint = renamed file / duplicate audio);
- corrections append and never overwrite the original.

Rights are never inferred here (DT-49 owns enforcement); unknown lineage on a
legacy node is surfaced, not guessed away.
"""

from dataclasses import dataclass, field

from src.evaluation.semantics.errors import (
    ErrorCode,
    QuarantineAction,
    ValidationError,
)
from src.provenance.ids import NodeType, is_valid_id, type_of
from src.provenance.nodes import Correction, NodeStatus, ProvenanceNode

# Minimum required parent node-types for an ACTIVE node to have valid lineage.
# A node satisfies the rule if it has at least one parent of *each* listed type.
_REQUIRED_PARENTS: dict[NodeType, tuple[NodeType, ...]] = {
    NodeType.WORK: (NodeType.SOURCE,),
    NodeType.SESSION: (NodeType.WORK,),
    NodeType.TAKE: (NodeType.SESSION,),
    NodeType.ASSET: (NodeType.TAKE,),
    NodeType.DERIVED: (NodeType.ASSET,),  # (asset OR derived — see _has_parent_type)
    NodeType.RESULT: (NodeType.DERIVED,),
    NodeType.CLAIM: (NodeType.RESULT,),
}

# For these types, a parent of the required type OR of an equivalent type counts.
_PARENT_EQUIVALENTS: dict[NodeType, set[NodeType]] = {
    NodeType.DERIVED: {NodeType.ASSET, NodeType.DERIVED},
    NodeType.RESULT: {NodeType.DERIVED, NodeType.ASSET},
}


@dataclass
class GraphValidationReport:
    """Outcome of validating a provenance graph."""

    errors: tuple[ValidationError, ...] = ()
    duplicate_fingerprints: dict[str, tuple[str, ...]] = field(default_factory=dict)
    legacy_unknown_lineage: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


class ProvenanceGraph:
    """A set of provenance nodes + corrections with integrity validation."""

    def __init__(self) -> None:
        self._nodes: dict[str, ProvenanceNode] = {}
        self._corrections: list[Correction] = []

    # -- construction -------------------------------------------------------
    def add_node(self, node: ProvenanceNode) -> None:
        if node.node_id in self._nodes:
            raise ValueError(f"duplicate node_id {node.node_id!r} (nodes are immutable)")
        self._nodes[node.node_id] = node

    def add_correction(self, correction: Correction) -> None:
        """Append a correction. The superseded node is retained, not mutated."""
        if correction.supersedes_node_id not in self._nodes:
            raise ValueError(
                f"correction supersedes unknown node {correction.supersedes_node_id!r}"
            )
        # Mark the original superseded but keep it (append-only history).
        original = self._nodes[correction.supersedes_node_id]
        self._nodes[correction.supersedes_node_id] = ProvenanceNode(
            node_id=original.node_id,
            node_type=original.node_type,
            created_at=original.created_at,
            owner=original.owner,
            status=NodeStatus.SUPERSEDED,
            group_id=original.group_id,
            parents=original.parents,
            fingerprint=original.fingerprint,
            rights_state=original.rights_state,
            attributes=original.attributes,
        )
        self._corrections.append(correction)
        # The replacement is a new node with its own id.
        if correction.replacement.node_id not in self._nodes:
            self._nodes[correction.replacement.node_id] = correction.replacement

    def node(self, node_id: str) -> ProvenanceNode:
        return self._nodes[node_id]

    def nodes(self) -> tuple[ProvenanceNode, ...]:
        return tuple(self._nodes.values())

    def corrections(self) -> tuple[Correction, ...]:
        return tuple(self._corrections)

    def group_members(self, group_id: str) -> tuple[str, ...]:
        """All node IDs sharing a group identity (e.g. aliases of one person)."""
        return tuple(n.node_id for n in self._nodes.values() if n.group_id == group_id)

    # -- validation ---------------------------------------------------------
    def _has_parent_type(self, node: ProvenanceNode, required: NodeType) -> bool:
        equivalents = _PARENT_EQUIVALENTS.get(node.node_type, {required})
        for pid in node.parents:
            parent = self._nodes.get(pid)
            if parent is not None and parent.node_type in equivalents:
                return True
        return False

    def _detect_cycle(self) -> list[str]:
        """Return a node path forming a derivation cycle, or []."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {nid: WHITE for nid in self._nodes}
        path: list[str] = []

        def visit(nid: str) -> list[str]:
            color[nid] = GRAY
            path.append(nid)
            for pid in self._nodes[nid].parents:
                if pid not in self._nodes:
                    continue
                if color[pid] == GRAY:
                    return path[path.index(pid):] + [pid]
                if color[pid] == WHITE:
                    found = visit(pid)
                    if found:
                        return found
            color[nid] = BLACK
            path.pop()
            return []

        for nid in self._nodes:
            if color[nid] == WHITE:
                cyc = visit(nid)
                if cyc:
                    return cyc
        return []

    def validate(self) -> GraphValidationReport:
        errors: list[ValidationError] = []

        def err(code: ErrorCode, node_id: str, path: str, msg: str) -> None:
            errors.append(
                ValidationError(
                    error_code=code,
                    field_path=path,
                    message=msg,
                    schema="drakotune.provenance_node",
                    schema_version="2.0.0",
                    record_id=node_id or None,
                    quarantine_action=QuarantineAction.QUARANTINE,
                )
            )

        legacy_unknown: list[str] = []
        for node in self._nodes.values():
            # Well-formed, type-consistent IDs.
            if not is_valid_id(node.node_id):
                err(ErrorCode.INVALID_IDENTITY, node.node_id, "node_id", "malformed node id")
            elif type_of(node.node_id) != node.node_type:
                err(
                    ErrorCode.INVALID_IDENTITY,
                    node.node_id,
                    "node_id",
                    f"id prefix does not match node_type {node.node_type.value}",
                )
            # Broken edges: every parent must exist.
            for pid in node.parents:
                if pid not in self._nodes:
                    err(
                        ErrorCode.BROKEN_PROVENANCE_EDGE,
                        node.node_id,
                        "parents",
                        f"parent {pid!r} not present in graph",
                    )
            # Required lineage (active nodes only; legacy is surfaced, not failed).
            required = _REQUIRED_PARENTS.get(node.node_type)
            if required:
                if node.status is NodeStatus.LEGACY:
                    if not node.parents:
                        legacy_unknown.append(node.node_id)
                elif node.status is NodeStatus.ACTIVE:
                    for req in required:
                        if not self._has_parent_type(node, req):
                            err(
                                ErrorCode.BROKEN_PROVENANCE_EDGE,
                                node.node_id,
                                "parents",
                                f"{node.node_type.value} requires a {req.value} ancestor",
                            )

        # Cyclic derivation.
        cycle = self._detect_cycle()
        if cycle:
            err(
                ErrorCode.BROKEN_PROVENANCE_EDGE,
                cycle[0],
                "parents",
                f"cyclic derivation: {' -> '.join(cycle)}",
            )

        return GraphValidationReport(
            errors=tuple(errors),
            duplicate_fingerprints=self.duplicate_fingerprints(),
            legacy_unknown_lineage=tuple(legacy_unknown),
        )

    def duplicate_fingerprints(self) -> dict[str, tuple[str, ...]]:
        """Map each shared fingerprint to the node IDs carrying it.

        Catches a renamed file (same audio, new name) and duplicate audio: they
        share a content fingerprint even with different IDs/filenames.
        """
        by_fp: dict[str, list[str]] = {}
        for n in self._nodes.values():
            if n.fingerprint:
                by_fp.setdefault(n.fingerprint, []).append(n.node_id)
        return {fp: tuple(sorted(ids)) for fp, ids in by_fp.items() if len(ids) > 1}
