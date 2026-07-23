"""Tests for the anti-drift roadmap checks (A3, 2026-07-23 reconciliation).

Stdlib-only (no PyYAML) so the check adds no CI dependency. Synthetic registries
are written in the same flow-style the real registry uses.
"""
from __future__ import annotations

from pathlib import Path

from scripts.check_roadmap_drift import _is_admin, _is_core, check, parse_milestones

REGISTRY = (
    Path(__file__).resolve().parent.parent
    / "AURELIAN" / "05_ROADMAP" / "MILESTONE_REGISTRY.yaml"
)


def _write(tmp_path, *lines: str) -> Path:
    body = "milestones:\n" + "\n".join(lines) + "\n"
    p = tmp_path / "reg.yaml"
    p.write_text(body, encoding="utf-8")
    return p


def test_current_registry_passes_drift_check():
    """The real registry must have no drift/traceability violations."""
    assert check() == []


def test_parser_reads_real_registry():
    ms = parse_milestones(REGISTRY.read_text(encoding="utf-8"))
    ids = {m["id"] for m in ms}
    assert "DT-54" in ids and "DT-45" in ids
    dt54 = next(m for m in ms if m["id"] == "DT-54")
    assert dt54["status"] == "complete" and dt54["has_detail"]


def test_core_and_admin_classification():
    assert _is_core("Target-Genre and Recording Strata Taxonomy")
    assert _is_core("Professional Engineer Pilot")
    assert _is_admin("Desktop Distribution Branch Decision")
    assert _is_admin("Reproducible Environment and SBOM")
    assert _is_admin("Integrated Security Privacy License and Claim Audit")


def test_drift_detected_when_ready_frontier_is_admin_only(tmp_path):
    p = _write(
        tmp_path,
        "  - {id: X-01, title: Desktop Distribution Branch Decision, status: ready, detail: d.md}",
        "  - {id: X-02, title: Champion DSP Improvement, status: blocked, detail: d.md}",
    )
    assert any("DRIFT" in v for v in check(p))


def test_no_drift_when_core_milestone_ready(tmp_path):
    p = _write(
        tmp_path,
        "  - {id: X-01, title: Desktop Distribution Branch Decision, status: ready, detail: d.md}",
        "  - {id: X-02, title: Vocal Loudness Treatment, status: ready, detail: d.md}",
    )
    assert check(p) == []


def test_dangling_human_gate_on_complete_is_flagged(tmp_path):
    p = _write(
        tmp_path,
        '  - {id: X-01, title: Vocal Cleanup, status: complete, detail: d.md, human_gate_remaining: "x"}',
    )
    assert any("dangling" in v for v in check(p))


def test_missing_detail_pointer_is_flagged(tmp_path):
    p = _write(tmp_path, "  - {id: X-01, title: Vocal Cleanup, status: ready}")
    assert any("traceability" in v for v in check(p))
