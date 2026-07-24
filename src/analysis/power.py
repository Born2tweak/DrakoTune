"""Synthetic power / sample-size simulation harness (DT-57).

Monte-Carlo power for the clustered, tie-aware analysis. Deterministic (seeded).
This COMPUTES power as a function of design inputs; it does NOT choose the final
sample size — that needs pilot variance (Field 8, out of scope) and human-set
alpha/power/margin. Between-listener heterogeneity is modelled with a Beta
concentration (``kappa``): low kappa = high heterogeneity (large clusters effect).

CI runs a reduced deterministic fixture (small ``n_sims``/``n_boot``).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.analysis.model import ListenerSummary, analyze, evaluate
from src.analysis.prereg import Direction


@dataclass(frozen=True)
class SimConfig:
    n_listeners: int
    items_per_listener: int
    true_pref: float          # true mean processed-preference among decisive
    kappa: float = 20.0       # Beta concentration; lower = more between-listener spread
    tie_rate: float = 0.15
    artifact_rate: float = 0.05


def simulate_summaries(cfg: SimConfig, rng: np.random.Generator) -> list[ListenerSummary]:
    """Draw one clustered, tie-aware synthetic dataset as listener summaries."""
    a = max(cfg.true_pref * cfg.kappa, 1e-6)
    b = max((1 - cfg.true_pref) * cfg.kappa, 1e-6)
    per_listener_rate = rng.beta(a, b, size=cfg.n_listeners)
    summaries = []
    for i in range(cfg.n_listeners):
        processed = original = ties = artifacts = 0
        for _ in range(cfg.items_per_listener):
            u = rng.random()
            if u < cfg.tie_rate:
                ties += 1
            elif u < cfg.tie_rate + cfg.artifact_rate:
                artifacts += 1
            elif rng.random() < per_listener_rate[i]:
                processed += 1
            else:
                original += 1
        summaries.append(ListenerSummary(
            f"L{i}", processed + original, processed, ties, artifacts, 0,
        ))
    return summaries


def estimate_power(
    cfg: SimConfig, direction: Direction, threshold: float,
    n_sims: int = 300, n_boot: int = 400, seed: int = 7, ci: float = 0.95,
) -> float:
    """Fraction of simulated studies that reject H0 at the given human threshold."""
    rng = np.random.default_rng(seed)
    rejects = 0
    for _ in range(n_sims):
        summaries = simulate_summaries(cfg, rng)
        result = analyze(summaries, n_boot=n_boot, seed=int(rng.integers(1, 2**31)), ci=ci)
        if evaluate(result, direction, threshold, ci_bound="lower").outcome == "reject_null":
            rejects += 1
    return rejects / n_sims


def power_curve(
    n_listener_values: list[int], base: SimConfig, direction: Direction,
    threshold: float, **kw,
) -> list[tuple[int, float]]:
    """Power vs number of listeners (holding other design inputs fixed)."""
    out = []
    for n in n_listener_values:
        cfg = SimConfig(
            n, base.items_per_listener, base.true_pref, base.kappa,
            base.tie_rate, base.artifact_rate,
        )
        out.append((n, estimate_power(cfg, direction, threshold, **kw)))
    return out


def type_one_error(
    cfg_null: SimConfig, direction: Direction, threshold: float, **kw,
) -> float:
    """Calibration check: power under a null configuration should stay near/below alpha."""
    return estimate_power(cfg_null, direction, threshold, **kw)
