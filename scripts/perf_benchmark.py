"""Long-file performance benchmark (M36, RG-12 / risk R14).

Measures wall time and peak Python-heap allocation of the full v2 path
(preflight -> diagnose -> plan -> execute -> evaluate) across input durations,
on a deterministic synthetic vocal. Reports realtime factor (processing time /
audio duration) and MB peak per audio minute so regressions are visible.

    python scripts/perf_benchmark.py [--durations 30 60 180 300]

Writes reports/evaluations/perf/<stamp>.md (+json). Numbers are machine-
dependent; the committed report records the hardware-free shape (scaling
linearity), and tests/test_performance.py pins a generous realtime budget.
"""

import argparse
import json
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.dsp_engine import execute_plan  # noqa: E402
from src.evaluation import evaluate_arrays  # noqa: E402
from src.ingestion import preflight  # noqa: E402
from src.orchestration import analyze_and_plan  # noqa: E402

PERF_BENCHMARK_VERSION = "1.0.0"
SR = 44100


def make_vocal(seconds: float, seed: int = 42) -> np.ndarray:
    """Deterministic vocal-ish signal: harmonic phrases + esses + level variety."""
    rng = np.random.default_rng(seed)
    n = int(SR * seconds)
    t = np.arange(n) / SR
    x = np.zeros(n, dtype=np.float64)
    for k, amp in enumerate((1.0, 0.5, 0.33, 0.2), start=1):
        x += amp * np.sin(2 * np.pi * 220.0 * k * t)
    envelope = np.zeros(n)
    pos = 0.1
    while pos < seconds - 1.0:
        dur = float(rng.uniform(0.4, 1.2))
        level = float(rng.uniform(0.3, 1.0))
        i, m = int(pos * SR), int(dur * SR)
        m = min(m, n - i)
        envelope[i:i + m] = np.maximum(envelope[i:i + m], level * np.hanning(m))
        pos += dur + float(rng.uniform(0.1, 0.5))
    x *= envelope * (0.6 + 0.4 * np.sin(2 * np.pi * 2.3 * t) ** 2)
    x *= 0.25 / max(np.max(np.abs(x)), 1e-9)
    return x.astype(np.float32)


def run_once(seconds: float, workdir: Path, preset: str = "clean") -> dict:
    src = workdir / f"perf_{int(seconds)}s.wav"
    audio = make_vocal(seconds)
    sf.write(src, audio, SR, subtype="PCM_16")

    tracemalloc.start()
    started = time.perf_counter()

    report = preflight(src)
    bundle = analyze_and_plan(str(src), report, asset_id="perf", preset=preset)
    loaded, _ = sf.read(src, dtype="float32")
    out, _ = execute_plan(loaded, SR, bundle.plan)
    out = out[:, 0] if out.ndim == 2 else out
    evaluate_arrays(loaded, out, SR, plan=bundle.plan)

    elapsed = time.perf_counter() - started
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    src.unlink(missing_ok=True)

    return {
        "duration_s": seconds,
        "wall_s": round(elapsed, 2),
        "realtime_factor": round(elapsed / seconds, 3),
        "peak_alloc_mb": round(peak_bytes / 1e6, 1),
        "mb_per_audio_min": round(peak_bytes / 1e6 / (seconds / 60), 1),
        "actions": [a.processor for a in bundle.plan.actions],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--durations", nargs="+", type=float,
                        default=[30.0, 60.0, 180.0, 300.0])
    parser.add_argument("--preset", default="clean", choices=("clean", "polished"))
    args = parser.parse_args()

    workdir = REPO / "data" / "derived" / "perf"
    workdir.mkdir(parents=True, exist_ok=True)
    rows = [run_once(d, workdir, args.preset) for d in args.durations]

    out_dir = REPO / "reports" / "evaluations" / "perf"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    payload = {"perf_benchmark_version": PERF_BENCHMARK_VERSION,
               "preset": args.preset, "sample_rate": SR, "rows": rows}
    (out_dir / f"{stamp}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [f"# Performance benchmark {stamp} (preset={args.preset})", "",
             "| audio (s) | wall (s) | realtime× | peak alloc (MB) | MB/audio-min | chain |",
             "|--:|--:|--:|--:|--:|---|"]
    for r in rows:
        lines.append(f"| {r['duration_s']:.0f} | {r['wall_s']} | {r['realtime_factor']} "
                     f"| {r['peak_alloc_mb']} | {r['mb_per_audio_min']} | {'+'.join(r['actions']) or 'none'} |")
    lines += ["", "Machine-dependent numbers; the committed value is the *shape* "
                  "(linear scaling; realtime factor stability across durations)."]
    (out_dir / f"{stamp}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
