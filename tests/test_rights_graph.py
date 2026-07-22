"""DT-49 — Rights, Consent, and Withdrawal Graph.

Covers the contract's acceptance (Field 13), automated verification (Field 14),
and adversarial cases (Field 16):

- purpose matrix, expiry, conditional use;
- graph traversal: withdrawal enumerates *all* fixture descendants and affected
  claims with *no unrelated deletion*;
- rebuild/retract simulation (never executes deletion);
- redaction (shareable records exclude the consent handle);
- adversarial: conflicting grants, expired consent, orphan derivative,
  re-identified alias, absent public-example permission — all fail closed.
"""

import pytest

from src.evaluation.semantics.claims import Claim, ClaimQuarantineRegistry
from src.evaluation.semantics.enums import (
    ClaimClass,
    ClaimStatus,
    GrantStatus,
    RightsPermission,
)
from src.provenance.graph import ProvenanceGraph
from src.provenance.ids import NodeType
from src.provenance.nodes import NodeStatus, ProvenanceNode
from src.rights import (
    InMemoryConsentStore,
    Purpose,
    RightsGrant,
    authorize,
    plan_withdrawal,
    suspend_affected_claims,
)

T0 = "2026-01-01T00:00:00Z"
T1 = "2026-06-01T00:00:00Z"
T2 = "2027-01-01T00:00:00Z"


def _grant(gid, subject, purposes, permission, **kw):
    return RightsGrant(
        grant_id=gid,
        subject_id=subject,
        purposes=tuple(purposes),
        permission=permission,
        granted_at=T0,
        **kw,
    )


def _node(nid, ntype, parents=(), group=None, status=NodeStatus.ACTIVE):
    return ProvenanceNode(
        node_id=nid,
        node_type=ntype,
        created_at=T0,
        status=status,
        group_id=group,
        parents=tuple(parents),
    )


# --------------------------------------------------------------------------
# authorize — purpose matrix, fail-closed, precedence
# --------------------------------------------------------------------------

def test_no_grant_fails_closed_unknown():
    store = InMemoryConsentStore()
    auth = authorize(store, None, "asset_a", Purpose.INTERNAL_ANALYSIS, T1)
    assert auth.permission is RightsPermission.UNKNOWN
    assert auth.authorized is False


def test_allowed_only_for_covered_purpose():
    store = InMemoryConsentStore([
        _grant("g1", "asset_a", [Purpose.SYNTHETIC_EVALUATION], RightsPermission.ALLOWED),
    ])
    ok = authorize(store, None, "asset_a", Purpose.SYNTHETIC_EVALUATION, T1)
    assert ok.authorized is True and ok.permission is RightsPermission.ALLOWED
    # A purpose the grant does not cover fails closed.
    other = authorize(store, None, "asset_a", Purpose.PUBLIC_EXAMPLE, T1)
    assert other.authorized is False
    assert other.permission is RightsPermission.UNKNOWN


def test_public_example_permission_absent_fails_closed():
    """Adversarial: an asset usable internally is NOT usable as a public example."""
    store = InMemoryConsentStore([
        _grant("g1", "asset_a", [Purpose.INTERNAL_ANALYSIS], RightsPermission.ALLOWED),
    ])
    auth = authorize(store, None, "asset_a", Purpose.PUBLIC_EXAMPLE, T1)
    assert auth.authorized is False
    assert auth.permission is RightsPermission.UNKNOWN


def test_conflicting_grants_resolve_to_prohibited():
    """Adversarial: allowed + prohibited for the same purpose => prohibited."""
    store = InMemoryConsentStore([
        _grant("g_allow", "asset_a", [Purpose.MODEL_TRAINING], RightsPermission.ALLOWED),
        _grant("g_deny", "asset_a", [Purpose.MODEL_TRAINING], RightsPermission.PROHIBITED),
    ])
    auth = authorize(store, None, "asset_a", Purpose.MODEL_TRAINING, T1)
    assert auth.permission is RightsPermission.PROHIBITED
    assert auth.authorized is False
    assert "g_deny" in auth.grant_ids


def test_expiry_blocks_after_expires_at():
    store = InMemoryConsentStore([
        _grant("g1", "asset_a", [Purpose.LISTENING_STUDY], RightsPermission.ALLOWED,
               expires_at=T2),
    ])
    assert authorize(store, None, "asset_a", Purpose.LISTENING_STUDY, T1).authorized is True
    expired = authorize(store, None, "asset_a", Purpose.LISTENING_STUDY, T2)
    assert expired.authorized is False
    assert expired.permission is RightsPermission.EXPIRED


def test_a_valid_allow_survives_a_second_expired_grant():
    store = InMemoryConsentStore([
        _grant("g_expired", "asset_a", [Purpose.LISTENING_STUDY], RightsPermission.ALLOWED,
               expires_at=T1),
        _grant("g_valid", "asset_a", [Purpose.LISTENING_STUDY], RightsPermission.ALLOWED,
               expires_at=T2),
    ])
    auth = authorize(store, None, "asset_a", Purpose.LISTENING_STUDY, T1 + "1")
    assert auth.authorized is True
    assert auth.grant_ids == ("g_valid",)


