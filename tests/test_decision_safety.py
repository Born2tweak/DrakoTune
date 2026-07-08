"""Decision engine v1 — safety rule tests (M07).

Pins the deterministic safety gates: severe clipping blocks enhancement, low
headroom blocks positive gain, invalid preflight stops processing, and every
decision explains applied and blocked actions.
"""

import json

import numpy as np

from src.decision import (
    DECISION_POLICY_VERSION,
    SEVERE_CLIP_RATIO,
    evaluate_safety,
)
from src.diagnostics import measure_safety
from src.diagnostics.safety import SAFETY_ANALYZER_VERSION
from src.ingestion import PreflightReport
from src.shared_types import DiagnosticResult

SR = 44100


def _safety_result(sig: np.ndarray) -> DiagnosticResult:
    obs, flags, ctx = measure_safety(sig, SR)
    return DiagnosticResult(
        id="t", audio_asset_id="t", analyzer_version=SAFETY_ANALYZER_VERSION,
        measurement_context=ctx, observations=tuple(obs), integrity_flags=tuple(flags),
    )


def _sine(freq: float, amp: float, seconds: float = 1.0) -> np.ndarray:
    t = np.linspace(0, seconds, int(SR * seconds), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def _passing_preflight() -> PreflightReport:
    return PreflightReport(path="t", passed=True)


class TestClippingGate:
    def test_severe_clipping_blocks_enhancement(self):
        clipped = np.clip(_sine(440, 2.0), -1.0, 1.0)  # ~50% full-scale
        decision = evaluate_safety(_passing_preflight(), _safety_result(clipped))
        assert decision.enhancement_allowed is False
        assert "enhancement" in decision.blocked_targets
        rec = next(r for r in decision.records if r.rule == "severe_clipping")
        assert rec.outcome == "block" and rec.evidence

    def test_mild_clipping_warns_not_blocks(self):
        sig = _sine(440, 0.5)
        n = sig.size
        sig[: int(n * 0.005)] = 1.0  # ~0.5% full-scale -> mild
        decision = evaluate_safety(_passing_preflight(), _safety_result(sig))
        clip_ratio = next(
            o.value for o in _safety_result(sig).observations if o.metric == "clipping_ratio"
        )
        assert 0.001 <= clip_ratio < SEVERE_CLIP_RATIO
        assert decision.enhancement_allowed is True
        assert "mild_clipping" in decision.warnings

    def test_clean_allows_enhancement(self):
        decision = evaluate_safety(_passing_preflight(), _safety_result(_sine(300, 0.5)))
        assert decision.enhancement_allowed is True


class TestHeadroomGate:
    def test_low_headroom_blocks_positive_gain(self):
        hot = _sine(300, 0.995)  # peak ~0.995 -> <1 dB headroom, no clipping
        decision = evaluate_safety(_passing_preflight(), _safety_result(hot))
        assert decision.positive_gain_allowed is False
        assert "positive_gain" in decision.blocked_targets
        # Enhancement not blocked by headroom alone.
        assert decision.enhancement_allowed is True

    def test_normal_headroom_allows_gain(self):
        decision = evaluate_safety(_passing_preflight(), _safety_result(_sine(300, 0.4)))
        assert decision.positive_gain_allowed is True


class TestPreflightGate:
    def test_invalid_preflight_stops_processing(self):
        blocked_preflight = PreflightReport(
            path="t", passed=False, blockers=("silent_or_near_silent",)
        )
        decision = evaluate_safety(blocked_preflight, _safety_result(_sine(300, 0.4)))
        assert decision.processing_allowed is False
        assert decision.enhancement_allowed is False
        assert decision.positive_gain_allowed is False
        rec = next(r for r in decision.records if r.rule == "preflight_invalid")
        assert rec.outcome == "block"


class TestExplainAndContract:
    def test_explain_lists_block_and_allow(self):
        clipped = np.clip(_sine(440, 2.0), -1.0, 1.0)
        text = evaluate_safety(_passing_preflight(), _safety_result(clipped)).explain()
        assert "BLOCK" in text and "enhancement" in text

    def test_records_cover_applied_and_blocked(self):
        decision = evaluate_safety(_passing_preflight(), _safety_result(_sine(300, 0.4)))
        outcomes = {r.outcome for r in decision.records}
        assert "allow" in outcomes  # applied/allowed actions are recorded too

    def test_policy_version_and_serialization(self):
        decision = evaluate_safety(_passing_preflight(), _safety_result(_sine(300, 0.4)))
        assert decision.policy_version == DECISION_POLICY_VERSION
        json.dumps(decision.to_dict())  # must not raise

    def test_deterministic(self):
        sig = np.clip(_sine(440, 2.0), -1.0, 1.0)
        a = evaluate_safety(_passing_preflight(), _safety_result(sig)).to_dict()
        b = evaluate_safety(_passing_preflight(), _safety_result(sig)).to_dict()
        assert a == b
