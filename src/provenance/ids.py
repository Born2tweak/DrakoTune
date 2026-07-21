"""Typed, opaque, stable identifiers for the provenance graph (DT-46).

IDs are opaque strings with a type prefix. Consumers must not derive meaning
from sequence or timestamp (canonical spec: "Identity and canonical
serialization"). Two minting strategies are supported:

- ``mint_content_id`` — content-addressed: a SHA-256 over a canonical body. Two
  records that mean the same thing get the same ID, which is what lets us detect
  a *renamed file* (same audio, new name) as the same asset.
- ``mint_random_id`` — for nodes with no natural content key (e.g. a session),
  a random opaque suffix.

An ID never encodes a rights, quality, or ordering claim.
"""

import hashlib
import secrets
from enum import Enum

from src.evaluation.semantics.canonical import canonical_bytes


class NodeType(str, Enum):
    """The identity-graph node types (Data/Evidence/Provenance spec)."""

    SOURCE = "source"
    WORK = "work"
    PERFORMER = "performer"
    SESSION = "session"
    TAKE = "take"
    ASSET = "asset"
    DERIVED = "derived"
    SPLIT = "split"
    PROTOCOL = "protocol"
    LISTENER = "listener"
    ITEM = "item"
    RESULT = "result"
    CLAIM = "claim"
    GROUP = "group"
    CORRECTION = "correction"


# Short stable prefixes per node type.
_PREFIX: dict[NodeType, str] = {
    NodeType.SOURCE: "src",
    NodeType.WORK: "work",
    NodeType.PERFORMER: "perf",
    NodeType.SESSION: "sess",
    NodeType.TAKE: "take",
    NodeType.ASSET: "asset",
    NodeType.DERIVED: "deriv",
    NodeType.SPLIT: "split",
    NodeType.PROTOCOL: "proto",
    NodeType.LISTENER: "listener",
    NodeType.ITEM: "item",
    NodeType.RESULT: "result",
    NodeType.CLAIM: "claim",
    NodeType.GROUP: "group",
    NodeType.CORRECTION: "correction",
}

_PREFIX_TO_TYPE = {v: k for k, v in _PREFIX.items()}


def prefix_for(node_type: NodeType) -> str:
    return _PREFIX[node_type]


def mint_content_id(node_type: NodeType, body: dict, *, length: int = 24) -> str:
    """Content-addressed ID: ``<prefix>_<sha256(canonical body)[:length]>``."""
    digest = hashlib.sha256(canonical_bytes(body)).hexdigest()[:length]
    return f"{_PREFIX[node_type]}_{digest}"


def mint_random_id(node_type: NodeType, *, nbytes: int = 12) -> str:
    """Random opaque ID for nodes without a natural content key."""
    return f"{_PREFIX[node_type]}_{secrets.token_hex(nbytes)}"


def type_of(node_id: str) -> NodeType | None:
    """Return the NodeType encoded by an ID prefix, or None if unrecognized."""
    if "_" not in node_id:
        return None
    return _PREFIX_TO_TYPE.get(node_id.split("_", 1)[0])


def is_valid_id(node_id: str) -> bool:
    """A well-formed ID has a known prefix and a non-empty opaque suffix."""
    if not isinstance(node_id, str) or "_" not in node_id:
        return False
    prefix, suffix = node_id.split("_", 1)
    return prefix in _PREFIX_TO_TYPE and len(suffix) > 0
