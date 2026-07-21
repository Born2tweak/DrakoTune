"""DT-46 identity and provenance schema v2 — schema + graph suite.

Acceptance (Field 13): round trip, canonical hash, graph integrity, duplicate
detection, legacy unknowns explicit, no ID collisions. Adversarial (Field 16):
aliases, renamed file, duplicate audio, cyclic derivation, correction overwrite,
missing source.
"""

import pytest

from src.evaluation.semantics.enums import RightsPermission
from src.provenance import (
    Correction,
    NodeStatus,
    NodeType,
    ProvenanceGraph,
    ProvenanceNode,
    import_legacy_asset,
    is_valid_id,
    mint_content_id,
    type_of,
)
from src.shared_types import AudioAsset

TS = "2026-07-21T12:00:00Z"


def _node(node_type, node_id=None, **kw):
    nid = node_id or mint_content_id(node_type, {"k": kw.get("_seed", node_type.value)})
    kw.pop("_seed", None)
    return ProvenanceNode(node_id=nid, node_type=node_type, created_at=TS, **kw)


def _lineage_graph():
    """A valid source->work->session->take->asset->derived->result->claim chain."""
    g = ProvenanceGraph()
    src = _node(NodeType.SOURCE, _seed="s")
    work = _node(NodeType.WORK, _seed="w", parents=(src.node_id,))
    sess = _node(NodeType.SESSION, _seed="ss", parents=(work.node_id,))
    take = _node(NodeType.TAKE, _seed="t", parents=(sess.node_id,))
    asset = _node(NodeType.ASSET, _seed="a", parents=(take.node_id,), fingerprint="sha256:aa")
    deriv = _node(NodeType.DERIVED, _seed="d", parents=(asset.node_id,), fingerprint="sha256:dd")
    result = _node(NodeType.RESULT, _seed="r", parents=(deriv.node_id,))
    claim = _node(NodeType.CLAIM, _seed="c", parents=(result.node_id,))
    for n in (src, work, sess, take, asset, deriv, result, claim):
        g.add_node(n)
    return g, {"src": src, "work": work, "sess": sess, "take": take,
               "asset": asset, "deriv": deriv, "result": result, "claim": claim}


# --------------------------------------------------------------------------
# IDs and round trip
# --------------------------------------------------------------------------

def test_ids_are_typed_and_valid():
    nid = mint_content_id(NodeType.ASSET, {"x": 1})
    assert nid.startswith("asset_")
    assert is_valid_id(nid)
    assert type_of(nid) is NodeType.ASSET


def test_content_id_is_stable_and_collision_free():
    a = mint_content_id(NodeType.ASSET, {"x": 1})
    a2 = mint_content_id(NodeType.ASSET, {"x": 1})
    b = mint_content_id(NodeType.ASSET, {"x": 2})
    assert a == a2  # deterministic
    assert a != b  # distinct content -> distinct id


def test_node_roundtrip_and_canonical_hash():
    n = _node(NodeType.ASSET, fingerprint="sha256:aa", parents=("take_x",))
    d = n.to_dict()
    assert d["content_hash"].startswith("sha256:")
    back = ProvenanceNode.from_dict(d)
    assert back.canonical_hash() == n.canonical_hash()
    assert back.rights_state is RightsPermission.UNKNOWN


# --------------------------------------------------------------------------
# Graph integrity
# --------------------------------------------------------------------------

def test_valid_lineage_graph_passes():
    g, _ = _lineage_graph()
    report = g.validate()
    assert report.ok, report.errors


def test_duplicate_node_id_rejected():
    g = ProvenanceGraph()
    n = _node(NodeType.SESSION, node_id="sess_dup", parents=("work_x",))
    g.add_node(n)
    with pytest.raises(ValueError, match="duplicate"):
        g.add_node(_node(NodeType.SESSION, node_id="sess_dup", parents=("work_y",)))


def test_missing_source_is_broken_edge():
    # An active take whose session parent is absent -> broken provenance edge.
    g = ProvenanceGraph()
    take = _node(NodeType.TAKE, parents=("sess_absent",))
    g.add_node(take)
    report = g.validate()
    assert not report.ok
    assert any(e.error_code.value == "broken_provenance_edge" for e in report.errors)


def test_active_asset_without_lineage_flagged():
    g = ProvenanceGraph()
    asset = _node(NodeType.ASSET)  # no parents, active
    g.add_node(asset)
    report = g.validate()
    assert any(
        e.error_code.value == "broken_provenance_edge" and "requires a take" in e.message
        for e in report.errors
    )


def test_id_prefix_must_match_node_type():
    g = ProvenanceGraph()
    bad = ProvenanceNode(node_id="claim_x", node_type=NodeType.ASSET, created_at=TS)
    g.add_node(bad)
    report = g.validate()
    assert any(e.error_code.value == "invalid_identity" for e in report.errors)


# --------------------------------------------------------------------------
# Cyclic derivation
# --------------------------------------------------------------------------

