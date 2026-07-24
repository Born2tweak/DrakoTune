"""End-to-end pilot dry-run on mock data (DT-58, autonomous portion).

Wires the whole listening workflow — screener -> blinded balanced assignment ->
response capture -> DT-57 clustered analysis — on synthetic participants. Proves the
pipeline runs and honestly shows that a 2-3 person pilot is exploratory/underpowered
(wide CI), which is exactly why the pilot is non-confirmatory (Field 21). No human is
contacted (Field 22).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.analysis import analyze, listener_summaries
from src.analysis.model import AnalysisResult
from src.listening import (
    Assignment,
    Panel,
    Protocol,
    Response,
    ResponseOutcome,
    Side,
    Treatment,
    Trial,
    assignment_balance,
    side_choice_diagnostic,
)
from src.pilot.criteria import Role, ScreenerResponse, qualify


def build_pilot_protocol(n_trials: int) -> Protocol:
    trials = tuple(Trial(f"pt{i}", f"clip{i}") for i in range(n_trials))
    return Protocol("pilot-dryrun", "1.0.0", trials=trials, panels=(Panel.EXPERT_ENGINEER,))


def balanced_assignments(
    protocol: Protocol, listener_ids: list[str],
) -> dict[tuple[str, str], Assignment]:
    """Counterbalance processed side + play order across trials×listeners."""
    out: dict[tuple[str, str], Assignment] = {}
    for li, lid in enumerate(listener_ids):
        for ti, trial in enumerate(protocol.trials):
            processed = Side.A if (li + ti) % 2 == 0 else Side.B
            other = Side.B if processed is Side.A else Side.A
            first = Side.A if ti % 2 == 0 else Side.B
            out[(trial.trial_id, lid)] = Assignment(
                trial.trial_id, lid,
                {processed: Treatment.PROCESSED, other: Treatment.ORIGINAL}, first,
            )
    return out


def simulate_responses(
    assignments: dict[tuple[str, str], Assignment], true_pref: float,
    tie_rate: float = 0.15, seed: int = 3,
) -> list[Response]:
    """Synthetic responses consistent with each blinded assignment + a true preference."""
    rng = np.random.default_rng(seed)
    responses = []
    for (trial_id, lid), asn in assignments.items():
        if rng.random() < tie_rate:
            outcome = ResponseOutcome.TIE_NO_DIFFERENCE
        else:
            prefers_processed = rng.random() < true_pref
            processed_side = asn.processed_side()
            if prefers_processed:
                outcome = ResponseOutcome.PREFER_A if processed_side is Side.A else ResponseOutcome.PREFER_B
            else:
                outcome = ResponseOutcome.PREFER_B if processed_side is Side.A else ResponseOutcome.PREFER_A
        responses.append(Response(trial_id, lid, Panel.EXPERT_ENGINEER, outcome))
    return responses


@dataclass(frozen=True)
class DryRunReport:
    n_screened: int
    n_qualified: int
    n_responses: int
    analysis: AnalysisResult
    side_balanced: bool
    no_degenerate_side_bias: bool
    workflow_ok: bool
    note: str


def dry_run(
    candidates: list[ScreenerResponse], n_trials: int = 12, true_pref: float = 0.7,
) -> DryRunReport:
    """Screen -> assign -> respond -> analyze, entirely on mock data."""
    quals = [qualify(c, Role.EXPERT_ENGINEER) for c in candidates]
    qualified = [q.candidate_id for q in quals if q.qualified]
    protocol = build_pilot_protocol(n_trials)
    assignments = balanced_assignments(protocol, qualified)
    responses = simulate_responses(assignments, true_pref)
    summaries = listener_summaries(responses, assignments)
    result = analyze(summaries, n_boot=400)
    bal = assignment_balance(list(assignments.values()))
    diag = side_choice_diagnostic(responses)
    workflow_ok = len(responses) == len(assignments) and (
        result.convergence.value in ("converged", "indeterminate")
    )
    return DryRunReport(
        n_screened=len(candidates), n_qualified=len(qualified), n_responses=len(responses),
        analysis=result, side_balanced=bool(bal["balanced"]),
        no_degenerate_side_bias=not diag["degenerate_side_bias"], workflow_ok=workflow_ok,
        note="2-3 engineer pilot is exploratory: wide CI expected; non-confirmatory (Field 21).",
    )
