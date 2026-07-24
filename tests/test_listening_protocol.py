"""DT-56 — listening protocol & immutable response schema (autonomous portion).

Field 14 (schema, uniqueness, tie, correction, idempotency) and Field 16
adversarial exploits (one-listener/eight-rows, unanimous ties, split panels,
all-A clicks, forged IDs, repeated import). Synthetic data only. The five audit
exploits N-002..N-006 must be rejected or honestly surfaced.
"""
from __future__ import annotations

import pytest

from src.listening import (
    Assignment,
    Panel,
    Protocol,
    Response,
    ResponseOutcome,
    ResolvedPreference,
    Side,
    Treatment,
    Trial,
    active_responses,
    apply_correction,
    assignment_balance,
    duplicate_rows,
    import_legacy,
    independent_listener_count,
    panel_breakdown,
    panels_disagree,
    preference_summary,
    resolve_preference,
    side_choice_diagnostic,
    validate_response,
)

PROTO = Protocol("p1", "1.0.0", trials=(Trial("t1", "clip1"), Trial("t2", "clip2")))


def _asn(trial, listener, processed_side=Side.B, first=Side.A) -> Assignment:
    other = Side.A if processed_side is Side.B else Side.B
    return Assignment(
        trial, listener,
        {processed_side: Treatment.PROCESSED, other: Treatment.ORIGINAL},
        first_played=first,
    )


def _resp(trial, listener, outcome, panel=Panel.TARGET_USER, **kw) -> Response:
    return Response(trial, listener, panel, outcome, **kw)


# --- schema invariants ---

def test_assignment_must_cover_both_treatments():
    with pytest.raises(ValueError):
        Assignment("t1", "l1", {Side.A: Treatment.PROCESSED, Side.B: Treatment.PROCESSED}, Side.A)


def test_listener_id_required():
    with pytest.raises(ValueError):
        from src.listening import ListenerRef
        ListenerRef("  ")


# --- N-002: one listener's eight rows is not n=8 ---

def test_duplicate_rows_do_not_inflate_sample():
    rows = [_resp("t1", "l1", ResponseOutcome.PREFER_B) for _ in range(8)]
    assert independent_listener_count(rows) == 1
    assert len(active_responses(rows)) == 1
    assert len(duplicate_rows(rows)) == 7


def test_eight_distinct_listeners_is_eight():
    rows = [_resp("t1", f"l{i}", ResponseOutcome.PREFER_B) for i in range(8)]
    assert independent_listener_count(rows) == 8


# --- N-003: original-preference is a visible harm signal, not "not processed" ---

def test_original_preference_is_explicit_not_collapsed():
    # processed on B; everyone prefers A (the original) -> harm signal.
    rows = [_resp("t1", f"l{i}", ResponseOutcome.PREFER_A) for i in range(8)]
    asn = {("t1", f"l{i}"): _asn("t1", f"l{i}", processed_side=Side.B) for i in range(8)}
    summary = preference_summary(rows, asn)
    assert summary["prefer_original"] == 8
    assert summary["prefer_processed"] == 0
    # "processed not preferred" must not read as a clean pass:
    assert summary["prefer_original"] > 0


# --- N-004: ties are explicit and never dropped ---

def test_ties_are_counted():
    rows = [_resp("t1", f"l{i}", ResponseOutcome.TIE_NO_DIFFERENCE) for i in range(5)]
    asn = {("t1", f"l{i}"): _asn("t1", f"l{i}") for i in range(5)}
    summary = preference_summary(rows, asn)
    assert summary["tie"] == 5


# --- N-005: panels are not pooled ---

