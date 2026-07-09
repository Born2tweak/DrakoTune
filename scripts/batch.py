"""Batch-process a directory of vocals (M20).

    python scripts/batch.py <input_dir> --output-dir batch_out/

Writes per-file <name>/before.wav, <name>/after.wav, <name>/report.md and a
top-level summary.json + summary.md.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.batch import run_batch  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="DrakoTune batch processor")
    parser.add_argument("input_dir", help="Directory of raw vocal files")
    parser.add_argument("--output-dir", default="batch_out", help="Output directory")
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    if not in_dir.is_dir():
        print(f"Error: not a directory: {in_dir}")
        sys.exit(1)

    summary = run_batch(in_dir, args.output_dir)
    c = summary.counts()
    print(f"Processed {len(summary.items)} file(s): "
          f"{c['completed']} completed, {c['blocked']} blocked, {c['failed']} failed.")
    for it in summary.items:
        detail = (f" - {it.passed} passed / {it.failed} failed"
                  if it.status == "completed" else f" - {it.message}")
        print(f"  [{it.status:9}] {it.name}{detail}")
    print(f"Summary: {Path(args.output_dir) / 'summary.md'}")


if __name__ == "__main__":
    main()
