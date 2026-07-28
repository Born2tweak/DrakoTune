"""Intentional output gain staging (DT-96 integration).

The pre-V3 output stage was attenuate-only, on the principle that a makeup
limiter would "boost quiet material and inflate loudness". That principle is
right about *evaluation* and wrong about *export*: it meant every chain that cut
anything handed back a quieter file, and the DT-95 renders duly came out 3.7-8.3
dB down. A vocal that is correct but quiet reads as worse, so the attenuate-only
rule was silently penalising the chains it was meant to protect.

The fix is to separate three intents that were previously one:

  RAW       - exactly what the graph produced. Ceiling enforced, nothing else.
              This is what evaluation and any metric comparison must use, because
              a makeup gain would corrupt every level-sensitive measurement.

  AUDITION  - for A/B listening. Level is NOT adjusted here; fair comparison is
              done by loudness-matching the pair together
              (`evaluation.ab_export.export_matched_pair`), which is the only way
              to make two files comparable to each other rather than to a target.

  EXPORT    - the file the user keeps. Gain is applied so the result lands at an
              intended peak headroom instead of wherever the chain happened to
              leave it.

In every case the hard ceiling is applied last and is never exceeded. Gain
staging changes how loud the delivered file is; it cannot change whether the
output is safe.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from src.dsp_engine.channels import normalize

# Hard peak ceiling. Unchanged from the M09 executor: attenuate-only protection
# that no stage may exceed.
CEILING_DBFS = -0.2
_CEILING_LINEAR = 10.0 ** (CEILING_DBFS / 20.0)

# Export target peak. Below the ceiling so downstream encoding has headroom.
EXPORT_TARGET_PEAK_DBFS = -1.0

# Never apply more than this much makeup. A chain that needs more than 12 dB to
# reach the target has removed most of the signal, and quietly amplifying that
# would hide the problem instead of surfacing it.
MAX_MAKEUP_DB = 12.0


class GainStage(Enum):
    RAW = "raw"
    AUDITION = "audition"
    EXPORT = "export"


@dataclass(frozen=True)
class GainStagingResult:
    applied_db: float
    peak_dbfs_before: float
    peak_dbfs_after: float
    stage: GainStage
    makeup_clamped: bool

    def to_dict(self) -> dict:
        return {
            "stage": self.stage.value,
            "applied_db": round(self.applied_db, 3),
            "peak_dbfs_before": round(self.peak_dbfs_before, 3),
            "peak_dbfs_after": round(self.peak_dbfs_after, 3),
            "makeup_clamped": self.makeup_clamped,
        }


def _peak(audio: np.ndarray) -> float:
    return float(np.max(np.abs(audio))) if audio.size else 0.0


def _dbfs(peak: float) -> float:
    return 20.0 * float(np.log10(peak)) if peak > 0 else -120.0


def apply_ceiling(audio: np.ndarray) -> np.ndarray:
    """Attenuate-only headroom protection. Never boosts."""
    a = normalize(audio)
    peak = _peak(a)
    if peak > _CEILING_LINEAR:
        a = a * np.float32(_CEILING_LINEAR / peak)
    return np.clip(a, -1.0, 1.0).astype(np.float32)


def stage_output(
    audio: np.ndarray, stage: GainStage | str = GainStage.RAW
) -> tuple[np.ndarray, GainStagingResult]:
    """Apply the gain intent for `stage`, then the hard ceiling."""
    resolved = GainStage(stage) if isinstance(stage, str) else stage
    a = normalize(audio)
    peak_before = _peak(a)
    applied_db = 0.0
    clamped = False

    if resolved is GainStage.EXPORT and peak_before > 0.0:
        target = 10.0 ** (EXPORT_TARGET_PEAK_DBFS / 20.0)
        wanted_db = 20.0 * float(np.log10(target / peak_before))
        if wanted_db > MAX_MAKEUP_DB:
            applied_db = MAX_MAKEUP_DB
            clamped = True
        else:
            # Attenuation is applied in full; only boosting is capped.
            applied_db = wanted_db
        a = (a * np.float32(10.0 ** (applied_db / 20.0))).astype(np.float32)

    a = apply_ceiling(a)
    return a, GainStagingResult(
        applied_db=applied_db,
        peak_dbfs_before=_dbfs(peak_before),
        peak_dbfs_after=_dbfs(_peak(a)),
        stage=resolved,
        makeup_clamped=clamped,
    )
