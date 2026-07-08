"""Report engine: user- and agent-readable explanations of a processing run."""

from src.reports.report_engine import (
    REPORT_ENGINE_VERSION,
    build_report,
    render_markdown,
)

__all__ = ["build_report", "render_markdown", "REPORT_ENGINE_VERSION"]
