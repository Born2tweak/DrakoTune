"""Discovery-record validators (DT-53 Field 14, Automatic).

Three automatic checks the contract calls for:

- **record completeness + consent/retention validation** (:func:`validate_note`,
  :func:`usable_notes`) — a record is usable only if consent is ``granted``, it
  is within retention, and it has a deletion path. Everything else fails closed
  and is excluded from synthesis (privacy rejection is honored, not overridden).
- **contradiction audit** (:func:`audit_contradictions`) — contradictory records
  are *retained and surfaced*, never dropped, so a confirmation-biased synthesis
  cannot hide dissent (Field 13 "contradictory evidence retained").
- **promise falsifier check** (:func:`check_promise_falsifiers`) — tests each
  candidate promise's falsifiers against the usable record set and returns an
  explicit outcome, so no promise is accepted while a falsifier is observed.

None of this makes the scope decision; it prepares an honest, testable basis for
the human who does.
"""

from dataclasses import dataclass

from src.product_discovery.promises import CandidatePromise, PromiseOutcome
from src.product_discovery.records import (
    USABLE_CONSENT_STATES,
    ResearchNote,
)


@dataclass(frozen=True)
class DiscoveryIssue:
    """One structured problem with a discovery record."""

    note_id: str
    code: str
    message: str


_REQUIRED_NONEMPTY = ("participant_pseudonym", "recorded_at", "primary_job")


def validate_note(note: ResearchNote, *, at_time: str) -> tuple[DiscoveryIssue, ...]:
    """Return completeness + consent/retention issues for one record."""
    issues: list[DiscoveryIssue] = []

    for f in _REQUIRED_NONEMPTY:
        if not getattr(note, f):
            issues.append(DiscoveryIssue(note.note_id, "incomplete", f"missing {f}"))

    if not note.pain_points and not note.observed_behaviors:
        issues.append(
            DiscoveryIssue(note.note_id, "incomplete", "no pain_points or observed_behaviors")
        )

    if note.consent_state not in USABLE_CONSENT_STATES:
        issues.append(
            DiscoveryIssue(
                note.note_id,
                "consent_not_usable",
                f"consent_state={note.consent_state.value} (usable requires granted)",
            )
        )
    if not note.deletion_path:
        issues.append(
            DiscoveryIssue(note.note_id, "no_deletion_path", "record lacks a deletion path")
        )
    if note.retention_until is None:
        issues.append(
            DiscoveryIssue(note.note_id, "no_retention", "record lacks a retention deadline")
        )
    elif not note.is_within_retention(at_time):
        issues.append(
            DiscoveryIssue(note.note_id, "retention_expired", "record past its retention deadline")
        )

    return tuple(issues)


def usable_notes(notes: list[ResearchNote], *, at_time: str) -> tuple[ResearchNote, ...]:
    """Only records that are complete, consented, and within retention.

    Fails closed: any record with issues is excluded (a refused/withdrawn record
    is never used, honoring a privacy rejection).
    """
    return tuple(n for n in notes if not validate_note(n, at_time=at_time))


def audit_contradictions(
    notes: list[ResearchNote],
) -> tuple[tuple[str, str], ...]:
    """Return every retained contradiction pair ``(a, b)`` among the records.

    Symmetric edges are de-duplicated. This makes dissent explicit; it never
    resolves or discards a contradiction.
    """
    by_id = {n.note_id: n for n in notes}
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for n in notes:
        for other in n.contradicts:
            if other not in by_id:
                continue
            pair = tuple(sorted((n.note_id, other)))
            if pair not in seen:
                seen.add(pair)  # type: ignore[arg-type]
                out.append(pair)  # type: ignore[arg-type]
    return tuple(out)


def check_promise_falsifiers(
    promise: CandidatePromise, notes: list[ResearchNote], *, at_time: str
) -> PromiseOutcome:
    """Test a promise against the *usable* record set.

    - If any usable record exhibits a falsifier token → ``FALSIFIED``.
    - Else if any usable record exhibits a support signal → ``SUPPORTED``.
    - Else → ``INSUFFICIENT`` (retain the narrow current spec).
    """
    usable = usable_notes(notes, at_time=at_time)
    falsifiers = set(promise.falsifiers)
    supports = set(promise.support_signals)

    observed_falsifier = False
    observed_support = False
    for n in usable:
        tokens = set(n.pain_points) | set(n.observed_behaviors)
        if tokens & falsifiers:
            observed_falsifier = True
        if tokens & supports:
            observed_support = True

    if observed_falsifier:
        return PromiseOutcome.FALSIFIED
    if observed_support:
        return PromiseOutcome.SUPPORTED
    return PromiseOutcome.INSUFFICIENT
