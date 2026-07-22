"""Product-promise discovery framework (DT-53, autonomous portion).

DT-53's *decision* (which user, which job, what promise, what launch boundary)
is a human-only ``product_scope`` gate, and participant contact is human-only
too. This package builds only the **autonomous framework** the contract's
Field 15 marks *Automatic*: a structured schema for (pseudonymized) discovery
records, candidate promises with explicit falsifiers, and validators for
research-record completeness, consent/retention state, and contradiction
retention.

Nothing here contacts a participant or decides scope. It runs on **synthetic
example records** so the machinery is proven before any real interview, and so a
human can drop real consented records into the same shape and get the same
checks.
"""

from src.product_discovery.promises import CandidatePromise, JobStep, PromiseOutcome
from src.product_discovery.records import ResearchConsentState, ResearchNote
from src.product_discovery.validate import (
    DiscoveryIssue,
    audit_contradictions,
    check_promise_falsifiers,
    usable_notes,
    validate_note,
)

__all__ = [
    "CandidatePromise",
    "JobStep",
    "PromiseOutcome",
    "ResearchConsentState",
    "ResearchNote",
    "DiscoveryIssue",
    "audit_contradictions",
    "check_promise_falsifiers",
    "usable_notes",
    "validate_note",
]
