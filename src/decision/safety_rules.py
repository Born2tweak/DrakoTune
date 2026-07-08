"""Decision engine v1 — deterministic safety rules (M07).

Consumes a preflight report and the technical-safety DiagnosticResult (M03/M04)
and produces a SafetyDecision. These are hard gates evaluated before any
adaptive enhancement is considered:

  1. Invalid preflight        -> stop processing entirely.
  2. Severe clipping          -> block enhancement (only mitigation is allowed).
  3. Low headroom             -> block positive gain.
  4. Mild clipping / DC offset -> warn, do not block.

Rules are deterministic and explainable; every ruling is recorded with its
evidence. This layer does NOT build a DSP chain (that is M08/M09).
"""

from src.decision.records import (
    OUTCOME_ALLOW,
    OUTCOME_BLOCK,
    OUTCOME_WARN,
    TARGET_ENHANCEMENT,
    TARGET_POSITIVE_GAIN,
    TARGET_PROCESSING,
    DecisionRecord,
    SafetyDecision,
)
from src.shared_types import DiagnosticResult

# --- Named policy thresholds (versioned via DECISION_POLICY_VERSION) ---
SEVERE_CLIP_RATIO = 0.02   # at/above this, enhancement is blocked
MILD_CLIP_RATIO = 0.001    # between mild and severe -> warn only
HEADROOM_MIN_DB = 1.0      # below this true-peak headroom, block positive gain


def _metric(safety: DiagnosticResult, name: str, default: float) -> float:
    for o in safety.observations:
        if o.metric == name:
            return o.value
    return default


def evaluate_safety(preflight_report, safety: DiagnosticResult) -> SafetyDecision:
    """Return a deterministic SafetyDecision from preflight + safety diagnostics."""
    records: list[DecisionRecord] = []
    warnings: list[str] = []
    blocked: list[str] = []

    processing_allowed = True
    enhancement_allowed = True
    positive_gain_allowed = True

    # Rule 1 — preflight gate.
    if preflight_report is not None and not preflight_report.passed:
        processing_allowed = False
        enhancement_allowed = False
        positive_gain_allowed = False
        blocked.extend([TARGET_PROCESSING, TARGET_ENHANCEMENT, TARGET_POSITIVE_GAIN])
        records.append(DecisionRecord(
            rule="preflight_invalid",
            outcome=OUTCOME_BLOCK,
            target=TARGET_PROCESSING,
            reason="Preflight blocked the input; no processing.",
            evidence=tuple(getattr(preflight_report, "blockers", ()) or ()),
        ))
        return SafetyDecision(
            processing_allowed=False,
            enhancement_allowed=False,
            positive_gain_allowed=False,
            blocked_targets=tuple(dict.fromkeys(blocked)),
            warnings=tuple(warnings),
            records=tuple(records),
        )

    records.append(DecisionRecord(
        rule="preflight_ok", outcome=OUTCOME_ALLOW, target=TARGET_PROCESSING,
        reason="Preflight passed.", evidence=(),
    ))

    clip_ratio = _metric(safety, "clipping_ratio", 0.0)
    headroom_db = _metric(safety, "headroom_db", 99.0)

    # Rule 2 — clipping gate.
    if clip_ratio >= SEVERE_CLIP_RATIO:
        enhancement_allowed = False
        blocked.append(TARGET_ENHANCEMENT)
        records.append(DecisionRecord(
            rule="severe_clipping",
            outcome=OUTCOME_BLOCK,
            target=TARGET_ENHANCEMENT,
            reason=f"Severe clipping ({clip_ratio:.2%}); only mitigation is safe, "
                   "enhancement blocked. Re-recording recommended.",
            evidence=("safety.clipping_ratio", "clipping"),
        ))
    else:
        if clip_ratio >= MILD_CLIP_RATIO:
            warnings.append("mild_clipping")
            records.append(DecisionRecord(
                rule="mild_clipping", outcome=OUTCOME_WARN, target=TARGET_ENHANCEMENT,
                reason=f"Mild clipping ({clip_ratio:.2%}); proceed with caution.",
                evidence=("safety.clipping_ratio",),
            ))
        records.append(DecisionRecord(
            rule="enhancement_allowed", outcome=OUTCOME_ALLOW, target=TARGET_ENHANCEMENT,
            reason="No severe clipping; enhancement permitted.", evidence=(),
        ))

    # Rule 3 — headroom gate for positive gain.
    if headroom_db < HEADROOM_MIN_DB:
        positive_gain_allowed = False
        blocked.append(TARGET_POSITIVE_GAIN)
        records.append(DecisionRecord(
            rule="low_headroom",
            outcome=OUTCOME_BLOCK,
            target=TARGET_POSITIVE_GAIN,
            reason=f"Only {headroom_db:.1f} dB headroom; positive gain blocked "
                   "to protect against overs.",
            evidence=("safety.headroom_db",),
        ))
    else:
        records.append(DecisionRecord(
            rule="headroom_ok", outcome=OUTCOME_ALLOW, target=TARGET_POSITIVE_GAIN,
            reason=f"{headroom_db:.1f} dB headroom; positive gain permitted.", evidence=(),
        ))

    # Rule 4 — DC offset is advisory only.
    if "dc_offset" in safety.integrity_flags:
        warnings.append("dc_offset")
        records.append(DecisionRecord(
            rule="dc_offset", outcome=OUTCOME_WARN, target=TARGET_PROCESSING,
            reason="DC offset present; consider a DC-blocking high-pass.",
            evidence=("dc_offset",),
        ))

    return SafetyDecision(
        processing_allowed=processing_allowed,
        enhancement_allowed=enhancement_allowed,
        positive_gain_allowed=positive_gain_allowed,
        blocked_targets=tuple(dict.fromkeys(blocked)),
        warnings=tuple(warnings),
        records=tuple(records),
    )
