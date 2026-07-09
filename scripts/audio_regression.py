"""Audio regression check (M15).

For every fixture, run the deterministic path (preflight -> diagnostics ->
decision -> plan -> render -> evaluate -> report) and compute a stable
*decision fingerprint*: objectives, applied processors, skipped issues, the
safety decision, and per-objective pass/fail. The fingerprint deliberately
excludes raw metric floats and confidence values so it is robust across
platforms while still catching any change in what DrakoTune *decides* to do.

Usage:
    python scripts/audio_regression.py            # check against goldens
    python scripts/audio_regression.py --update   # regenerate goldens

On mismatch, the actual fingerprint is written under artifacts/ (for CI upload)
and the process exits non-zero.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fixtures import list_fixtures, load_fixture  # noqa: E402
from fixtures.loader import AUDIO_DIR  # noqa: E402
from src.dsp_engine import execute_plan  # noqa: E402
from src.evaluation import evaluate_arrays  # noqa: E402
from src.ingestion import preflight  # noqa: E402
from src.orchestration import analyze_and_plan  # noqa: E402
from src.reports import build_report  # noqa: E402

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "regression"
ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"


def _skipped_issue(entry: str) -> dict:
    # "PeakFilter:sibilance (report-only: low confidence)" -> issue + reason kind
    issue = entry.split(":", 1)[1].split(" (", 1)[0] if ":" in entry else entry
    if "enhancement blocked" in entry:
        reason = "enhancement_blocked"
    elif "report-only" in entry:
        reason = "report_only"
    else:
        reason = "other"
    return {"issue": issue.strip(), "reason": reason}


def build_fingerprint(name: str) -> dict:
    path = str(AUDIO_DIR / f"{name}.wav")
    pf = preflight(path)
    bundle = analyze_and_plan(path, pf, asset_id=name)

    before = load_fixture(name).audio
    after, _ = execute_plan(before, load_fixture(name).sample_rate, bundle.plan)
    after = after[:, 0] if after.ndim > 1 else after
    evaluation = evaluate_arrays(before, after, load_fixture(name).sample_rate, plan=bundle.plan)
    report = build_report(bundle, evaluation, asset_name=name)

    def goal_of(check: str) -> str:
        return check.split(":", 1)[0]

    return {
        "name": name,
        "preflight_passed": pf.passed,
        "objectives": sorted(o.goal for o in bundle.plan.objectives),
        "applied_processors": sorted(
            f"{a.processor}<-{a.objective_id}" for a in bundle.plan.actions
        ),
        "skipped": sorted(
            (json.dumps(_skipped_issue(s), sort_keys=True) for s in bundle.plan.skipped_processors)
        ),
        "decision": {
            "processing_allowed": bundle.decision.processing_allowed,
            "enhancement_allowed": bundle.decision.enhancement_allowed,
            "positive_gain_allowed": bundle.decision.positive_gain_allowed,
            "blocked_targets": sorted(bundle.decision.blocked_targets),
        },
        "evaluation": {
            "passed": sorted(goal_of(c) for c in evaluation.passed_checks),
            "failed": sorted(goal_of(c) for c in evaluation.failed_checks),
        },
        "report_finding_count": len(report.findings),
    }


def golden_path(name: str) -> Path:
    return GOLDEN_DIR / f"{name}.json"


def update_goldens() -> list[str]:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    names = list_fixtures()
    for name in names:
        golden_path(name).write_text(json.dumps(build_fingerprint(name), indent=2, sort_keys=True) + "\n")
    return names


def check() -> int:
    failures: list[str] = []
    for name in list_fixtures():
        actual = build_fingerprint(name)
        gp = golden_path(name)
        if not gp.exists():
            failures.append(f"{name}: no golden (run --update)")
            _write_artifact(name, actual)
            continue
        expected = json.loads(gp.read_text())
        if actual != expected:
            failures.append(f"{name}: decision fingerprint changed")
            _write_artifact(name, actual)

    if failures:
        print("AUDIO REGRESSION FAILED:")
        for f in failures:
            print(f"  - {f}")
        print(f"Actual fingerprints written to {ARTIFACT_DIR} for inspection.")
        return 1
    print(f"Audio regression OK: {len(list_fixtures())} fixtures match goldens.")
    return 0


def _write_artifact(name: str, fingerprint: dict) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_DIR / f"{name}.actual.json").write_text(
        json.dumps(fingerprint, indent=2, sort_keys=True) + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="DrakoTune audio regression check")
    parser.add_argument("--update", action="store_true", help="regenerate golden fingerprints")
    args = parser.parse_args()
    if args.update:
        names = update_goldens()
        print(f"Updated {len(names)} goldens: {', '.join(names)}")
        return
    sys.exit(check())


if __name__ == "__main__":
    main()
