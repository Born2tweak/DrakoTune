"""Layered diagnostics: deterministic measurements emitted as Observations.

Each analyzer measures a family of technical properties and returns canonical
DiagnosticResults. Diagnostics never interpret or act — interpretation and
decisions belong to later layers (M06 refactor, M07/M08 decision engine).
"""

from src.diagnostics.safety import (
    SAFETY_ANALYZER_VERSION,
    diagnose_safety,
    measure_safety,
)

__all__ = ["measure_safety", "diagnose_safety", "SAFETY_ANALYZER_VERSION"]
