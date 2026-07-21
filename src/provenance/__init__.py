"""Identity and provenance graph (DT-46).

Stable, opaque, typed identities for the full evidence chain — source, work,
performer, session, take, asset, derived artifact, split, protocol, listener,
item, result, and claim — plus a graph validator that enforces edge integrity,
required lineage, cycle-freedom, duplicate-content detection, and append-only
corrections. Rights are recorded, never inferred (DT-49 enforces).
"""

from src.provenance.graph import GraphValidationReport, ProvenanceGraph
from src.provenance.ids import (
    NodeType,
    is_valid_id,
    mint_content_id,
    mint_random_id,
    prefix_for,
    type_of,
)
from src.provenance.legacy_import import import_legacy_asset
from src.provenance.nodes import (
    PROVENANCE_SCHEMA,
    PROVENANCE_SCHEMA_VERSION,
    Correction,
    NodeStatus,
    ProvenanceNode,
)

__all__ = [
    "NodeType",
    "NodeStatus",
    "ProvenanceNode",
    "Correction",
    "ProvenanceGraph",
    "GraphValidationReport",
    "mint_content_id",
    "mint_random_id",
    "prefix_for",
    "type_of",
    "is_valid_id",
    "import_legacy_asset",
    "PROVENANCE_SCHEMA",
    "PROVENANCE_SCHEMA_VERSION",
]
