"""Clustered, tie-aware preference analysis (DT-57).

The estimand is defined at the **listener** unit, not the response row (N-002): the
statistic is the mean of per-listener processed-preference proportions among that
listener's *decisive* responses, and uncertainty comes from a **cluster bootstrap
over listeners**. Ties, artifacts, and cannot-tell are separate reported masses,
never dropped (N-003, N-004) and never treated as preferences.

Failure modes yield ``INDETERMINATE`` — never a naive binomial fallback (Field 19):
fewer than two decisive clusters, zero decisive responses, or a degenerate resample.
Thresholds/alpha are supplied by the frozen preregistration; this module never
invents them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from src.analysis.prereg import Direction
from src.listening.integrity import (
    ResolvedPreference,
    active_responses,
    resolve_preference,
)
from src.listening.schema import Assignment, Response

MIN_DECISIVE_CLUSTERS = 2


class Convergence(str, Enum):
    CONVERGED = "converged"
    INDETERMINATE = "indeterminate"   # degenerate; no fallback (Field 19)


@dataclass(frozen=True)
class ListenerSummary:
    listener_id: str
    decisive: int          # prefer_processed + prefer_original
    processed: int
    ties: int
    artifacts: int
    cannot_tell: int

    @property
    def proportion_processed(self) -> float | None:
        return self.processed / self.decisive if self.decisive > 0 else None


@dataclass(frozen=True)
class AnalysisResult:
    convergence: Convergence
    n_listeners: int
    n_decisive_listeners: int
    n_responses: int
    point_estimate: float | None            # mean per-listener processed-preference
    ci_low: float | None
    ci_high: float | None
    tie_mass: int = 0
    artifact_mass: int = 0
    cannot_tell_mass: int = 0
    note: str = ""


def listener_summaries(
    responses: list[Response], assignments: dict[tuple[str, str], Assignment]
) -> list[ListenerSummary]:
    """Per-listener decisive/tie/artifact counts from active responses."""
    buckets: dict[str, dict[str, int]] = {}
    for r in active_responses(responses):
        asn = assignments.get(r.response_key)
        if asn is None:
            continue  # unresolved responses are not counted (fail closed)
        pref = resolve_preference(r, asn)
        b = buckets.setdefault(
            r.listener_id,
            {"processed": 0, "original": 0, "ties": 0, "artifacts": 0, "cannot_tell": 0},
        )
        if pref is ResolvedPreference.PREFER_PROCESSED:
            b["processed"] += 1
        elif pref is ResolvedPreference.PREFER_ORIGINAL:
            b["original"] += 1
        elif pref is ResolvedPreference.TIE:
            b["ties"] += 1
        elif pref is ResolvedPreference.ARTIFACTS:
            b["artifacts"] += 1
        else:
            b["cannot_tell"] += 1
    return [
        ListenerSummary(
            lid, b["processed"] + b["original"], b["processed"],
            b["ties"], b["artifacts"], b["cannot_tell"],
        )
        for lid, b in sorted(buckets.items())
    ]


def analyze(
    summaries: list[ListenerSummary], n_boot: int = 2000, seed: int = 12345,
    ci: float = 0.95,
) -> AnalysisResult:
    """Cluster-bootstrap the listener-weighted processed-preference proportion."""
    decisive = [s for s in summaries if s.decisive > 0]
    tie_mass = sum(s.ties for s in summaries)
    artifact_mass = sum(s.artifacts for s in summaries)
    cannot = sum(s.cannot_tell for s in summaries)
    n_resp = sum(s.decisive + s.ties + s.artifacts + s.cannot_tell for s in summaries)

    if len(decisive) < MIN_DECISIVE_CLUSTERS:
        return AnalysisResult(
            Convergence.INDETERMINATE, len(summaries), len(decisive), n_resp,
            None, None, None, tie_mass, artifact_mass, cannot,
            note=f"only {len(decisive)} decisive listener(s); need >= {MIN_DECISIVE_CLUSTERS} (no naive fallback)",
        )

    props = np.array([s.proportion_processed for s in decisive], dtype=float)
    point = float(np.mean(props))

    rng = np.random.default_rng(seed)
    idx = np.arange(len(props))
    boot_means = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        sample = rng.choice(idx, size=len(idx), replace=True)  # resample LISTENERS
        boot_means[i] = float(np.mean(props[sample]))
    lo = float(np.quantile(boot_means, (1 - ci) / 2))
    hi = float(np.quantile(boot_means, 1 - (1 - ci) / 2))
    return AnalysisResult(
        Convergence.CONVERGED, len(summaries), len(decisive), n_resp,
        point, lo, hi, tie_mass, artifact_mass, cannot,
    )


@dataclass(frozen=True)
class Decision:
    outcome: str          # "reject_null" | "fail_to_reject" | "indeterminate"
    detail: str


def evaluate(
    result: AnalysisResult, direction: Direction, threshold: float, ci_bound: str,
) -> Decision:
    """Apply a HUMAN-SUPPLIED threshold to a result. Never invents the threshold.

    superiority: reject H0 iff the CI lower bound exceeds ``threshold`` (e.g. 0.5+margin).
    non_inferiority (do-no-harm): reject H0 (harm) iff the CI lower bound stays at/above
    ``threshold`` (e.g. 0.5-margin) — processed is not worse than original by more than the margin.
    """
    if result.convergence is Convergence.INDETERMINATE or result.ci_low is None:
        return Decision("indeterminate", result.note or "analysis did not converge")
    if direction is Direction.SUPERIORITY:
        ok = result.ci_low > threshold
        return Decision(
            "reject_null" if ok else "fail_to_reject",
            f"CI[{result.ci_low:.3f},{result.ci_high:.3f}] vs superiority threshold {threshold}",
        )
    # non-inferiority: the lower bound must not fall below the harm margin.
    ok = result.ci_low >= threshold
    return Decision(
        "reject_null" if ok else "fail_to_reject",
        f"CI lower {result.ci_low:.3f} vs non-inferiority margin {threshold}",
    )
