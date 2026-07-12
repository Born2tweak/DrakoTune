"""Dynamic de-esser tests (M30): effectiveness, lisp guard, transparency,
determinism, and mixed plugin/array executor ordering."""

import numpy as np
import pytest
import soundfile as sf

from fixtures.degradations import STANDARD_GRID, apply_recipe
from src.dsp_engine import execute_plan
from src.dsp_engine.deesser import de_ess
from src.dsp_engine.processors import PROCESSORS, clamp_params
from src.orchestration import analyze_and_plan

SR = 44100


def _voice(seconds=4.0):
    n = int(SR * seconds)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, amp in enumerate((1.0, 0.5, 0.33, 0.2), start=1):
        x += amp * np.sin(2 * np.pi * 220.0 * k * t)
    envelope = np.zeros(n)
    for start_s, dur_s in ((0.10, 0.85), (1.15, 0.60), (2.05, 1.10), (3.40, 0.45)):
        i, m = int(start_s * SR), int(dur_s * SR)
        envelope[i:i + m] = np.maximum(envelope[i:i + m], np.hanning(m))
    x *= envelope * (0.6 + 0.4 * np.sin(2 * np.pi * 2.3 * t) ** 2)
    x *= 0.25 / max(np.max(np.abs(x)), 1e-9)
    return x.astype(np.float32)


def _with_esses(voice):
    """Add short bandlimited-noise 's' bursts (5-9 kHz) DURING phrases.

    Placement matters: a burst in silence saturates the frame-fraction metric
    (band/full ≈ 1 regardless of level); real esses overlap voice, so the
    bursts sit mid-phrase where the fraction responds to attenuation.
    """
    rng = np.random.default_rng(11)
    out = voice.copy()
    burst_len = int(SR * 0.09)
    for pos_s in (0.50, 1.45, 2.60, 3.55):
        noise = rng.standard_normal(burst_len)
        spectrum = np.fft.rfft(noise)
        freqs = np.fft.rfftfreq(burst_len, 1.0 / SR)
        spectrum[(freqs < 5000) | (freqs > 9000)] = 0.0
        burst = np.fft.irfft(spectrum, burst_len).astype(np.float32)
        # 0.8 puts the before-p95 near 0.29 — the range measured on the
        # user-tested real files (0.29-0.40). Quieter bursts sit below the
        # detection threshold and only reshuffle the percentile.
        burst *= 0.8 / max(np.max(np.abs(burst)), 1e-9)
        burst *= np.hanning(burst_len).astype(np.float32)
        i = int(pos_s * SR)
        out[i:i + burst_len] += burst
    return out


def _frame_sib_p95(x):
    import librosa
    S = np.abs(librosa.stft(x, n_fft=2048, hop_length=512)) ** 2
    f = librosa.fft_frequencies(sr=SR, n_fft=2048)
    frac = S[(f >= 5000) & (f <= 8000)].sum(axis=0) / (S.sum(axis=0) + 1e-20)
    return float(np.percentile(frac, 95))


def test_de_ess_reduces_sibilant_frames():
    sibilant = _with_esses(_voice())
    out = de_ess(sibilant, SR)
    assert _frame_sib_p95(out) < _frame_sib_p95(sibilant) * 0.75
    assert _frame_sib_p95(out) < 0.2


def test_lisp_guard_reduction_is_capped():
    """An 's' is tamed, never deleted: band energy in sibilant moments keeps
    at least the max_reduction_db floor."""
    sibilant = _with_esses(_voice())
    out = de_ess(sibilant, SR, max_reduction_db=8.0)
    i, m = int(0.50 * SR), int(SR * 0.09)  # first burst position

    def band_energy(x):
        seg = x[i:i + m].astype(np.float64)
        spectrum = np.abs(np.fft.rfft(seg)) ** 2
        freqs = np.fft.rfftfreq(len(seg), 1.0 / SR)
        return float(np.sum(spectrum[(freqs >= 5000) & (freqs <= 9000)]))

    reduction_db = 10 * np.log10(band_energy(out) / band_energy(sibilant))
    assert reduction_db < -2.0            # it did something to the ess
    assert reduction_db > -10.0           # but never past the cap (+istft smear margin)