def test_conditional_use_requires_all_conditions():
    store = InMemoryConsentStore([
        _grant("g1", "asset_a", [Purpose.PUBLIC_EXAMPLE], RightsPermission.CONDITIONAL,
               conditions=("attribution", "no_commercial")),
    ])
    unmet = authorize(store, None, "asset_a", Purpose.PUBLIC_EXAMPLE, T1,
                      satisfied_conditions={"attribution"})
    assert unmet.authorized is False
    assert unmet.permission is RightsPermission.CONDITIONAL
    assert "no_commercial" in unmet.unmet_conditions

    met = authorize(store, None, "asset_a", Purpose.PUBLIC_EXAMPLE, T1,
                    satisfied_conditions={"attribution", "no_commercial"})
    assert met.authorized is True


def test_draft_and_withdrawn_grants_do_not_authorize():
    store = InMemoryConsentStore([
        _grant("g_draft", "asset_a", [Purpose.INTERNAL_ANALYSIS], RightsPermission.ALLOWED,
               status=GrantStatus.DRAFT),
    ])
    assert authorize(store, None, "asset_a", Purpose.INTERNAL_ANALYSIS, T1).authorized is False
    store2 = InMemoryConsentStore([
        _grant("g_w", "asset_a", [Purpose.INTERNAL_ANALYSIS], RightsPermission.ALLOWED,
               status=GrantStatus.WITHDRAWN),
    ])
    w = authorize(store2, None, "asset_a", Purpose.INTERNAL_ANALYSIS, T1)
    assert w.authorized is False
    assert w.permission is RightsPermission.WITHDRAWN


def test_grant_rejects_nondeclarable_permission():
    with pytest.raises(ValueError):
        _grant("bad", "asset_a", [Purpose.INTERNAL_ANALYSIS], RightsPermission.UNKNOWN)
    with pytest.raises(ValueError):
        # conditional grant with no conditions is malformed
        _grant("bad2", "asset_a", [Purpose.INTERNAL_ANALYSIS], RightsPermission.CONDITIONAL)


# --------------------------------------------------------------------------
# alias / group authorization
# --------------------------------------------------------------------------

def test_group_grant_authorizes_aliased_asset():
    graph = ProvenanceGraph()
    graph.add_node(_node("asset_alias1", NodeType.ASSET, group="group_person"))
    store = InMemoryConsentStore([
        _grant("g1", "group_person", [Purpose.SYNTHETIC_EVALUATION], RightsPermission.ALLOWED),
    ])
    auth = authorize(store, graph, "asset_alias1", Purpose.SYNTHETIC_EVALUATION, T1)
    assert auth.authorized is True
    assert auth.grant_ids == ("g1",)


# --------------------------------------------------------------------------
# withdrawal propagation
# --------------------------------------------------------------------------

def _lineage_graph():
    """A small provenance lineage plus an unrelated branch that must be preserved."""
    g = ProvenanceGraph()
    # affected branch: asset -> derived -> result -> claim
    g.add_node(_node("asset_x", NodeType.ASSET, group="group_x"))
    g.add_node(_node("deriv_x", NodeType.DERIVED, parents=["asset_x"]))
    g.add_node(_node("result_x", NodeType.RESULT, parents=["deriv_x"]))
    g.add_node(_node("claim_x", NodeType.CLAIM, parents=["result_x"]))
    # unrelated branch that shares nothing
    g.add_node(_node("asset_y", NodeType.ASSET, group="group_y"))
    g.add_node(_node("deriv_y", NodeType.DERIVED, parents=["asset_y"]))
    g.add_node(_node("result_y", NodeType.RESULT, parents=["deriv_y"]))
    return g


def test_withdrawal_enumerates_all_descendants_and_nothing_unrelated():
    g = _lineage_graph()
    plan = plan_withdrawal(g, "asset_x", T2)
    affected = set(plan.affected_assets) | set(plan.affected_results) | set(plan.affected_claims)
    # all descendants of asset_x are reached
    assert {"asset_x", "deriv_x"} <= set(plan.affected_assets)
    assert plan.affected_results == ("result_x",)
    assert plan.affected_claims == ("claim_x",)
    # nothing from the unrelated branch is touched
    assert "asset_y" not in affected
    assert "result_y" not in affected
    # preserved count == unrelated nodes (asset_y, deriv_y, result_y)
    assert plan.preserved_node_count == 3
    # a plan is a simulation: never executed
    assert plan.executed is False


def test_orphan_derivative_is_affected_by_parent_withdrawal():
    """Adversarial: a derivative whose source asset is withdrawn is enumerated."""
    g = _lineage_graph()
    plan = plan_withdrawal(g, "asset_x", T2)
    assert "deriv_x" in plan.simulated_deletions


