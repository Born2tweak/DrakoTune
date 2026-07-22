"""DT-53 — Product-promise discovery framework (autonomous portion).

Covers Field 14 (research-record completeness, consent/retention validation,
decision/falsifier-link checks) and Field 16 adversarial cases (confirmation-
biased sample, accompaniment required, users misread "automatic", privacy
rejection, engineer/creator conflict). No participant is contacted and no scope
decision is made — synthetic records only.
"""

from src.product_discovery import (
    CandidatePromise,
    PromiseOutcome,
    ResearchConsentState,
    ResearchNote,
    audit_contradictions,
    check_promise_falsifiers,
    usable_notes,
    validate_note,
)

NOW = "2026-07-21T00:00:00Z"
FUTURE = "2026-12-31T00:00:00Z"
PAST = "2026-01-01T00:00:00Z"


def _note(nid, consent, **kw):
    base = dict(
        note_id=nid,
        participant_pseudonym=f"P-{nid}",
        consent_state=consent,
        recorded_at=NOW,
        retention_until=FUTURE,
        deletion_path=True,
        primary_job="clean up a rap vocal take",
        pain_points=("harsh_sibilance",),
    )
    base.update(kw)
    return ResearchNote(**base)


# -- completeness + consent/retention --------------------------------------

def test_complete_consented_note_has_no_issues():
    assert validate_note(_note("n1", ResearchConsentState.GRANTED), at_time=NOW) == ()


def test_missing_required_field_flagged():
    issues = validate_note(_note("n1", ResearchConsentState.GRANTED, primary_job=""), at_time=NOW)
    assert any(i.code == "incomplete" for i in issues)


def test_note_without_signals_is_incomplete():
    issues = validate_note(
        _note("n1", ResearchConsentState.GRANTED, pain_points=(), observed_behaviors=()),
        at_time=NOW,
    )
    assert any("pain_points or observed_behaviors" in i.message for i in issues)


def test_privacy_rejection_note_is_unusable():
    """Adversarial: a refused record is never used in synthesis."""
    refused = _note("n1", ResearchConsentState.REFUSED)
    issues = validate_note(refused, at_time=NOW)
    assert any(i.code == "consent_not_usable" for i in issues)
    assert usable_notes([refused], at_time=NOW) == ()


def test_withdrawn_and_pending_are_unusable():
    notes = [
        _note("g", ResearchConsentState.GRANTED),
        _note("w", ResearchConsentState.WITHDRAWN),
        _note("p", ResearchConsentState.PENDING),
    ]
    usable = usable_notes(notes, at_time=NOW)
    assert {n.note_id for n in usable} == {"g"}


def test_missing_deletion_path_or_retention_flagged():
    n = _note("n1", ResearchConsentState.GRANTED, deletion_path=False, retention_until=None)
    codes = {i.code for i in validate_note(n, at_time=NOW)}
    assert {"no_deletion_path", "no_retention"} <= codes


def test_retention_expired_note_excluded():
    n = _note("n1", ResearchConsentState.GRANTED, retention_until=PAST)
    assert any(i.code == "retention_expired" for i in validate_note(n, at_time=NOW))
    assert usable_notes([n], at_time=NOW) == ()


# -- contradiction audit ---------------------------------------------------

def test_engineer_creator_conflict_is_retained():
    """Adversarial: opposing views are surfaced, not dropped."""
    engineer = _note("eng", ResearchConsentState.GRANTED,
                     observed_behaviors=("wants_manual_control",), contradicts=("creator",))
    creator = _note("creator", ResearchConsentState.GRANTED,
                    observed_behaviors=("wants_automatic",))
    pairs = audit_contradictions([engineer, creator])
    assert pairs == (("creator", "eng"),)


def test_contradiction_dedup_and_ignores_dangling():
    a = _note("a", ResearchConsentState.GRANTED, contradicts=("b", "ghost"))
    b = _note("b", ResearchConsentState.GRANTED, contradicts=("a",))
    pairs = audit_contradictions([a, b])
    assert pairs == (("a", "b"),)  # symmetric edge de-duped; "ghost" ignored


# -- promise falsifiers ----------------------------------------------------

def _promise(**kw):
    base = dict(
        promise_id="pr1",
        statement="Automatically clean a single dry rap vocal.",
        target_user="bedroom rap artist",
        job="clean up a vocal take",
        in_scope=("single_dry_vocal",),
        out_of_scope=("full_mix", "accompaniment"),
        falsifiers=("accompaniment_required", "misread_automatic"),
        support_signals=("wants_automatic",),
    )
    base.update(kw)
    return CandidatePromise(**base)


def test_promise_requires_a_falsifier():
    import pytest
    with pytest.raises(ValueError):
        _promise(falsifiers=())


def test_promise_supported_when_signal_present_and_no_falsifier():
    notes = [_note("n1", ResearchConsentState.GRANTED,
                   observed_behaviors=("wants_automatic",))]
    assert check_promise_falsifiers(_promise(), notes, at_time=NOW) is PromiseOutcome.SUPPORTED


def test_accompaniment_required_falsifies_single_vocal_promise():
    """Adversarial: a user who needs accompaniment refutes the single-vocal promise."""
    notes = [_note("n1", ResearchConsentState.GRANTED,
                   pain_points=("accompaniment_required",))]
    assert check_promise_falsifiers(_promise(), notes, at_time=NOW) is PromiseOutcome.FALSIFIED


def test_misread_automatic_falsifies_promise():
    """Adversarial: users misreading 'automatic' is a falsifier, not noise."""
    notes = [_note("n1", ResearchConsentState.GRANTED,
                   observed_behaviors=("wants_automatic", "misread_automatic"))]
    assert check_promise_falsifiers(_promise(), notes, at_time=NOW) is PromiseOutcome.FALSIFIED


def test_falsifier_in_unusable_note_does_not_count():
    """A falsifier only counts from a usable (consented) record — fail closed the other way too."""
    notes = [_note("n1", ResearchConsentState.REFUSED,
                   pain_points=("accompaniment_required",))]
    # refused note is excluded, so no falsifier and no support => insufficient
    assert check_promise_falsifiers(_promise(), notes, at_time=NOW) is PromiseOutcome.INSUFFICIENT


def test_confirmation_biased_sample_cannot_hide_dissent():
    """Adversarial: even if most notes support, a single falsifier flips the outcome."""
    notes = [
        _note("s1", ResearchConsentState.GRANTED, observed_behaviors=("wants_automatic",)),
        _note("s2", ResearchConsentState.GRANTED, observed_behaviors=("wants_automatic",)),
        _note("dissent", ResearchConsentState.GRANTED, pain_points=("accompaniment_required",)),
    ]
    assert check_promise_falsifiers(_promise(), notes, at_time=NOW) is PromiseOutcome.FALSIFIED


def test_insufficient_when_neither_support_nor_falsifier():
    notes = [_note("n1", ResearchConsentState.GRANTED, pain_points=("unrelated_thing",))]
    assert check_promise_falsifiers(_promise(), notes, at_time=NOW) is PromiseOutcome.INSUFFICIENT
