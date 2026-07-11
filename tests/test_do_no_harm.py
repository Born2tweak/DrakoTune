"""Clean-input do-no-harm CI gate (M26).

Contract (validation plan §6.2, ADR 0004): on clean studio-quality input the
default (v2) engine must not audibly damage the recording — bounded spectral
change, true-peak safety, no clipping, no explosion of applied processors.
Uses the committed Tier A real-vocal fixtures (fixtures/audio_real/), so this
gate runs in CI on real voices, not just synthetic tones.
"""

import numpy as np
import pytest
import soundfile as sf

from pathlib import Path

from src.dsp_engine import execute_plan
from src.orchestration import analyze_and_plan

REPO = Path(__file__).resolve().parent.parent
FIXTURES = sorted((REPO / "fixtures" / "audio_real").glob("*.wav"))
STUDIO_FIXTURES = [p for p in FIXTURES if p.name.startswith("vocalset_")]

SR = 44100
TRUE_PEAK_CEILING = 10 ** (-1.0 / 20)   # -1 dBFS sample-peak proxy
MAX_BAND_DELTA_DB = 6.0                 # no band may move more than this on clean input
MAX_ACTIONS_ON_CLEAN = 3                # a clean take must not attract a full rack

BANDS = ((20, 80), (80, 250), (250, 500), (500, 2000), (2000, 5000), (5000, 10000))


def _band_db(x: np.ndarray, lo: float, hi: float) -> float:
    spectrum = np.abs(np.fft.rfft(x.astype(np.float64))) ** 2
    freqs = np.fft.rfftfreq(len(x), 1.0 / SR)
    e = float(np.sum(spectrum[(freqs >= lo) & (freqs <= hi)]))
    return 10.0 * np.log10(e + 1e-12)


def _process(path: Path) -> tuple[np.ndarray, np.ndarray, object]:
    audio, _ = sf.read(path, dtype="float32")
    bundle = analyze_and_plan(str(path))
    out, result = execute_plan(audio, SR, bundle.plan)
    return audio, (out[:, 0] if out.ndim == 2 else out), result


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_output_safety_on_real_fixtures(path):
    _, out, _ = _process(path)
    assert float(np.max(np.abs(out))) <= TRUE_PEAK_CEILING + 1e-4
    assert float(np.mean(np.abs(out) >= 0.999)) == 0.0


@pytest.mark.parametrize("path", STUDIO_FIXTURES, ids=lambda p: p.stem)
def test_clean_studio_input_band_changes_bounded(path):
    before, after, _ = _process(path)
    n = min(len(before), len(after))
    for lo, hi in BANDS:
        delta = _band_db(after[:n], lo, hi) - _band_db(before[:n], lo, hi)
        assert abs(delta) <= MAX_BAND_DELTA_DB, f"band {lo}-{hi}Hz moved {delta:+.1f} dB"


@pytest.mark.parametrize("path", STUDIO_FIXTURES, ids=lambda p: p.stem)
def test_clean_studio_input_attracts_few_processors(path):
    _, _, result = _process(path)
    non_safety = [a for a in result.applied if a.processor != "output_ceiling"]
    assert len(non_safety) <= MAX_ACTIONS_ON_CLEAN, \
        f"clean input attracted {[a.processor for a in non_safety]}"
