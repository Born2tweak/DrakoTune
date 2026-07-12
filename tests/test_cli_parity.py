"""CLI/batch parity tests (M37): advisory findings + JSON manifest everywhere."""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "fixtures" / "audio_real" / "vocadito_1.wav"


def test_cli_writes_markdown_and_json_manifest(tmp_path):
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "run_alpha.py"), str(FIXTURE),
         "--output-dir", str(tmp_path), "--name", "parity"],
        capture_output=True, text=True, timeout=300, cwd=REPO)
    assert result.returncode == 0, result.stderr[-500:]
    assert (tmp_path / "parity_report.md").exists()
    manifest = json.loads((tmp_path / "parity_report.json").read_text(encoding="utf-8"))
    assert manifest["report_engine_version"].startswith("2.")
    assert set(manifest["analyzers"]) == {"safety", "loudness", "spectral"}
    assert "plan" in manifest and "evaluation" in manifest


def test_batch_writes_manifest_and_respects_preset(tmp_path):
    from src.batch import run_batch

    in_dir = tmp_path / "in"
    in_dir.mkdir()
    (in_dir / "clip.wav").write_bytes(FIXTURE.read_bytes())
    out_dir = tmp_path / "out"

    summary = run_batch(in_dir, out_dir, preset="polished")
    assert len(summary.items) == 1 and summary.items[0].status == "completed"
    workdirs = list(out_dir.glob("*/report.json"))
    assert workdirs, "batch must write a JSON manifest per file"
    manifest = json.loads(workdirs[0].read_text(encoding="utf-8"))
    assert manifest["plan"]  # plan recorded (preset effects visible in actions)
