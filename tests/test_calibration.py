"""Calibration harness tests (M17).

Pins current detector performance on the labeled synthetic set: strong positives
are detected (high TPR) and clean controls rarely trip detectors (low FPR). This
locks in the muddiness false-positive fix and catches detection regressions.
"""

from src.calibration import ISSUES, build_samples, calibrate, detect_issues

MIN_TPR = 0.9   # strong positives should be detected
MAX_FPR = 0.34  # clean controls should rarely trip a detector


def test_report_shape():
    report = calibrate()
    assert set(report["issues"]) == set(ISSUES)
    assert report["n_samples"] > 0


def test_true_positive_rates_meet_bar():
    issues = calibrate()["issues"]
    for issue, st in issues.items():
        assert st["tpr"] >= MIN_TPR, f"{issue} TPR {st['tpr']} below {MIN_TPR}"


def test_false_positive_rates_within_bar():
    issues = calibrate()["issues"]
    for issue, st in issues.items():
        assert st["fpr"] <= MAX_FPR, f"{issue} FPR {st['fpr']} above {MAX_FPR}"


def test_muddiness_no_longer_false_positives_on_clean():
    # Regression guard for the M17 fix: clean controls must not read as muddy.
    assert calibrate()["issues"]["muddiness"]["fpr"] == 0.0


def test_detection_deterministic():
    samples = build_samples()
    a = {s.name: detect_issues(s.audio) for s in samples}
    b = {s.name: detect_issues(s.audio) for s in samples}
    assert a == b


def test_clean_controls_mostly_quiet():
    # A clean control should trip at most one detector (ideally none).
    for s in build_samples():
        if s.issue is None:
            assert len(detect_issues(s.audio)) <= 1
