"""Identity-safe, exploit-resistant listening protocol & responses (DT-56).

Supersedes the legacy M24/M43 CSV listening records. Builds only the schema +
integrity layer the contract marks *Automatic* (Field 15); consent/privacy terms
and opening the protocol to real participants remain human-only. Statistical
thresholds and confirmatory execution are out of scope (DT-57+). Runs on synthetic
stimuli/responses.
"""
from src.listening.integrity import (
    ResolvedPreference,
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
from src.listening.schema import (
    Assignment,
    ListenerRef,
    Panel,
    Protocol,
    Response,
    ResponseOutcome,
    Side,
    Treatment,
    Trial,
)

__all__ = [
    "ResolvedPreference",
    "active_responses",
    "apply_correction",
    "assignment_balance",
    "duplicate_rows",
    "import_legacy",
    "independent_listener_count",
    "panel_breakdown",
    "panels_disagree",
    "preference_summary",
    "resolve_preference",
    "side_choice_diagnostic",
    "validate_response",
    "Assignment",
    "ListenerRef",
    "Panel",
    "Protocol",
    "Response",
    "ResponseOutcome",
    "Side",
    "Treatment",
    "Trial",
]
