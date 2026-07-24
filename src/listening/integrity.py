"""Integrity operations over listening responses (DT-56 Field 14/16).

Every function fails closed and encodes an audit lesson structurally:

- ``active_responses`` / ``independent_listener_count`` — one active response per
  (trial, listener); the sample unit is the listener, never the row (N-002).
- ``resolve_preference`` / ``preference_summary`` — original-preference and ties
  are explicit categories, never collapsed into "not processed" (N-003, N-004).
- ``panel_breakdown`` — panels are reported separately, never pooled (N-005).
- ``side_choice_diagnostic`` / ``assignment_balance`` — degenerate side/order
  patterns are surfaced (N-006).
- ``apply_correction`` — corrections append a superseding revision, never mutate.
- ``import_legacy`` — forged/unknown IDs are rejected; imports are idempotent and
  land quarantined (legacy stays exploratory, Field 19).
"""
from __future__ import annotations

from dataclasses import replace
from enum import Enum

from src.listening.schema import (
    Assignment,
    Panel,
    Protocol,
    Response,
    ResponseOutcome,
    Side,
    Treatment,
)


class ResolvedPreference(str, Enum):
    PREFER_PROCESSED = "prefer_processed"
    PREFER_ORIGINAL = "prefer_original"   # N-003: a harm signal, kept visible
    TIE = "tie"                            # N-004
    ARTIFACTS = "artifacts"
    CANNOT_TELL = "cannot_tell"


def active_responses(responses: list[Response]) -> list[Response]:
    """Highest non-quarantined revision per (trial, listener). One active per key."""
    latest: dict[tuple[str, str], Response] = {}
    for r in responses:
        if r.quarantined:
            continue
        cur = latest.get(r.response_key)
        if cur is None or r.revision > cur.revision:
            latest[r.response_key] = r
    return list(latest.values())


def duplicate_rows(responses: list[Response]) -> list[Response]:
    """Every non-quarantined row that is not the single active row for its key.

    These extras must never inflate the sample count (N-002). Uses object identity
    so that byte-identical duplicate rows (same key and revision) are each caught.
    """
    active_ids = {id(r) for r in active_responses(responses)}
    active_keys = {r.response_key for r in active_responses(responses)}
    return [
        r for r in responses
        if not r.quarantined and id(r) not in active_ids and r.response_key in active_keys
    ]


def independent_listener_count(responses: list[Response]) -> int:
    """Independent sample size = distinct listeners among active responses (N-002)."""
    return len({r.listener_id for r in active_responses(responses)})


def resolve_preference(response: Response, assignment: Assignment) -> ResolvedPreference:
    """Map a blinded A/B outcome to a treatment preference via the assignment.

    Raw responses never name a treatment; only the (separately stored) assignment
    resolves them — so a leaked/forced side cannot masquerade as a preference (N-006).
    """
    if response.perceived_artifacts or response.outcome is ResponseOutcome.BOTH_ARTIFACTS:
        return ResolvedPreference.ARTIFACTS
    if response.outcome is ResponseOutcome.TIE_NO_DIFFERENCE:
        return ResolvedPreference.TIE
    if response.outcome is ResponseOutcome.CANNOT_TELL:
        return ResolvedPreference.CANNOT_TELL
    chosen_side = Side.A if response.outcome is ResponseOutcome.PREFER_A else Side.B
    treatment = assignment.treatment_of(chosen_side)
    return (
        ResolvedPreference.PREFER_PROCESSED
        if treatment is Treatment.PROCESSED
        else ResolvedPreference.PREFER_ORIGINAL
    )


def preference_summary(
    responses: list[Response], assignments: dict[tuple[str, str], Assignment]
) -> dict[str, int]:
    """Explicit counts across every ResolvedPreference category.

    original-preference and ties are separate keys, so "processed not preferred"
    can never be mistaken for "no harm" (N-003) and ties never vanish (N-004).
    Missing assignment => the response is not counted (fails closed).
    """
    counts = {p.value: 0 for p in ResolvedPreference}
    counts["unresolved_missing_assignment"] = 0
    for r in active_responses(responses):
        asn = assignments.get(r.response_key)
        if asn is None:
            counts["unresolved_missing_assignment"] += 1
            continue
        counts[resolve_preference(r, asn).value] += 1
    return counts


