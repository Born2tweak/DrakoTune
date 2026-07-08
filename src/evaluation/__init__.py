"""Evaluation: before/after comparison of processed audio.

Compares targeted, loudness-invariant metrics; never claims subjective quality.
"""

from src.evaluation.evaluate import (
    EVALUATION_VERSION,
    evaluate,
    evaluate_arrays,
)

__all__ = ["evaluate", "evaluate_arrays", "EVALUATION_VERSION"]
