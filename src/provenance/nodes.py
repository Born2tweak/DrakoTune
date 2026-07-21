"""Provenance graph nodes (DT-46).

Every node carries a stable ID, schema version, creation time, owner, status,
optional content hash, a group identity (so aliases of the same person/work are
linkable without exposing direct identity), parent edges, and a typed attribute
bag. Rights are represented only as an explicit permission state — DT-46 records
provenance and never *infers* rights (that enforcement is DT-49).

Records are immutable. A correction is a new ``Correction`` node that points at
the superseded node; the original is never mutated.
"""

from dataclasses import dataclass, field
from enum import Enum

from src.evaluation.semantics.canonical import content_hash
from src.evaluation.semantics.enums import RightsPermission, parse_enum
from src.provenance.ids import NodeType


class NodeStatus(str, Enum):
    ACTIVE = "active"
    LEGACY = "legacy"
    QUARANTINED = "quarantined"
    SUPERSEDED = "superseded"


PROVENANCE_SCHEMA = "drakotune.provenance_node"
PROVENANCE_SCHEMA_VERSION = "2.0.0"


@dataclass(frozen=True)
class ProvenanceNode:
    """One identity-graph node."""

    node_id: str
    node_type: NodeType
    created_at: str
    owner: str = "unknown"
    status: NodeStatus = NodeStatus.ACTIVE
    group_id: str | None = None
    parents: tuple[str, ...] = ()
    fingerprint: str | None = None  # content hash of the underlying artifact
    rights_state: RightsPermission = RightsPermission.UNKNOWN
    attributes: dict = field(default_factory=dict)
    schema: str = PROVENANCE_SCHEMA
    schema_version: str = PROVENANCE_SCHEMA_VERSION

    def to_dict(self, *, with_hash: bool = True) -> dict:
        payload = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "created_at": self.created_at,
            "owner": self.owner,
            "status": self.status.value,
            "group_id": self.group_id,
            "parents": list(self.parents),
            "fingerprint": self.fingerprint,
            "rights_state": self.rights_state.value,
            "attributes": dict(self.attributes),
        }
        if with_hash:
            payload["content_hash"] = content_hash(payload)
        return payload

    @classmethod
    def from_dict(cls, d: dict) -> "ProvenanceNode":
        return cls(
            node_id=d["node_id"],
            node_type=parse_enum(NodeType, d["node_type"]),
            created_at=d["created_at"],
            owner=d.get("owner", "unknown"),
            status=parse_enum(NodeStatus, d.get("status", "active")),
            group_id=d.get("group_id"),
            parents=tuple(d.get("parents", ())),
            fingerprint=d.get("fingerprint"),
            rights_state=parse_enum(RightsPermission, d.get("rights_state", "unknown")),
            attributes=dict(d.get("attributes", {})),
            schema=d.get("schema", PROVENANCE_SCHEMA),
            schema_version=d.get("schema_version", PROVENANCE_SCHEMA_VERSION),
        )

    def canonical_hash(self) -> str:
        return content_hash(self.to_dict(with_hash=False))


@dataclass(frozen=True)
class Correction:
    """An append-only correction to a prior node. Never mutates the original."""

    correction_id: str
    supersedes_node_id: str
    created_at: str
    reason: str
    replacement: ProvenanceNode
    owner: str = "unknown"
    schema: str = "drakotune.provenance_correction"
    schema_version: str = PROVENANCE_SCHEMA_VERSION

    def to_dict(self, *, with_hash: bool = True) -> dict:
        payload = {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "correction_id": self.correction_id,
            "supersedes_node_id": self.supersedes_node_id,
            "created_at": self.created_at,
            "reason": self.reason,
            "owner": self.owner,
            "replacement": self.replacement.to_dict(),
        }
        if with_hash:
            payload["content_hash"] = content_hash(payload)
        return payload

    @classmethod
    def from_dict(cls, d: dict) -> "Correction":
        return cls(
            correction_id=d["correction_id"],
            supersedes_node_id=d["supersedes_node_id"],
            created_at=d["created_at"],
            reason=d["reason"],
            replacement=ProvenanceNode.from_dict(d["replacement"]),
            owner=d.get("owner", "unknown"),
            schema=d.get("schema", "drakotune.provenance_correction"),
            schema_version=d.get("schema_version", PROVENANCE_SCHEMA_VERSION),
        )
