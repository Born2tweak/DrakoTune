"""Mode distinctness measurement (DT-95).

The failure this exists to prevent is the one the pre-V3 engine actually had:
two "modes" that differ by one gentle compressor and therefore sound the same.
A mode that cannot be told apart from another mode is a renamed preset.

Distinctness is measured two ways, and both must hold:

  * STRUCTURAL - the graphs differ in topology/parameters. Cheap, exact, and it
    catches copy-paste modes without rendering anything.
  * AUDIBLE - the rendered outputs differ by more than a threshold, measured on
    level-matched signals. Level matching matters because otherwise a pure gain
    change would register as a large difference while sounding identical.

This is a *difference* measure, not a quality measure. It says two modes are not
the same. It says nothing about either one being good, and no perceptual claim
follows from it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.dsp_engine.channels import match_channels, normalize
from src.dsp_engine.graph import render_graph
from src.modes.contracts import Intensity, build_graph

# Minimum level-matched difference for two modes to count as audibly distinct.
# -30 dB relative to the signal is a difference of roughly 3% RMS — well above
# dither/rounding, well below "these are unrelated sounds".
AUDIBLE_DELTA_FLOOR_DB = -30.0


def _rms(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(a, dtype=np.float64)))) if a.size else 0.0


def _level_match(reference: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Scale `target` to `reference`'s RMS so gain alone cannot fake distinctness."""
    ref_rms, tgt_rms = _rms(reference), _rms(target)
    if tgt_rms <= 0.0 or ref_rms <= 0.0:
        return target
    return (target * (ref_rms / tgt_rms)).astype(np.float32)


def difference_db(a: np.ndarray, b: np.ndarray) -> float:
    """Level-matched RMS difference between two renders, relative to the first."""
    x, y = normalize(a), normalize(b)
    n = min(x.shape[0], y.shape[0])
    if n == 0:
        return -120.0
    width = max(x.shape[1], y.shape[1])
    x = match_channels(x[:n], width)
    y = match_channels(y[:n], width)
    y = _level_match(x, y)
    base = _rms(x)
    if base <= 0.0:
        return -120.0
    return 20.0 * float(np.log10(max(_rms(x - y), 1e-12) / base))


@dataclass(frozen=True)
class DistinctnessResult:
    mode_a: str
    mode_b: str
    structural: bool
    delta_db: float

    @property
    def audible(self) -> bool:
        return self.delta_db > AUDIBLE_DELTA_FLOOR_DB

    @property
    def distinct(self) -> bool:
        return self.structural and self.audible

    def to_dict(self) -> dict:
        return {
            "mode_a": self.mode_a,
            "mode_b": self.mode_b,
            "structural": self.structural,
            "delta_db": round(self.delta_db, 2),
            "audible": self.audible,
            "distinct": self.distinct,
        }


def compare_modes(
    mode_a: str,
    mode_b: str,
    audio: np.ndarray,
    sample_rate: int,
    intensity: Intensity | str | None = None,
) -> DistinctnessResult:
    graph_a = build_graph(mode_a, intensity)
    graph_b = build_graph(mode_b, intensity)
    structural = graph_a.describe() != graph_b.describe()
    rendered_a = render_graph(audio, sample_rate, graph_a)
    rendered_b = render_graph(audio, sample_rate, graph_b)
    return DistinctnessResult(
        mode_a=mode_a,
        mode_b=mode_b,
        structural=structural,
        delta_db=difference_db(rendered_a, rendered_b),
    )


def compare_all(
    modes: list[str],
    audio: np.ndarray,
    sample_rate: int,
    intensity: Intensity | str | None = None,
) -> list[DistinctnessResult]:
    """Every unordered pair, so one duplicated mode cannot hide in the set."""
    return [
        compare_modes(modes[i], modes[j], audio, sample_rate, intensity)
        for i in range(len(modes))
        for j in range(i + 1, len(modes))
    ]
