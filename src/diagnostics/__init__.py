"""Layered diagnostics: deterministic measurements emitted as Observations.

Each analyzer measures a family of technical properties and returns canonical
DiagnosticResults. Diagnostics never interpret or act — interpretation and
decisions belong to later layers (M06 refactor, M07/M08 decision engine).
"""

from src.diagnostics.loudness import (
    LOUDNESS_ANALYZER_VERSION,
    diagnose_loudness,
    measure_loudness,
)
from src.diagnostics.safety import (
    SAFETY_ANALYZER_VERSION,
    diagnose_safety,
    measure_safety,
)
from src.diagnostics.spectral import (
    SPECTRAL_ANALYZER_VERSION,
    diagnose_spectral,
    interpret_spectral,
    measure_spectral,
)

__all__ = [
    "measure_safety",
    "diagnose_safety",
    "SAFETY_ANALYZER_VERSION",
    "measure_loudness",
    "diagnose_loudness",
    "LOUDNESS_ANALYZER_VERSION",
    "measure_spectral",
    "interpret_spectral",
    "diagnose_spectral",
    "SPECTRAL_ANALYZER_VERSION",
]
