"""Reference metrics + loudness-matched A/B export tests (M23)."""

import numpy as np
import pytest

from src.evaluation.ab_export import (
    MAX_MISMATCH_LU,
    TARGET_LUFS,
    LoudnessMatchError,
    loudness_matched_pair,
)
from src.evaluation.reference_metrics import segmental_snr, si_sdr

SR = 44100


def _tone(seconds=3.0, freq=220.0, amp=0.1):
    t = np.arange(int(SR * seconds)) / SR
    x = amp * np.sin(2 * np.pi * freq * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 2 * t))
    return x.astype(np.float32)


# --- SI-SDR -------------------------------------------------------------------

def test_si_sdr_perfect_reconstruction_is_high():
    x = _tone()
    assert si_sdr(x, x.copy()) > 60.0


def test_si_sdr_is_scale_invariant():
    x = _tone()
    noisy = x + 0.01 * np.random.default_rng(0).standard_normal(len(x)).astype(np.float32)
    assert abs(si_sdr(x, noisy) - si_sdr(x, noisy * 0.25)) < 1e-6


def test_si_sdr_decreases_with_noise():
    x = _tone()
    rng = np.random.default_rng(1)
    noise = rng.standard_normal(len(x)).astype(np.float32)
    light = si_sdr(x, x + 0.001 * noise)
    heavy = si_sdr(x, x + 0.05 * noise)
    assert light > heavy


def test_si_sdr_known_answer():
    # est = ref + orthogonal noise with 10% of ref energy -> SI-SDR = 10 dB.
    rng = np.random.default_rng(2)
    ref = rng.standard_normal(SR).astype(np.float64)
    noise = rng.standard_normal(SR)
    ref -= ref.mean()
    noise -= noise.mean()
    noise -= (np.dot(noise, ref) / np.dot(ref, ref)) * ref  # orthogonalize
    noise *= np.sqrt(0.1 * np.dot(ref, ref) / np.dot(noise, noise))
    assert abs(si_sdr(ref, ref + noise) - 10.0) < 0.1


# --- segmental SNR -------------------------------------------------------------

def test_seg_snr_orders_degradation_levels():
    x = _tone()
    rng = np.random.default_rng(3)
    noise = rng.standard_normal(len(x)).astype(np.float32)
    assert segmental_snr(x, x + 0.001 * noise, SR) > segmental_snr(x, x + 0.02 * noise, SR)


def test_seg_snr_clamps_and_handles_identity():
    x = _tone()
    assert segmental_snr(x, x.copy(), SR) == pytest.approx(35.0)  # ceiling clamp


# --- loudness matching ----------------------------------------------------------

def test_matched_pair_hits_target_and_tolerance():
    quiet = _tone(amp=0.02)
    loud = _tone(amp=0.4)
    pair = loudness_matched_pair(quiet, loud, SR)
    assert abs(pair.a_lufs - TARGET_LUFS) < 1.0
    assert abs(pair.a_lufs - pair.b_lufs) <= MAX_MISMATCH_LU
    assert pair.a_gain_db > 0 and pair.b_gain_db < 0  # quiet up, loud down


def test_matched_pair_peak_guard():
    # Highly peaky, quiet signal: gain-up to -23 LUFS would exceed the ceiling.
    x = _tone(amp=0.003)
    x[SR // 2] = 0.5  # isolated spike
    try:
        pair = loudness_matched_pair(x, _tone(amp=0.1), SR)
        assert np.max(np.abs(pair.a)) <= 10 ** (-1.5 / 20) + 1e-4
    except LoudnessMatchError:
        pass  # refusal is the designed alternative to emitting a biased pair


def test_matched_pair_rejects_silence():
    with pytest.raises(LoudnessMatchError):
        loudness_matched_pair(np.zeros(SR * 3, dtype=np.float32), _tone(), SR)