def test_panels_reported_separately_and_disagreement_flagged():
    rows = []
    asn = {}
    for i in range(4):  # experts prefer original (A)
        rows.append(_resp("t1", f"e{i}", ResponseOutcome.PREFER_A, panel=Panel.EXPERT_ENGINEER))
        asn[("t1", f"e{i}")] = _asn("t1", f"e{i}", processed_side=Side.B)
    for i in range(4):  # users prefer processed (B)
        rows.append(_resp("t2", f"u{i}", ResponseOutcome.PREFER_B, panel=Panel.TARGET_USER))
        asn[("t2", f"u{i}")] = _asn("t2", f"u{i}", processed_side=Side.B)
    breakdown = panel_breakdown(rows, asn)
    assert set(breakdown) == {"expert_engineer", "target_user"}
    assert panels_disagree(breakdown) is True


# --- N-006: side/order bias surfaced; treatment resolved only via assignment ---

def test_all_A_clicks_flagged_as_degenerate():
    rows = [_resp("t1", f"l{i}", ResponseOutcome.PREFER_A) for i in range(6)]
    diag = side_choice_diagnostic(rows)
    assert diag["degenerate_side_bias"] is True


def test_preference_needs_assignment_no_treatment_leak():
    r = _resp("t1", "l1", ResponseOutcome.PREFER_A)
    # same A/B click resolves to opposite treatments under opposite assignments
    assert resolve_preference(r, _asn("t1", "l1", processed_side=Side.A)) is ResolvedPreference.PREFER_PROCESSED
    assert resolve_preference(r, _asn("t1", "l1", processed_side=Side.B)) is ResolvedPreference.PREFER_ORIGINAL


def test_missing_assignment_is_not_counted():
    rows = [_resp("t1", "l1", ResponseOutcome.PREFER_A)]
    summary = preference_summary(rows, {})  # no assignment
    assert summary["unresolved_missing_assignment"] == 1
    assert summary["prefer_processed"] == 0


def test_assignment_balance_reports_imbalance():
    asns = [_asn("t1", f"l{i}", processed_side=Side.A) for i in range(6)]  # all processed on A
    bal = assignment_balance(asns)
    assert bal["balanced"] is False and bal["processed_on_a"] == 6


# --- append-only corrections ---

def test_correction_appends_superseding_revision():
    rows = [_resp("t1", "l1", ResponseOutcome.PREFER_A)]
    corrected = apply_correction(rows, "t1", "l1", ResponseOutcome.PREFER_B, timestamp="t")
    assert len(corrected) == 2                      # original retained
    active = active_responses(corrected)
    assert len(active) == 1 and active[0].outcome is ResponseOutcome.PREFER_B
    assert active[0].revision == 1 and active[0].supersedes_revision == 0


def test_correcting_unknown_response_fails():
    with pytest.raises(ValueError):
        apply_correction([], "t1", "l1", ResponseOutcome.PREFER_B)


# --- forged IDs + legacy import idempotency ---

def test_forged_ids_rejected():
    bad = _resp("t_forged", "l_forged", ResponseOutcome.PREFER_A)
    issues = validate_response(bad, PROTO, frozenset({"l1"}))
    assert len(issues) == 2  # unknown trial + unknown listener


def test_legacy_import_rejects_forged_and_is_idempotent():
    rows = [
        {"trial_id": "t1", "listener_id": "l1", "outcome": "prefer_b", "panel": "target_user"},
        {"trial_id": "t_x", "listener_id": "l1", "outcome": "prefer_b"},  # forged trial
    ]
    imported, rejected = import_legacy(rows, PROTO, frozenset({"l1"}))
    assert len(imported) == 1 and imported[0].quarantined is True
    assert len(rejected) == 1
    # re-import with existing -> idempotent, nothing added
    again, _ = import_legacy(rows, PROTO, frozenset({"l1"}), existing=imported)
    assert again == []


def test_legacy_import_is_quarantined_and_excluded_from_active():
    rows = [{"trial_id": "t1", "listener_id": "l1", "outcome": "prefer_b", "panel": "target_user"}]
    imported, _ = import_legacy(rows, PROTO, frozenset({"l1"}))
    # quarantined legacy rows never enter the active/independent count
    assert independent_listener_count(imported) == 0