def test_cyclic_derivation_detected():
    g = ProvenanceGraph()
    # deriv_a -> parent deriv_b -> parent deriv_a  (a cycle)
    a = ProvenanceNode(node_id="deriv_a", node_type=NodeType.DERIVED, created_at=TS, parents=("deriv_b",))
    b = ProvenanceNode(node_id="deriv_b", node_type=NodeType.DERIVED, created_at=TS, parents=("deriv_a",))
    g.add_node(a)
    g.add_node(b)
    report = g.validate()
    assert any("cyclic derivation" in e.message for e in report.errors)


# --------------------------------------------------------------------------
# Duplicate detection: renamed file / duplicate audio
# --------------------------------------------------------------------------

def test_renamed_file_and_duplicate_audio_detected_by_fingerprint():
    g, nodes = _lineage_graph()
    # a second asset with the SAME fingerprint but different id/name = renamed dup
    dup = ProvenanceNode(
        node_id="asset_renamed",
        node_type=NodeType.ASSET,
        created_at=TS,
        parents=(nodes["take"].node_id,),
        fingerprint="sha256:aa",  # same content as nodes['asset']
    )
    g.add_node(dup)
    dups = g.validate().duplicate_fingerprints
    assert "sha256:aa" in dups
    assert set(dups["sha256:aa"]) == {nodes["asset"].node_id, "asset_renamed"}


# --------------------------------------------------------------------------
# Aliases: same person under two performer nodes, one group identity
# --------------------------------------------------------------------------

def test_aliases_link_through_group_identity():
    g = ProvenanceGraph()
    src = _node(NodeType.SOURCE, _seed="s")
    g.add_node(src)
    alias1 = ProvenanceNode(node_id="perf_alias1", node_type=NodeType.PERFORMER, created_at=TS, group_id="group_person_A")
    alias2 = ProvenanceNode(node_id="perf_alias2", node_type=NodeType.PERFORMER, created_at=TS, group_id="group_person_A")
    g.add_node(alias1)
    g.add_node(alias2)
    assert set(g.group_members("group_person_A")) == {"perf_alias1", "perf_alias2"}


# --------------------------------------------------------------------------
# Corrections append, never overwrite
# --------------------------------------------------------------------------

def test_correction_appends_and_supersedes_without_mutation():
    g, nodes = _lineage_graph()
    original = nodes["asset"]
    original_hash = original.canonical_hash()
    replacement = ProvenanceNode(
        node_id="asset_corrected",
        node_type=NodeType.ASSET,
        created_at=TS,
        parents=(nodes["take"].node_id,),
        fingerprint="sha256:aa_fixed",
    )
    corr = Correction(
        correction_id="correction_1",
        supersedes_node_id=original.node_id,
        created_at=TS,
        reason="wrong_fingerprint",
        replacement=replacement,
    )
    g.add_correction(corr)
    # original still present, now superseded, and its own hash body unchanged
    superseded = g.node(original.node_id)
    assert superseded.status is NodeStatus.SUPERSEDED
    # the correction is recorded and the replacement exists as a new node
    assert len(g.corrections()) == 1
    assert g.node("asset_corrected").fingerprint == "sha256:aa_fixed"
    # a correction pointing at a nonexistent node is rejected
    with pytest.raises(ValueError, match="unknown node"):
        g.add_correction(Correction("c2", "asset_ghost", TS, "x", replacement))
    # original identity was not reused for the replacement (no overwrite)
    assert original_hash != g.node("asset_corrected").canonical_hash()


# --------------------------------------------------------------------------
# Legacy import: explicit unknowns, no inference
# --------------------------------------------------------------------------

def test_legacy_asset_imports_as_explicit_unknown():
    asset = AudioAsset(
        id="legacy_001",
        owner_id="owner_x",
        original_storage_path="/private/secret/take1.wav",
        sample_rate=48000,
        channels=1,
        duration=12.3,
    )
    node = import_legacy_asset(asset, fingerprint="sha256:legacyaudio")
    assert node.status is NodeStatus.LEGACY
    assert node.rights_state is RightsPermission.UNKNOWN
    assert node.parents == ()  # lineage not inferred
    assert node.attributes["lineage"] == "unknown"
    # sensitive storage path is NOT copied into the shareable node
    serialized = str(node.to_dict())
    assert "/private/secret" not in serialized


def test_legacy_node_missing_lineage_is_surfaced_not_failed():
    asset = AudioAsset("legacy_002", "owner", "/p/x.wav", 44100, 1, 5.0)
    node = import_legacy_asset(asset, fingerprint="sha256:legB")
    g = ProvenanceGraph()
    g.add_node(node)
    report = g.validate()
    # legacy nodes do not raise required-lineage errors...
    assert not any(e.error_code.value == "broken_provenance_edge" for e in report.errors)
    # ...but their unknown lineage is explicitly surfaced
    assert node.node_id in report.legacy_unknown_lineage


def test_renamed_legacy_file_maps_to_same_content_id():
    a1 = AudioAsset("id_name_one", "o", "/p/one.wav", 48000, 1, 3.0)
    a2 = AudioAsset("id_name_two", "o", "/p/two.wav", 48000, 1, 3.0)
    n1 = import_legacy_asset(a1, fingerprint="sha256:samecontent")
    n2 = import_legacy_asset(a2, fingerprint="sha256:samecontent")
    assert n1.node_id == n2.node_id  # renamed file -> same content-addressed id
