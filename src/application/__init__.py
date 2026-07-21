"""Application service seam (DT-52).

Typed Analyze/Plan/Render/Evaluate commands over a license-aware ``DspBackend``
contract. Behavior-preserving facade over the v2 pipeline; the DSP library is
swappable and never imported by the UI/service layer directly.
"""

from src.application.backend import (
    BackendCapabilities,
    BackendUnavailable,
    DspBackend,
    PedalboardBackend,
    UnavailableBackend,
    default_backend,
)
from src.application.commands import (
    AnalyzeResult,
    BuildIdentity,
    EvaluateResult,
    RenderResult,
)
from src.application.service import ApplicationService

__all__ = [
    "ApplicationService",
    "DspBackend",
    "BackendCapabilities",
    "PedalboardBackend",
    "UnavailableBackend",
    "BackendUnavailable",
    "default_backend",
    "AnalyzeResult",
    "RenderResult",
    "EvaluateResult",
    "BuildIdentity",
]
