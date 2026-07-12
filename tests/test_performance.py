"""Performance budget tests (M36, RG-12/R14).

Generous budgets: these catch order-of-magnitude regressions (accidental
O(n^2), duplicated full-file copies), not machine variance. Measured local
baseline (2026-07-12): realtime factor ~0.07, ~180 MB peak alloc per audio
minute, linear scaling (reports/evaluations/perf/).
"""

import sys
import tracemalloc
from pathlib import Path

import numpy as np
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from perf_benchmark import make_vocal  # noqa: E402

from src.dsp_engine import execute_plan  # noqa: E402
from src.orchestration import analyze_and_plan  # noqa: E402

SR = 44100

MAX_REALTIME_FACTOR = 0.8      # 60 s of audio must process in < 48 s
MAX_MB_PER_AUDIO_MIN = 500.0   # measured ~180; alarm at ~3x


def test_sixty_second_file_budget(tmp_path):
    import time

    seconds = 60.0
    src = tmp_path / "perf60.wav"
    sf.write(src, make_vocal(seconds), SR, subtype="PCM_16")

    tracemalloc.start()
    started = time.perf_counter()
    bundle = analyze_and_plan(str(src), asset_id="perf")
    audio, _ = sf.read(src, dtype="float32")
    out, _ = execute_plan(audio, SR, bundle.plan)
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert elapsed / seconds < MAX_REALTIME_FACTOR, f"realtime factor {elapsed / seconds:.2f}"
    assert peak / 1e6 / (seconds / 60) < MAX_MB_PER_AUDIO_MIN, \
        f"{peak / 1e6:.0f} MB peak for one minute of audio"
    out = out[:, 0] if out.ndim == 2 else out
    assert np.max(np.abs(out)) <= 1.0 and len(out) > 0
