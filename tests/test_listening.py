"""Listening-test tooling tests (M24).

The analysis pipeline is tested end-to-end with a synthetic session key and
synthetic listener responses (no audio, no local corpus needed). Session
*preparation* needs the local corpus and is exercised manually / locally.
"""

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from listening_analyze import _binom_p_geq, analyze  # noqa: E402


def test_binomial_tail_known_values():
    assert _binom_p_geq(0, 10) == 1.0
    assert abs(_binom_p_geq(10, 10) - 0.5 ** 10) < 1e-12
    assert abs(_binom_p_geq(8, 10) - 0.0546875) < 1e-6  # classic table value
    assert _binom_p_geq(15, 20) < 0.05 < _binom_p_geq(13, 20)


def _make_session(tmp_path: Path) -> Path:
    session = tmp_path / "session"
    session.mkdir()
    trials = []
    for i in range(10):  # defect trials, processed always on side B
        trials.append({"trial": f"t{i + 1:03d}", "kind": "defect", "processed_is": "B",
                       "clip_id": f"c{i}", "family": "noise", "severity": "strong"})
    trials.append({"trial": "t011", "kind": "clean", "processed_is": "A",
                   "clip_id": "c_clean", "family": "none", "severity": "clean"})
    for i in (12, 13):
        trials.append({"trial": f"t{i:03d}", "kind": "catch", "processed_is": "neither",
                       "clip_id": "c_catch", "family": "none", "severity": "identical"})
    (session / "session_key.json").write_text(json.dumps({"trials": trials}))
    return session


def _write_responses(path: Path, listener: str, defect_pref: str, catch_pref: str,
                     clean_pref: str = "none") -> None:
    header = ["listener_id", "listener_type", "trial", "preference(A/B/none)", "strength(1-5)",
              "artifact_pumping", "notes"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for i in range(10):
            writer.writerow([listener, "artist", f"t{i + 1:03d}", defect_pref, "3", "", ""])
        writer.writerow([listener, "artist", "t011", clean_pref, "", "", ""])
        for i in (12, 13):
            writer.writerow([listener, "artist", f"t{i:03d}", catch_pref, "", "", ""])


def test_analysis_pass_case_and_preference_log(tmp_path):
    session = _make_session(tmp_path)
    r1, r2 = tmp_path / "l1.csv", tmp_path / "l2.csv"
    _write_responses(r1, "l1", defect_pref="B", catch_pref="none")   # honest, prefers processed
    _write_responses(r2, "l2", defect_pref="B", catch_pref="none")
    log = tmp_path / "log.jsonl"

    result = analyze(session, [r1, r2], log_path=log)

    noise = next(f for f in result["family_results"] if f["family"] == "noise")
    assert noise["n"] == 20 and noise["rate"] == 1.0 and noise["passes"]
    assert result["do_no_harm_pass"] is True          # clean pref "none" -> not preferred
    assert result["listeners_excluded_by_catch"] == []
    assert result["pairwise_agreement"] == 1.0
    assert (session / "analysis.md").exists() and (session / "analysis.json").exists()
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 26                            # 13 trials x 2 listeners
    assert json.loads(lines[0])["schema"] == 1


def test_catch_trial_screening_excludes_listener(tmp_path):
    session = _make_session(tmp_path)
    good, bad = tmp_path / "good.csv", tmp_path / "bad.csv"
    _write_responses(good, "good", defect_pref="B", catch_pref="none")
    _write_responses(bad, "bad", defect_pref="A", catch_pref="A")     # fails both catches

    result = analyze(session, [good, bad], log_path=tmp_path / "log.jsonl")

    assert result["listeners_excluded_by_catch"] == ["bad"]
    noise = next(f for f in result["family_results"] if f["family"] == "noise")
    assert noise["n"] == 10                            # only the good listener counts


def test_underpowered_family_gets_no_verdict(tmp_path):
    session = _make_session(tmp_path)
    r1 = tmp_path / "l1.csv"
    header = ["listener_id", "listener_type", "trial", "preference(A/B/none)", "strength(1-5)",
              "artifact_pumping", "notes"]
    with open(r1, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for i in range(4):                             # only 4 of 10 defect trials answered
            writer.writerow(["l1", "engineer", f"t{i + 1:03d}", "B", "4", "", ""])
    result = analyze(session, [r1], log_path=tmp_path / "log.jsonl")
    noise = next(f for f in result["family_results"] if f["family"] == "noise")
    assert noise["passes"] is False and "underpowered" in noise["note"]
