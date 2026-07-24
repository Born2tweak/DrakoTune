"""DT-55A — private-corpus registration (manifest only; no audio decode).

Verifies fail-closed rights classification (leaked / AI-isolated rejected even
though the rest is merely blocked), duplicate detection, filename-hint parsing,
and that the ingestion validator refuses manifest records (consent_ref null).
"""
from __future__ import annotations

from pathlib import Path

from scripts.register_private_corpus import build_manifest, classify, parse_name
from src.acquisition import ingestion_valid


def _mk(folder: Path, name: str, content: bytes) -> None:
    (folder / name).write_bytes(content)


def _fixture_folder(tmp_path: Path) -> Path:
    _mk(tmp_path, "01 - Artist - Song One (RAW ACAPELLA) NO AUTOTUNE [abc123XYZ_].mp3", b"raw-one")
    _mk(tmp_path, "02 - Artist - Song One (STUDIO ACAPELLA) [def456UVW-].mp3", b"wet-one")
    _mk(tmp_path, "03 - Other - Tune (LEAKED ACAPELLA) [ghi789RST_].mp3", b"leak")
    _mk(tmp_path, "04 - Other - Tune ( AI Isolated Vocals) Acapella [jkl012OPQ-].mp3", b"ai-iso")
    _mk(tmp_path, "05 - Artist - Song Two (RAW ACAPELLA) NO AUTOTUNE [mno345LMN_].mp3", b"raw-two")
    _mk(tmp_path, "06 - Artist - Song Two (RAW ACAPELLA) NO AUTOTUNE [mno345LMN_] copy.mp3", b"raw-two")  # dup bytes
    return tmp_path


def test_leaked_and_ai_isolated_rejected_permanently():
    assert classify("X (LEAKED ACAPELLA).mp3") == "rejected_leaked"
    assert classify("Y ( AI Isolated Vocals) Vocals.mp3") == "rejected_ai_isolated_wet"
    assert classify("Z (RAW ACAPELLA).mp3") == "blocked_pending_H1D"


def test_manifest_classifies_and_detects_duplicates(tmp_path):
    m = build_manifest(_fixture_folder(tmp_path))
    by_name = {r["filename"]: r for r in m["files"]}
    assert by_name["03 - Other - Tune (LEAKED ACAPELLA) [ghi789RST_].mp3"]["rights_class"] == "rejected_leaked"
    assert by_name["04 - Other - Tune ( AI Isolated Vocals) Acapella [jkl012OPQ-].mp3"]["rights_class"] == "rejected_ai_isolated_wet"
    dup = by_name["06 - Artist - Song Two (RAW ACAPELLA) NO AUTOTUNE [mno345LMN_] copy.mp3"]
    assert dup["rights_class"] == "duplicate"
    assert dup["duplicate_of"].startswith("05 -")
    # everything else fail-closed blocked
    assert by_name["01 - Artist - Song One (RAW ACAPELLA) NO AUTOTUNE [abc123XYZ_].mp3"]["rights_class"] == "blocked_pending_H1D"


def test_candidate_pair_grouping_excludes_rejected_and_duplicates(tmp_path):
    m = build_manifest(_fixture_folder(tmp_path))
    groups = m["candidate_pair_groups"]
    assert "song one" in groups and len(groups["song one"]) == 2
    # 'tune' had only rejected members -> no group; song two lost its dup -> single -> no group
    assert "tune" not in groups
    assert "song two" not in groups


def test_filename_parsing_hints():
    p = parse_name("07 - Juice WRLD - Lucid Dreams (RAW ACAPELLA) NO AUTOTUNE [l0AnQrTNEAo].mp3")
    assert p["artist_hint"] == "Juice WRLD"
    assert p["pair_key_hint"] == "lucid dreams"
    assert p["role_hint"] == "raw"
    assert p["youtube_id"] == "l0AnQrTNEAo"


def test_approval_never_flips_rejected_classes(tmp_path):
    """--approve (H1-D/D-029) upgrades blocked files but leaked/AI stay rejected."""
    m = build_manifest(_fixture_folder(tmp_path), approve_ref="D-029")
    by_name = {r["filename"]: r for r in m["files"]}
    ok = by_name["01 - Artist - Song One (RAW ACAPELLA) NO AUTOTUNE [abc123XYZ_].mp3"]
    assert ok["rights_class"] == "approved_local_internal_eval"
    assert ok["consent_ref"] == "D-029"
    assert by_name["03 - Other - Tune (LEAKED ACAPELLA) [ghi789RST_].mp3"]["rights_class"] == "rejected_leaked"
    assert by_name["04 - Other - Tune ( AI Isolated Vocals) Acapella [jkl012OPQ-].mp3"]["rights_class"] == "rejected_ai_isolated_wet"
    assert by_name["03 - Other - Tune (LEAKED ACAPELLA) [ghi789RST_].mp3"]["consent_ref"] is None


def test_ingestion_validator_refuses_manifest_records(tmp_path):
    """The fail-closed bridge: consent_ref is null until H1-D, so ingestion fails."""
    m = build_manifest(_fixture_folder(tmp_path))
    rec = m["files"][0]
    issues = ingestion_valid({
        "asset_id": rec["filename"], "source_dataset": "private_corpus",
        "license": "unverified", "sha256": rec["sha256"],
        "permitted_use": [], "consent_ref": rec["consent_ref"],
    })
    assert any("consent_ref" in i for i in issues)
