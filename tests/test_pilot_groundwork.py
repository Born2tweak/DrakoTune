"""DT-58 — expert-pilot recruitment/budget groundwork (autonomous portion).

Field 14 (packet/screener/fair-rate/qualification checks) and Field 16 adversarial
(unqualified profile, accessibility need, no-show/withdrawal). No outreach, no
enrollment, no spend. Distinct from the legacy tests/test_pilot.py (M16).
"""
from __future__ import annotations

from dataclasses import replace

from src.listening import active_responses
from src.pilot import (
    FairRate,
    PilotBudget,
    Role,
    ScreenerResponse,
    balanced_assignments,
    build_pilot_protocol,
    dry_run,
    qualify,
    simulate_responses,
)


def _good(cid="c1", **kw) -> ScreenerResponse:
    base = dict(candidate_id=cid, years_mixing_experience=6.0, target_genre_familiar=True,
                calibrated_monitoring=True, passed_audio_check=True)
    base.update(kw)
    return ScreenerResponse(**base)


# --- screener / qualification ---

def test_qualified_expert_passes():
    q = qualify(_good())
    assert q.qualified and q.reasons == ()


def test_unqualified_profile_rejected_with_reasons():
    q = qualify(_good(years_mixing_experience=1.0, calibrated_monitoring=False))
    assert not q.qualified
    assert any("experience" in r for r in q.reasons)
    assert any("monitoring" in r for r in q.reasons)


def test_accessibility_need_is_accommodation_not_disqualifier():
    q = qualify(_good(accessibility_needs=("screen_reader",)))
    assert q.qualified is True
    assert q.accommodations_required == ("screen_reader",)


def test_failed_audio_check_disqualifies():
    assert qualify(_good(passed_audio_check=False)).qualified is False


# --- fair rate / budget: always needs authorization, never sets base rate ---

def test_fair_rate_applies_professional_premium():
    rate = FairRate(base_hourly=30.0, professional_premium=1.5)
    assert rate.hourly() == 45.0
    assert rate.per_participant(task_hours=2.0) == 90.0


def test_budget_requires_human_authorization_and_adds_fees():
    budget = PilotBudget(n_participants=3, task_hours=2.0, rate=FairRate(30.0, 1.5))
    s = budget.summary()
    assert s["requires_human_authorization"] is True
    assert s["total_with_fees_contingency"] > s["participant_cost"]


# --- end-to-end dry run on mock data ---

def test_dry_run_end_to_end_workflow_ok():
    candidates = [_good(f"c{i}", years_mixing_experience=5.0) for i in range(3)]
    report = dry_run(candidates, n_trials=12, true_pref=0.75)
    assert report.n_qualified == 3
    assert report.n_responses == 36                  # 3 listeners x 12 trials
    assert report.workflow_ok is True
    assert report.side_balanced and report.no_degenerate_side_bias


def test_dry_run_screens_out_unqualified():
    candidates = [_good("ok", years_mixing_experience=5.0),
                  _good("bad", years_mixing_experience=0.5)]
    report = dry_run(candidates)
    assert report.n_screened == 2 and report.n_qualified == 1


def test_tiny_pilot_is_exploratory_not_confirmatory():
    candidates = [_good("a", years_mixing_experience=5.0), _good("b", years_mixing_experience=5.0)]
    report = dry_run(candidates, n_trials=10, true_pref=0.7)
    assert "exploratory" in report.note


# --- withdrawal / response quality (Field 16: no-show / withdrawal) ---

def test_participant_withdrawal_quarantines_their_responses():
    protocol = build_pilot_protocol(4)
    asn = balanced_assignments(protocol, ["a", "b"])
    responses = simulate_responses(asn, true_pref=0.8)
    withdrawn = [replace(r, quarantined=True, quarantine_reason="withdrew")
                 if r.listener_id == "b" else r for r in responses]
    remaining = active_responses(withdrawn)
    assert all(r.listener_id == "a" for r in remaining)
