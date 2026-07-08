"""Audio ingestion: preflight validation before analysis or processing."""

from src.ingestion.preflight import (
    PREFLIGHT_VERSION,
    PreflightError,
    PreflightReport,
    ensure_processable,
    preflight,
)

__all__ = [
    "PreflightReport",
    "PreflightError",
    "preflight",
    "ensure_processable",
    "PREFLIGHT_VERSION",
]
