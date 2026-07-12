"""Degradation recipe library tests (M22).

Guards: bit-exact regeneration for deterministic families, measurable effect
per family (each recipe actually produces its defect), severity monotonicity,
and grid completeness. Codec recipes are effect-tested only (encoder builds
vary), matching the documented determinism scope.
"""

import numpy as np
import pytest

from fixtures.degradations import (
    DEGRADATION_LIBRARY_VERSION,
    DETERMINISTIC_FAMILIES,
    STANDARD_GRID,
    apply_recipe,
    output_sha256,
)

SR = 44100


@pytest.fixture(scope="module")
def voice_like():
    """Deterministic harmonic 'voice': 220 Hz + harmonics with slow AM, 3 s."""
    t = np.arange(int(SR * 3.0)) / SR
    x = np.zeros_like(t)
    for k, amp in enumerate((1.0, 0.5, 0.33, 0.2, 0.1), start=1):
        x += amp * np.sin(2 * np.pi * 220.0 * k * t)
    x *= 0.5 + 0.5 * np.sin(2 * np.pi * 3.0 * t) ** 2   # amplitude movement
    x *= 0.3 / np.max(np.abs(x))
    return x.astype(np.float32)


def _band_energy(x: np.ndarray, lo: float, hi: float) -> float:
    spectrum = np.abs(np.fft.rfft(x)) ** 2
    freqs = np.fft.rfftfreq(len(x), 1.0 / SR)
    return float(np.sum(spectrum[(freqs >= lo) & (freqs <= hi)]))


def _by_id(rid: str):
    return next(r for r in STANDARD_GRID if r.id == rid)


def test_grid_covers_planned_families():
    families = {r.family for r in STANDARD_GRID}
    assert families == {"noise", "hum", "clipping", "reverb", "harshness",
                        "sibilance", "proximity", "low_level", "codec", "plosive",
                        "overcompression", "gain_jumps", "dullness", "thinness"}
    assert len(STANDARD_GRID) == len({r.id for r in STANDARD_GRID}), "recipe ids must be unique"
    assert all(r.version == DEGRADATION_LIBRARY_VERSION for r in STANDARD_GRID)


def test_deterministic_families_regenerate_bit_exact(voice_like):
    for recipe in STANDARD_GRID:
        if recipe.family not in DETERMINISTIC_FAMILIES:
            continue
        first = apply_recipe(voice_like, SR, recipe)
        second = apply_recipe(voice_like, SR, recipe)
        assert output_sha256(first) == output_sha256(second), recipe.id


def test_noise_lowers_snr_monotonically(voice_like):
    floors = []
    for rid in ("noise_mild_room_tone", "noise_moderate_room_tone", "noise_strong_room_tone"):
        out = apply_recipe(voice_like, SR, _by_id(rid))
        residual = out - voice_like
        floors.append(float(np.sqrt(np.mean(residual ** 2))))
    assert floors[0] < floors[1] < floors[2]


def test_hum_adds_60hz_energy(voice_like):
    out = apply_recipe(voice_like, SR, _by_id("hum_strong"))
    assert _band_energy(out, 55, 65) > _band_energy(voice_like, 55, 65) * 2


def test_clipping_reaches_target_fraction(voice_like):
    for rid, frac in (("clipping_mild", 0.01), ("clipping_strong", 0.08)):
        out = apply_recipe(voice_like, SR, _by_id(rid))
        clipped = float(np.mean(np.abs(out) >= 0.999))
        assert frac * 0.3 <= clipped <= frac * 2.5, f"{rid}: clipped={clipped:.4f}"
    strong = apply_recipe(voice_like, SR, _by_id("clipping_strong"))
    mild = apply_recipe(voice_like, SR, _by_id("clipping_mild"))
    assert np.mean(np.abs(strong) >= 0.999) > np.mean(np.abs(mild) >= 0.999)


def test_reverb_smears_energy_into_silent_tail(voice_like):
    padded = np.concatenate([voice_like, np.zeros(SR // 2, dtype=np.float32)])
    out = apply_recipe(padded, SR, _by_id("reverb_strong"))
    tail_before = float(np.sqrt(np.mean(padded[-SR // 4:] ** 2)))
    tail_after = float(np.sqrt(np.mean(out[-SR // 4:] ** 2)))
    assert tail_before < 1e-6
    assert tail_after > 1e-3  # reverb tail rings into the silence


def test_spectral_boost_families_raise_their_bands(voice_like):
    checks = (
        ("harshness_strong", 3000, 5000),
        ("sibilance_strong", 5500, 12000),
        ("proximity_moderate", 60, 250),
    )
    for rid, lo, hi in checks:
        out = apply_recipe(voice_like, SR, _by_id(rid))
        assert _band_energy(out, lo, hi) > _band_energy(voice_like, lo, hi) * 1.5, rid


def test_low_level_reduces_gain(voice_like):
    moderate = apply_recipe(voice_like, SR, _by_id("low_level_moderate"))
    strong = apply_recipe(voice_like, SR, _by_id("low_level_strong"))
    assert np.max(np.abs(strong)) < np.max(np.abs(moderate)) < np.max(np.abs(voice_like))


def test_codec_roundtrip_effect(voice_like):
    out = apply_recipe(voice_like, SR, _by_id("codec_strong"))
    assert out.shape == voice_like.shape
    assert not np.array_equal(out, voice_like)          # it did something
    corr = float(np.corrcoef(out, voice_like)[0, 1])
    assert corr > 0.7                                    # but kept the signal


def test_recipe_manifest_roundtrip():
    recipe = _by_id("noise_strong_hvac")
    d = recipe.to_dict()
    assert d["family"] == "noise" and d["params"]["kind"] == "hvac"
    assert d["seed"] == recipe.seed and d["version"] == DEGRADATION_LIBRARY_VERSION


def test_plosive_recipe_adds_lf_bursts(voice_like):
    out = apply_recipe(voice_like, SR, _by_id("plosive_strong"))
    assert not np.array_equal(out, voice_like)
    assert _band_energy(out, 40, 120) > _band_energy(voice_like, 40, 120) * 1.5


def test_dullness_and_thinness_recipes(voice_like):
    dull = apply_recipe(voice_like, SR, _by_id("dullness_strong"))
    assert _band_energy(dull, 5000, 12000) < _band_energy(voice_like, 5000, 12000) * 0.5
    thin = apply_recipe(voice_like, SR, _by_id("thinness_strong"))
    assert _band_energy(thin, 80, 250) < _band_energy(voice_like, 80, 250) * 0.5