def test_reidentified_alias_group_withdrawal_reaches_all_members():
    """Adversarial: withdrawing on a group reaches a re-identified alias."""
    g = ProvenanceGraph()
    g.add_node(_node("asset_a1", NodeType.ASSET, group="group_same"))
    g.add_node(_node("asset_a2", NodeType.ASSET, group="group_same"))  # alias of same person
    g.add_node(_node("deriv_a2", NodeType.DERIVED, parents=["asset_a2"]))
    plan = plan_withdrawal(g, "group_same", T2)
    assert {"asset_a1", "asset_a2", "deriv_a2"} <= set(plan.affected_assets)
    assert set(plan.seed_ids) == {"asset_a1", "asset_a2"}


def test_withdrawal_suspends_registry_claims_by_supporting_result():
    g = _lineage_graph()
    registry = ClaimQuarantineRegistry([
        Claim(
            claim_id="claim_reg1",
            exact_wording="bounded improvement on result_x",
            claim_class=ClaimClass.BOUNDED_PERFORMANCE,
            status=ClaimStatus.CANDIDATE,
            supporting_results=("result_x",),
        ),
        Claim(
            claim_id="claim_reg_unrelated",
            exact_wording="unrelated",
            claim_class=ClaimClass.ENGINEERING,
            status=ClaimStatus.CANDIDATE,
            supporting_results=("result_y",),
        ),
    ])
    plan = plan_withdrawal(g, "asset_x", T2, claim_registry=registry)
    assert "claim_reg1" in plan.affected_claims
    assert "claim_reg_unrelated" not in plan.affected_claims

    suspended = suspend_affected_claims(registry, plan)
    assert "claim_reg1" in suspended
    assert registry.get("claim_reg1").quarantined is True
    assert registry.get("claim_reg1").render_status() is ClaimStatus.SUSPENDED
    # unrelated claim untouched
    assert registry.get("claim_reg_unrelated").quarantined is False


def test_withdrawal_plan_is_deterministic():
    g = _lineage_graph()
    p1 = plan_withdrawal(g, "asset_x", T2).to_dict()
    p2 = plan_withdrawal(g, "asset_x", T2).to_dict()
    assert p1 == p2


# --------------------------------------------------------------------------
# consent store: append-only, redaction, security posture
# --------------------------------------------------------------------------

def test_consent_store_withdrawal_is_append_only():
    store = InMemoryConsentStore([
        _grant("g1", "asset_a", [Purpose.INTERNAL_ANALYSIS], RightsPermission.ALLOWED,
               consent_ref="opaque-handle-123"),
    ])
    withdrawn = store.record_withdrawal("asset_a", at_time=T2, reason="artist request")
    assert len(withdrawn) == 1
    assert withdrawn[0].status is GrantStatus.WITHDRAWN
    # history retains both the original and the withdrawn record
    assert len(store.history()) == 2
    # after withdrawal, authorization fails closed
    assert authorize(store, None, "asset_a", Purpose.INTERNAL_ANALYSIS, T2).authorized is False


def test_shareable_grant_redacts_consent_handle_and_owner():
    store = InMemoryConsentStore([
        _grant("g1", "asset_a", [Purpose.INTERNAL_ANALYSIS], RightsPermission.ALLOWED,
               consent_ref="opaque-handle-123", owner="alice"),
    ])
    shared = store.shareable_grants()[0]
    assert shared["consent_ref"] is None
    assert shared["owner"] == "redacted"
    # subject/purpose/permission remain (pseudonymous graph is still useful)
    assert shared["subject_id"] == "asset_a"


def test_duplicate_grant_id_rejected():
    with pytest.raises(ValueError):
        InMemoryConsentStore([
            _grant("dup", "asset_a", [Purpose.INTERNAL_ANALYSIS], RightsPermission.ALLOWED),
            _grant("dup", "asset_b", [Purpose.INTERNAL_ANALYSIS], RightsPermission.ALLOWED),
        ])


def test_grant_roundtrip_serialization():
    g = _grant("g1", "asset_a", [Purpose.LISTENING_STUDY, Purpose.RETENTION],
               RightsPermission.CONDITIONAL, conditions=("loudness_matched",),
               expires_at=T2, consent_ref="h1")
    back = RightsGrant.from_dict(g.to_dict())
    assert back == g


# --------------------------------------------------------------------------
# the graph built for these fixtures is itself provenance-valid
# --------------------------------------------------------------------------

def test_fixture_lineage_has_no_dangling_parent_edges():
    """Withdrawal traversal relies on every parent pointer resolving inside the
    graph. (Ancestor-completeness is a separate DT-46 concern and intentionally
    not asserted here — the withdrawal fixtures use partial lineage.)"""
    g = _lineage_graph()
    report = g.validate()
    dangling = [e for e in report.errors if "not present in graph" in e.message]
    assert dangling == []