def panel_breakdown(
    responses: list[Response], assignments: dict[tuple[str, str], Assignment]
) -> dict[str, dict[str, int]]:
    """Per-panel summaries; panels are NEVER pooled (N-005)."""
    by_panel: dict[Panel, list[Response]] = {}
    for r in active_responses(responses):
        by_panel.setdefault(r.panel, []).append(r)
    return {
        panel.value: preference_summary(rs, assignments)
        for panel, rs in by_panel.items()
    }


def panels_disagree(breakdown: dict[str, dict[str, int]]) -> bool:
    """True if any panel leans processed while another leans original (N-005)."""
    directions = set()
    for summary in breakdown.values():
        p, o = summary["prefer_processed"], summary["prefer_original"]
        if p > o:
            directions.add("processed")
        elif o > p:
            directions.add("original")
    return {"processed", "original"} <= directions


def side_choice_diagnostic(responses: list[Response]) -> dict[str, object]:
    """Detect degenerate side patterns (e.g. everyone clicked A) (N-006)."""
    a = sum(1 for r in active_responses(responses)
            if r.outcome is ResponseOutcome.PREFER_A)
    b = sum(1 for r in active_responses(responses)
            if r.outcome is ResponseOutcome.PREFER_B)
    decisive = a + b
    return {
        "prefer_a": a, "prefer_b": b,
        "degenerate_side_bias": decisive > 0 and (a == 0 or b == 0),
    }


def assignment_balance(assignments: list[Assignment]) -> dict[str, object]:
    """Balance of processed-side and play order across assignments (N-006)."""
    n = len(assignments)
    processed_on_a = sum(1 for a in assignments if a.processed_side() is Side.A)
    first_a = sum(1 for a in assignments if a.first_played is Side.A)
    return {
        "n": n,
        "processed_on_a": processed_on_a,
        "processed_on_b": n - processed_on_a,
        "first_played_a": first_a,
        "balanced": n == 0 or (0 < processed_on_a < n),
    }


def apply_correction(
    responses: list[Response], trial_id: str, listener_id: str,
    new_outcome: ResponseOutcome, timestamp: str = "", **fields: object
) -> list[Response]:
    """Append-only correction: supersede the active response with a new revision."""
    current = next(
        (r for r in active_responses(responses)
         if r.response_key == (trial_id, listener_id)), None
    )
    if current is None:
        raise ValueError(f"no active response for {(trial_id, listener_id)} to correct")
    corrected = replace(
        current, outcome=new_outcome, timestamp=timestamp,
        revision=current.revision + 1, supersedes_revision=current.revision, **fields,
    )
    return [*responses, corrected]


def validate_response(
    response: Response, protocol: Protocol, known_listeners: frozenset[str]
) -> list[str]:
    """Fail-closed validation: forged trial or listener IDs are rejected (N: forged IDs)."""
    issues = []
    if response.trial_id not in protocol.trial_ids():
        issues.append(f"unknown trial_id '{response.trial_id}' (forged or stale)")
    if response.listener_id not in known_listeners:
        issues.append(f"unknown listener_id '{response.listener_id}' (forged)")
    return issues


def import_legacy(
    rows: list[dict], protocol: Protocol, known_listeners: frozenset[str],
    existing: list[Response] | None = None,
) -> tuple[list[Response], list[dict]]:
    """Import legacy M24 rows as quarantined (exploratory) responses.

    Rejects forged/unknown IDs. Idempotent: a row whose key is already present is
    skipped, so repeated import never double-counts.
    """
    existing = existing or []
    seen = {(r.trial_id, r.listener_id) for r in existing if r.source == "legacy_import"}
    imported: list[Response] = []
    rejected: list[dict] = []
    for row in rows:
        tid, lid = row.get("trial_id", ""), row.get("listener_id", "")
        if tid not in protocol.trial_ids() or lid not in known_listeners:
            rejected.append({**row, "reason": "forged/unknown id"})
            continue
        if (tid, lid) in seen:
            continue  # idempotent
        seen.add((tid, lid))
        try:
            outcome = ResponseOutcome(row.get("outcome", ""))
        except ValueError:
            rejected.append({**row, "reason": "unknown outcome"})
            continue
        imported.append(Response(
            trial_id=tid, listener_id=lid,
            panel=Panel(row.get("panel", "unknown")) if row.get("panel") in
            {p.value for p in Panel} else Panel.UNKNOWN,
            outcome=outcome, source="legacy_import", quarantined=True,
            quarantine_reason="legacy M24 import — exploratory only (Field 19)",
        ))
    return imported, rejected
