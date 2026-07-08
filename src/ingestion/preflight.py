"""Preflight validation (M03).

Validate audio before diagnostics or DSP. Corrupt, too-short, silent, or
undecodable input must not move blindly through the pipeline. Preflight is
read-only — it never modifies the original audio.

A PreflightReport separates hard **blockers** (processing must stop) from
**warnings** (proceed with caution). Thresholds are named policy constants, not
magic numbers, and are versioned via PREFLIGHT_VERSION so behavior can be pinned.
"""

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

PREFLIGHT_VERSION = "1.0.0"

# --- Policy thresholds (documented; change deliberately and bump the version) ---
MIN_DURATION_SECONDS = 0.25  # shorter than this is not a usable vocal take
SILENCE_PEAK = 1e-3          # peak amplitude at/below this reads as silence
SEVERE_CLIP_RATIO = 0.02     # >=2% full-scale samples => warn (re-record advised)
MAX_DURATION_SECONDS = 1800  # 30 min: warn on unusually long input


@dataclass(frozen=True)
class PreflightReport:
    """Outcome of validating one audio file before processing."""

    path: str
    passed: bool
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    metrics: dict = field(default_factory=dict)
    preflight_version: str = PREFLIGHT_VERSION

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "passed": self.passed,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "metrics": dict(self.metrics),
            "preflight_version": self.preflight_version,
        }

    def explain(self) -> str:
        """Human-readable summary for CLI / report use."""
        status = "PASSED" if self.passed else "BLOCKED"
        lines = [f"Preflight {status}: {Path(self.path).name}"]
        for b in self.blockers:
            lines.append(f"  BLOCKER: {b}")
        for w in self.warnings:
            lines.append(f"  warning: {w}")
        return "\n".join(lines)


class PreflightError(RuntimeError):
    """Raised when a blocked file is processed with enforcement on."""

    def __init__(self, report: PreflightReport):
        self.report = report
        super().__init__(report.explain())


def preflight(audio_path: str | Path) -> PreflightReport:
    """Validate an audio file. Returns a report; never raises on bad audio."""
    path = Path(audio_path)
    if not path.exists():
        return PreflightReport(str(path), passed=False, blockers=("file_not_found",))

    # Decode. soundfile raises for corrupt/unsupported containers.
    try:
        audio, sample_rate = sf.read(str(path), dtype="float32")
    except Exception as exc:  # noqa: BLE001 - report any decode failure uniformly
        return PreflightReport(
            str(path),
            passed=False,
            blockers=("decode_failed",),
            metrics={"decode_error": type(exc).__name__},
        )

    channels = 1 if audio.ndim == 1 else audio.shape[1]
    total_samples = audio.shape[0]
    duration = total_samples / sample_rate if sample_rate else 0.0
    peak = float(np.max(np.abs(audio))) if total_samples else 0.0

    blockers: list[str] = []
    warnings: list[str] = []

    if total_samples == 0:
        blockers.append("empty_audio")
    if duration < MIN_DURATION_SECONDS:
        blockers.append("too_short")
    if peak <= SILENCE_PEAK:
        blockers.append("silent_or_near_silent")

    if duration > MAX_DURATION_SECONDS:
        warnings.append("unusually_long")
    if total_samples:
        clip_ratio = float(np.mean(np.abs(audio) >= 0.999))
        if clip_ratio >= SEVERE_CLIP_RATIO:
            warnings.append("severe_clipping")
    else:
        clip_ratio = 0.0

    metrics = {
        "sample_rate": int(sample_rate),
        "channels": int(channels),
        "duration_seconds": float(duration),
        "peak": peak,
        "clip_ratio": clip_ratio,
        "total_samples": int(total_samples),
    }

    return PreflightReport(
        str(path),
        passed=not blockers,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        metrics=metrics,
    )


def ensure_processable(audio_path: str | Path, enforce: bool = True) -> PreflightReport:
    """Run preflight and, when enforcing, raise PreflightError on any blocker.

    `enforce=False` is the documented rollback path: the report is still
    produced (and can be surfaced) but blockers do not stop processing.
    """
    report = preflight(audio_path)
    if enforce and not report.passed:
        raise PreflightError(report)
    return report
