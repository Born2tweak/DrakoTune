"""Schema, analyzer, and policy versions for DrakoTune canonical records.

Version fields let diagnostics, decisions, and reports be compared across runs
and pinned by regression fixtures. Bump the relevant constant whenever the
*meaning* of a record changes, not merely its wording.

Per the DrakoTune Bible: "Version metrics, thresholds, processing policies, and
reports." These constants are the single source of truth for those versions.
"""

from enum import Enum

# Shape of the canonical records in this package.
SCHEMA_VERSION = "1.0.0"

# Behavior of the diagnostic engine (src/dsp/diagnose.py). Matches Alpha 2.2.
ANALYZER_VERSION = "0.2.2"

# Decision-engine policy version. No decision engine exists yet (arrives in
# M07/M08); "0.0.0" marks "no policy applied".
POLICY_VERSION = "0.0.0"


class ConfidenceBand(str, Enum):
    """Automation band derived from a 0..1 confidence.

    The Bible law "Confidence controls automation":
      HIGH   -> apply or strongly recommend a bounded adjustment.
      MEDIUM -> apply only conservative adjustment / auditionable option.
      LOW    -> report observation only; do not auto-process.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Documented policy thresholds (not magic numbers): the boundaries that map a
# raw confidence to an automation band. Change deliberately and bump
# POLICY_VERSION when the decision engine begins consuming these.
CONFIDENCE_HIGH_MIN = 0.66
CONFIDENCE_MEDIUM_MIN = 0.33


def band_from_confidence(confidence: float) -> ConfidenceBand:
    """Map a 0..1 confidence to an automation band."""
    if confidence >= CONFIDENCE_HIGH_MIN:
        return ConfidenceBand.HIGH
    if confidence >= CONFIDENCE_MEDIUM_MIN:
        return ConfidenceBand.MEDIUM
    return ConfidenceBand.LOW
