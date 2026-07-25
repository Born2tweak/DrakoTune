"""The anonymization gate must actually catch a leak, not just pass (D-029).

A gate nobody has seen fail is not evidence. These tests plant a leak and
require the detector to find it, and require ordinary audio vocabulary not to
trip it.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "check_corpus_anonymization", REPO / "scripts" / "check_corpus_anonymization.py")
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


def _records():
    return [{
        "filename": "03 Someartist - Rockstar In His Prime (Studio Acapella) [lhvPA8yfr0U].mp3",
        "artist_hint": "Someartist", "title_hint": "Rockstar In His Prime (Studio Acapella)",
        "pair_key_hint": "rockstar in his prime", "youtube_id": "lhvPA8yfr0U",
    }]


def test_identifying_tokens_capture_names_and_video_ids():
    tokens = gate.identifying_tokens(_records())
    assert "someartist" in tokens
    assert "rockstar" in tokens
    assert "lhvpa8yfr0u" in tokens


def test_generic_audio_vocabulary_is_not_an_identifier():
    tokens = gate.identifying_tokens(_records())
    for word in ("studio", "acapella", "vocal", "raw", "wet", "master"):
        assert word not in tokens, f"{word!r} would cause false anonymization failures"


def test_malformed_video_id_is_not_treated_as_an_identifier():
    """The registrar mis-parses some ids; a bad parse must not fail the gate."""
    recs = [{"filename": "x.mp3", "youtube_id": "STUDIO"}]
    assert "studio" not in gate.identifying_tokens(recs)


def test_gate_detects_a_planted_leak(tmp_path, monkeypatch):
    leaked = tmp_path / "leaky.md"
    leaked.write_text("Results for Rockstar In His Prime look good.", encoding="utf-8")
    clean = tmp_path / "clean.md"
    clean.write_text("Results for P-01 look good.", encoding="utf-8")

    manifest = tmp_path / "manifest.json"
    import json
    manifest.write_text(json.dumps({"files": _records()}), encoding="utf-8")
    monkeypatch.setattr(gate, "MANIFEST", manifest)
    monkeypatch.setattr(gate, "REPO", tmp_path)

    monkeypatch.setattr(gate, "GUARDED", ("leaky.md",))
    assert gate.main() == 1, "gate failed to detect a planted title leak"

    monkeypatch.setattr(gate, "GUARDED", ("clean.md",))
    assert gate.main() == 0


def test_gate_skips_when_manifest_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "MANIFEST", tmp_path / "missing.json")
    assert gate.main() == 0        # CI has no manifest; skip, do not fail
