"""Batch processing tests (M20)."""

import json
import shutil

from fixtures.loader import AUDIO_DIR
from src.batch import run_batch


def _make_input(tmp_path):
    d = tmp_path / "in"
    d.mkdir()
    for name in ("harsh", "muddy", "silence"):
        shutil.copy(AUDIO_DIR / f"{name}.wav", d / f"{name}.wav")
    (d / "junk.wav").write_bytes(b"not audio")
    (d / "notes.txt").write_text("ignored non-audio")  # must be skipped
    return d


def test_batch_processes_all_audio(tmp_path):
    out = tmp_path / "out"
    summary = run_batch(_make_input(tmp_path), out)
    names = {it.name for it in summary.items}
    assert names == {"harsh", "muddy", "silence", "junk"}  # notes.txt skipped


def test_batch_statuses(tmp_path):
    summary = run_batch(_make_input(tmp_path), tmp_path / "out")
    by_name = {it.name: it for it in summary.items}
    assert by_name["harsh"].status == "completed"
    assert by_name["muddy"].status == "completed"
    assert by_name["silence"].status == "blocked"
    assert by_name["junk"].status == "failed"


def test_batch_writes_reports_and_audio(tmp_path):
    out = tmp_path / "out"
    run_batch(_make_input(tmp_path), out)
    assert (out / "harsh" / "before.wav").exists()
    assert (out / "harsh" / "after.wav").exists()
    assert (out / "harsh" / "report.md").exists()
    # blocked file: no processed audio, no report
    assert not (out / "silence" / "after.wav").exists()


def test_batch_writes_summary_index(tmp_path):
    out = tmp_path / "out"
    summary = run_batch(_make_input(tmp_path), out)
    assert (out / "summary.json").exists() and (out / "summary.md").exists()
    data = json.loads((out / "summary.json").read_text())
    assert data["counts"]["completed"] == 2
    assert data["counts"]["blocked"] == 1
    assert data["counts"]["failed"] == 1
    assert "Batch Summary" in (out / "summary.md").read_text()


def test_batch_completed_items_have_objectives(tmp_path):
    summary = run_batch(_make_input(tmp_path), tmp_path / "out")
    harsh = next(it for it in summary.items if it.name == "harsh")
    assert harsh.objectives and harsh.report_path


def test_empty_dir_is_ok(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    summary = run_batch(d, tmp_path / "out")
    assert summary.items == []
    assert summary.counts()["completed"] == 0
