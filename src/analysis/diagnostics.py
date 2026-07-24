"""Analysis diagnostics (DT-57 Field 14/16).

Surfaces degenerate designs so they resolve to indeterminate rather than a
spurious pass: perfect separation, single decisive cluster, dominant tie/artifact
mass, and outcome-correlated dropout.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.analysis.model import ListenerSummary


@dataclass(frozen=True)
class Diagnostics:
    perfect_separation: bool
    single_decisive_cluster: bool
    high_tie_mass: bool
    high_artifact_mass: bool
    dropout_correlated_with_outcome: bool

    @property
    def any_flag(self) -> bool:
        return any([
            self.perfect_separation, self.single_decisive_cluster,
            self.high_tie_mass, self.high_artifact_mass,
            self.dropout_correlated_with_outcome,
        ])


def diagnose(
    summaries: list[ListenerSummary], tie_artifact_warn: float = 0.5,
    dropout_by_group: dict[str, tuple[int, int]] | None = None,
) -> Diagnostics:
    """Compute design diagnostics.

    ``dropout_by_group`` maps a group label -> (n_completed, n_dropped); a large
    spread in dropout rate across groups flags outcome-correlated missingness.
    """
    decisive = [s for s in summaries if s.decisive > 0]
    props = [s.proportion_processed for s in decisive]
    total = sum(s.decisive + s.ties + s.artifacts + s.cannot_tell for s in summaries)
    ties = sum(s.ties for s in summaries)
    artifacts = sum(s.artifacts for s in summaries)

    perfect_sep = len(props) > 0 and all(p in (0.0, 1.0) for p in props)
    single = len(decisive) < 2
    high_tie = total > 0 and ties / total > tie_artifact_warn
    high_art = total > 0 and artifacts / total > tie_artifact_warn

    dropout_flag = False
    if dropout_by_group:
        rates = []
        for _, (done, dropped) in dropout_by_group.items():
            n = done + dropped
            if n > 0:
                rates.append(dropped / n)
        if len(rates) >= 2 and (max(rates) - min(rates)) > 0.25:
            dropout_flag = True

    return Diagnostics(perfect_sep, single, high_tie, high_art, dropout_flag)
