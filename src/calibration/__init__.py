"""Calibration: measure detector accuracy on labeled synthetic signals."""

from src.calibration.harness import (
    CALIBRATION_VERSION,
    ISSUES,
    build_samples,
    calibrate,
    detect_issues,
)

__all__ = ["calibrate", "build_samples", "detect_issues", "ISSUES", "CALIBRATION_VERSION"]
