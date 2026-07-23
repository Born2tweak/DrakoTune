"""Tests for the anti-drift roadmap checks (A3, 2026-07-23 reconciliation)."""
from __future__ import annotations

from pathlib import Path

import yaml

from scripts.check_roadmap_drift import _is_admin, _is_core, check

REGISTRY = (
    Path(__file__).resolve().parent.parent
    / "AURELIAN" / "05_ROADMAP" / "MILESTONE_REGISTRY.yaml"
)


def test_current_registry_passes_drift_check():
    """The real registry must have no drift/traceability violations."""
    assert check() == []


def test_core_and_admin_classification():
    assert _is_core("Target-Genre and Recording Strata Taxonomy")
    assert _is_core("Professional Engineer Pilot")
    assert _is_admin("Desktop Distribution Branch Decision")
    assert _is_admin("Reproducible Environment and SBOM")
    assert _is_admin("Integrated Security Privacy License and Claim Audit")


def test_drift_detected_when_ready_frontier_is_admin_only(tmp_path):
    """Synthetic registry whose only ready milestone is administrative -> DRIFT."""
    reg = {
        "milestones": [
            {"id": "X-01", "title": "Desktop Distribution Branch Decision",
             "status": "ready", "detail": "d.md"},
            {"id": "X-02", "title": "Champion DSP Improvement",
             "status": "blocked", "detail": "d.md"},
        ]
    }
    p = tmp_path / "reg.yaml"
    p.write_text(yaml.safe_dump(reg), encoding="utf-8")
    violations = check(p)
    assert any("DRIFT" in v for v in violations)


def test_dangling_human_gate_on_complete_is_flagged(tmp_path):
    reg = {
        "milestones": [
            {"id": "X-01", "title": "Vocal Cleanup", "status": "complete",
             "detail": "d.md", "human_gate_remaining": "something"},
        ]
    }
    p = tmp_path / "reg.yaml"
    p.write_text(yaml.safe_dump(reg), encoding="utf-8")
    violations = check(p)
    assert any("dangling" in v for v in violations)


def test_missing_detail_pointer_is_flagged(tmp_path):
    reg = {"milestones": [{"id": "X-01", "title": "Vocal Cleanup", "status": "ready"}]}
    p = tmp_path / "reg.yaml"
    p.write_text(yaml.safe_dump(reg), encoding="utf-8")
    violations = check(p)
    assert any("traceability" in v for v in violations)
