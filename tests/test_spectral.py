"""Spectral/noise diagnostics tests (M06).

Verifies the observation/interpretation separation, that single metrics do not
produce strong claims, versioned band definitions, and issue detection on
synthetic and fixture signals.
"""

import numpy as np
import pytest

from fixtures.loader import AUDIO_DIR
from src.diagnostics import diagnose_spectral, interpret_spectral, measure_spectral
from src.diagnostics.spectral import SINGLE_METRIC_CAP, SPECTRAL_ANALYZER_VERSION
from src.shared_types import Interpretation, Observation

SR = 44100


def _tone(components: dict[float, float], seconds: float = 1.0) -> np.ndarray:
    t = np.linspace(0, seconds, int(SR * seconds), endpoint=False)
    sig = np.zeros_like(t)
    for freq, amp in components.items():
        sig += amp * np.sin(2 * np.pi * freq * t)
    return sig.astype(np.float32)


def _issues(interpretations) -> set[str]:
    return {i.issue for i in interpretations}


class TestSeparation:
    def test_measure_returns_only_observations(self):
        obs, _ = measure_spectral(_tone({200: 0.4, 3500: 0.3}), SR)
        assert obs and all(isinstance(o, Observation) for o in obs)

    def test_interpretations_are_interpretation_type_without_actions(self):
        obs, _ = measure_spectral(_tone({200: 0.1, 3500: 0.5}), SR)
        interps = interpret_spectral(obs)
        assert all(isinstance(i, Interpretation) for i in interps)
        # Structural proof of separation: Interpretation has no action/recommendation.
        assert not hasattr(Interpretation, "recommendation")
        assert not any(hasattr(i, "processor") for i in interps)

    def test_supporting_ids_reference_real_observations(self):
        obs, _ = measure_spectral(_tone({200: 0.1, 3500: 0.5}), SR)
        obs_ids = {o.id for o in obs}
        for interp in interpret_spectral(obs):
            for oid in interp.supporting_observation_ids:
                assert oid in obs_ids


class TestSingleMetricRule:
    def test_single_supporting_observation_is_capped(self):
        # Sweep several signals; any interpretation backed by ONE observation
        # must stay within the MEDIUM ceiling.
        for comps in ({40: 0.6, 1000: 0.1}, {200: 0.1, 6500: 0.6}, {300: 0.6, 1500: 0.05}):
            obs, _ = measure_spectral(_tone(comps), SR)
            for interp in interpret_spectral(obs):
                if len(interp.supporting_observation_ids) == 1:
                    assert interp.confidence <= SINGLE_METRIC_CAP + 1e-9


class TestDetection:
    def test_harsh_fixture_flags_harshness(self):
        _, interps = diagnose_spectral(str(AUDIO_DIR / "harsh.wav"), asset_id="h")
        assert "harshness" in _issues(interps)

    def test_muddy_fixture_flags_muddiness(self):
        _, interps = diagnose_spectral(str(AUDIO_DIR / "muddy.wav"), asset_id="m")
        assert "muddiness" in _issues(interps)

    def test_sibilance_detected(self):
        obs, _ = measure_spectral(_tone({200: 0.1, 6500: 0.6}), SR)
        assert "sibilance" in _issues(interpret_spectral(obs))

    def test_rumble_detected(self):
        obs, _ = measure_spectral(_tone({40: 0.6, 1000: 0.1}), SR)
        assert "rumble" in _issues(interpret_spectral(obs))


class TestContractAndDeterminism:
    def test_bands_versioned_in_context(self):
        result, _ = diagnose_spectral(str(AUDIO_DIR / "clean_tone.wav"), asset_id="c")
        ctx = result.measurement_context
        assert ctx["analyzer_version"] == SPECTRAL_ANALYZER_VERSION
        assert "bands_hz" in ctx and "harshness" in ctx["bands_hz"]
        assert ctx["single_metric_cap"] == SINGLE_METRIC_CAP

    def test_observations_confidence_scored(self):
        obs, _ = measure_spectral(_tone({200: 0.4, 3500: 0.3}), SR)
        assert len(obs) == 8  # +sibilance_frame_p95 (analyzer 1.2.0)
        for o in obs:
            assert 0.0 <= o.confidence <= 1.0

    def test_deterministic(self):
        sig = _tone({200: 0.4, 3500: 0.3})
        a = {o.metric: o.value for o in measure_spectral(sig, SR)[0]}
        b = {o.metric: o.value for o in measure_spectral(sig, SR)[0]}
        assert a == b

    def test_short_signal_returns_empty(self):
        obs, ctx = measure_spectral(_tone({440: 0.5}, seconds=0.01), SR)
        assert obs == []
        assert ctx["reason"] == "signal_too_short"
