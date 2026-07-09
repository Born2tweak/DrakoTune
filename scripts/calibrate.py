"""Print the calibration report (M17).

Runs the detectors over the labeled synthetic set and prints per-issue
true-positive and false-positive rates. This is evidence for adjusting
thresholds deliberately — it does not change any threshold itself.

    python scripts/calibrate.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.calibration import calibrate  # noqa: E402


def main() -> None:
    report = calibrate()
    print(json.dumps(report, indent=2, sort_keys=True))
    print("\nPer-issue detection (higher TPR / lower FPR is better):")
    for issue, st in sorted(report["issues"].items()):
        print(f"  {issue:12}  TPR={st['tpr']:.2f}  FPR={st['fpr']:.2f}  "
              f"(n+={st['n_positive']}, clean={st['n_clean']})")


if __name__ == "__main__":
    main()
