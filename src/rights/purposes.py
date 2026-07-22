"""Purpose taxonomy for rights authorization (DT-49).

Rights are *purpose-specific*: a grant that permits internal synthetic
evaluation does not permit public distribution. ``authorize`` always takes an
explicit :class:`Purpose`; there is no wildcard "any purpose" authorization,
because an unstated purpose must fail closed rather than inherit permission.
"""

from enum import Enum


class Purpose(str, Enum):
    """The controlled vocabulary of uses an asset can be authorized for.

    Ordered loosely from least to most externally consequential. Each grant
    lists exactly the purposes it covers; a purpose not listed is treated as
    ``unknown`` (fail closed), never as implicitly allowed.
    """

    INTERNAL_ANALYSIS = "internal_analysis"          # inspect/measure locally
    SYNTHETIC_EVALUATION = "synthetic_evaluation"    # use in a synthetic eval corpus
    METRIC_CALIBRATION = "metric_calibration"        # calibrate a metric registry card
    LISTENING_STUDY = "listening_study"              # present to human listeners
    MODEL_TRAINING = "model_training"                # train/fit a model
    PUBLIC_EXAMPLE = "public_example"                # show publicly as an example
    DISTRIBUTION = "distribution"                    # bundle/ship the asset
    RETENTION = "retention"                          # store beyond the active task


# Purposes whose authorization has external, hard-to-reverse consequences. These
# never receive an implied grant and are the ones most sensitive to withdrawal.
EXTERNAL_PURPOSES = frozenset(
    {
        Purpose.LISTENING_STUDY,
        Purpose.PUBLIC_EXAMPLE,
        Purpose.DISTRIBUTION,
        Purpose.MODEL_TRAINING,
    }
)
