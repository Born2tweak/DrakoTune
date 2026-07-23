"""Lightweight anti-drift checks over the milestone registry (A3, 2026-07-23).

Guards against the failure the 2026-07-23 reconciliation diagnosed: a roadmap that
keeps completing governance/admin work while never advancing audio/product. These
are CHECKS over the existing registry, not a new governance plane.

Check 1 (core-work floor): if the actionable `ready` frontier is non-empty, at
least one ready milestone must be core (audio/DSP/product/usability), not purely
administrative — otherwise the frontier has drifted.

Check 2 (mission-traceability): every milestone names a contract (`detail:`), and
every milestone marked `complete` that carried a human gate records how the gate
was resolved (`human_gate_status`), never a dangling `human_gate_remaining`.

Exit 0 = pass, 1 = drift/violation. Usage: python scripts/check_roadmap_drift.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "AURELIAN" / "05_ROADMAP" / "MILESTONE_REGISTRY.yaml"

# A milestone is "core" (advances audio/product/user value) if its title matches.
CORE_KEYWORDS = (
    "audio", "dsp", "vocal", "listening", "mixing", "mastering", "loudness",
    "champion", "taxonomy", "corpus", "usability", "hardware", "performance",
    "quality", "defect", "treatment", "genre", "strata", "calibration",
    "acquisition", "protocol", "pilot", "project", "application service",
    "import", "render", "audition", "export",
)
# Purely administrative milestones (do not by themselves satisfy the core floor).
ADMIN_KEYWORDS = (
    "license", "distribution branch", "sbom", "reproducible environment",
    "security", "claim", "evidence semantics", "provenance", "rights",
    "audit", "packaging",
)


def _is_core(title: str) -> bool:
    t = title.lower()
    if any(k in t for k in CORE_KEYWORDS):
        return True
    return False


def _is_admin(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in ADMIN_KEYWORDS) and not _is_core(title)


def check(registry_path: Path = REGISTRY) -> list[str]:
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    milestones = data["milestones"]
    violations: list[str] = []

    # Check 1: core-work floor.
    ready = [m for m in milestones if m.get("status") == "ready"]
    if ready:
        core_ready = [m for m in ready if _is_core(m["title"])]
        if not core_ready:
            admin_only = ", ".join(f"{m['id']}({m['title']})" for m in ready)
            violations.append(
                "DRIFT: the ready frontier contains no core audio/product milestone; "
                f"it is administrative-only: {admin_only}"
            )

    # Check 2: mission-traceability.
    for m in milestones:
        if "detail" not in m:
            violations.append(f"{m['id']}: missing `detail:` contract pointer (traceability)")
        if m.get("status") == "complete" and "human_gate_remaining" in m:
            violations.append(
                f"{m['id']}: marked complete but still has a dangling `human_gate_remaining`; "
                "record `human_gate_status` instead"
            )
    return violations


def main() -> int:
    violations = check()
    if violations:
        print("Roadmap drift check FAILED:")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("Roadmap drift check OK: core frontier present; traceability intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
