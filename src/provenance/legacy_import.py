"""Import legacy records into the provenance graph as explicit-unknown nodes (DT-46).

Current schema `1.0.0` records (e.g. ``AudioAsset``) predate the identity graph.
They are imported as ``legacy`` nodes with ``unknown`` rights and no asserted
lineage. Missing rights and missing source are **not** inferred — they are
surfaced as explicit unknowns so downstream gates fail closed.

Sensitive storage paths and direct filenames are not copied into the shareable
provenance node; only non-identifying technical metadata is retained.
"""

from src.evaluation.semantics.enums import RightsPermission
from src.provenance.ids import NodeType, mint_content_id
from src.provenance.nodes import NodeStatus, ProvenanceNode


def import_legacy_asset(
    asset,
    *,
    fingerprint: str | None = None,
    owner: str | None = None,
    created_at: str | None = None,
) -> ProvenanceNode:
    """Map a legacy ``AudioAsset`` to a legacy provenance asset node.

    If a content ``fingerprint`` is provided, the node ID is content-addressed
    on it, so a renamed copy of the same audio maps to the same node ID.
    """
    # Content-address on the fingerprint when available, else on the legacy id.
    id_body = {"fingerprint": fingerprint} if fingerprint else {"legacy_id": asset.id}
    node_id = mint_content_id(NodeType.ASSET, id_body)

    return ProvenanceNode(
        node_id=node_id,
        node_type=NodeType.ASSET,
        created_at=created_at or getattr(asset, "created_at", "") or "1970-01-01T00:00:00Z",
        owner=owner or getattr(asset, "owner_id", "unknown") or "unknown",
        status=NodeStatus.LEGACY,
        group_id=None,  # unknown grouping; not inferred
        parents=(),  # unknown lineage; surfaced by the validator, not guessed
        fingerprint=fingerprint,
        rights_state=RightsPermission.UNKNOWN,  # never inferred
        attributes={
            "legacy_asset_id": asset.id,
            "sample_rate": getattr(asset, "sample_rate", None),
            "channels": getattr(asset, "channels", None),
            "duration": getattr(asset, "duration", None),
            "lineage": "unknown",
            "rights": "unknown",
            "import_note": "legacy_v1_asset; rights and source not inferred",
        },
    )
