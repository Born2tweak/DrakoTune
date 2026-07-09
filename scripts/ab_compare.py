"""A/B comparison: v2 decision engine vs legacy adaptive chain (M19).

For each fixture, reports a targeted metric (harshness-band energy) for the
input, the v2 output, and the legacy output, plus output clipping. This is
transparency for the default switch — it does not assert that v2 "beats" legacy
subjectively; the guard (tests/test_ab_v2_vs_legacy.py) checks that v2 is safe
and achieves its objectives.

    python scripts/ab_compare.py
"""

import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fixtures import list_fixtures, load_fixture  # noqa: E402
from fixtures.loader import AUDIO_DIR  # noqa: E402
from src.diagnostics import measure_safety  # noqa: E402
from src.dsp.diagnose import diagnose  # noqa: E402  (legacy diagnose)
from src.dsp.pipeline import process_audio  # noqa: E402
from src.dsp_engine import execute_plan  # noqa: E402
from src.orchestration import analyze_and_plan  # noqa: E402


def _harsh_energy(a: np.ndarray, sr: int) -> float:
    fft = np.fft.rfft(a)
    freqs = np.fft.rfftfreq(len(a), 1.0 / sr)
    mask = (freqs >= 2500) & (freqs <= 6000)
    return float(np.sum(np.abs(fft[mask]) ** 2))


def _clip(a: np.ndarray, sr: int) -> float:
    return {o.metric: o.value for o in measure_safety(a, sr)[0]}["clipping_ratio"]


def _mono(a: np.ndarray) -> np.ndarray:
    return a[:, 0] if a.ndim > 1 else a


def main() -> None:
    print(f"{'fixture':11} {'input_harsh':>12} {'v2_harsh':>12} {'legacy_harsh':>13} "
          f"{'v2_clip':>8} {'legacy_clip':>11}")
    for name in list_fixtures():
        fx = load_fixture(name)
        sr = fx.sample_rate

        bundle = analyze_and_plan(str(AUDIO_DIR / f"{name}.wav"))
        v2_out = _mono(execute_plan(fx.audio, sr, bundle.plan)[0])

        with tempfile.TemporaryDirectory() as td:
            outp = Path(td) / "legacy.wav"
            profile = diagnose(str(AUDIO_DIR / f"{name}.wav"))
            process_audio(str(AUDIO_DIR / f"{name}.wav"), str(outp), profile=profile)
            import soundfile as sf
            legacy_out = _mono(sf.read(str(outp), dtype="float32")[0])

        print(f"{name:11} {_harsh_energy(fx.audio, sr):12.1f} {_harsh_energy(v2_out, sr):12.1f} "
              f"{_harsh_energy(legacy_out, sr):13.1f} {_clip(v2_out, sr):8.4f} "
              f"{_clip(legacy_out, sr):11.4f}")


if __name__ == "__main__":
    main()