def test_non_sibilant_content_passes_transparently():
    voice = _voice()  # harmonic content only, nothing near the band
    out = de_ess(voice, SR)
    n = min(len(out), len(voice))
    residual = out[:n] - voice[:n]
    assert 20 * np.log10(np.sqrt(np.mean(residual ** 2)) + 1e-12) < -50.0


def test_deterministic():
    sibilant = _with_esses(_voice())
    a = de_ess(sibilant, SR)
    b = de_ess(sibilant, SR)
    assert np.array_equal(a, b)


def test_clamping_and_registry():
    params, clamped = clamp_params("DeEsser", {"band_lo_hz": 1000.0, "band_hi_hz": 20000.0,
                                               "frame_threshold": 0.01, "max_reduction_db": 40.0})
    assert params["band_lo_hz"] == 4000.0 and params["band_hi_hz"] == 11000.0
    assert params["frame_threshold"] == 0.10 and params["max_reduction_db"] == 10.0
    assert len(clamped) == 4
    spec = PROCESSORS["DeEsser"]
    assert spec.process is not None and spec.factory is None
    assert spec.objective == "reduce_sibilance"


def test_end_to_end_plan_uses_deesser(tmp_path):
    sibilant = apply_recipe(_with_esses(_voice()), SR,
                            next(r for r in STANDARD_GRID if r.id == "sibilance_strong"))
    src = tmp_path / "sib.wav"
    sf.write(src, sibilant, SR, subtype="PCM_16")

    bundle = analyze_and_plan(str(src), asset_id="sib")
    processors = [a.processor for a in bundle.plan.actions]
    assert "DeEsser" in processors, processors

    audio, _ = sf.read(src, dtype="float32")
    out, result = execute_plan(audio, SR, bundle.plan)
    out = out[:, 0] if out.ndim == 2 else out
    assert _frame_sib_p95(out) < _frame_sib_p95(sibilant)
    assert float(np.max(np.abs(out))) <= 10 ** (-0.2 / 20) + 1e-4  # ceiling holds
    assert any(a.processor == "DeEsser" for a in result.applied)


def test_executor_mixed_plugin_and_array_order(tmp_path):
    """Plugins before and after an array processor all execute (segmenting)."""
    from src.shared_types import ProcessingAction, ProcessingPlan

    plan = ProcessingPlan(
        id="p", preset_profile="test", objectives=(), skipped_processors=(),
        policy_version="test",
        actions=(
            ProcessingAction(id="a1", processor="HighpassFilter",
                             parameters={"cutoff_frequency_hz": 100.0}, strength=1.0,
                             reason="t", objective_id="o1", reversible=True),
            ProcessingAction(id="a2", processor="DeEsser",
                             parameters={"band_lo_hz": 5000.0, "band_hi_hz": 9000.0,
                                         "frame_threshold": 0.18, "max_reduction_db": 8.0},
                             strength=1.0, reason="t", objective_id="o2", reversible=True),
            ProcessingAction(id="a3", processor="Gain",
                             parameters={"gain_db": -6.0}, strength=1.0,
                             reason="t", objective_id="o3", reversible=True),
        ),
    )
    x = _with_esses(_voice())
    out, result = execute_plan(x, SR, plan, apply_output_safety=False)
    out = out[:, 0] if out.ndim == 2 else out
    assert [a.processor for a in result.applied] == ["HighpassFilter", "DeEsser", "Gain"]
    # Gain -6 dB after the chain: overall RMS clearly reduced.
    assert np.sqrt(np.mean(out ** 2)) < np.sqrt(np.mean(x ** 2)) * 0.7
    # HPF ran: sub-80 Hz content attenuated.
    spectrum = lambda sig: np.abs(np.fft.rfft(sig.astype(np.float64))) ** 2
    freqs = np.fft.rfftfreq(len(x), 1.0 / SR)
    lf = (freqs >= 20) & (freqs <= 60)
    assert np.sum(spectrum(out[:len(x)])[lf]) < np.sum(spectrum(x)[lf])