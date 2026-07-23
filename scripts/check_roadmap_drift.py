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

Stdlib-only (no PyYAML): milestone entries are flow-style one-line dicts, parsed
with a targeted reader so this check adds no dependency to CI. Exit 0 = pass,
1 = drift/violation. Usage: python scripts/check_roadmap_drift.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

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

# Matches a flow-style milestone entry line: `- {id: DT-54, title: ..., status: ...}`.
_MILESTONE_LINE = re.compile(r"-\s*\{id:\s*(?P<id>[A-Za-z]+-\d+)\s*,(?P<rest>.*)\}\s*$")


def _field(rest: str, key: str) -> str | None:
    """Extract a bareword/short value for `key` from a flow-dict body.

    Titles and statuses are comma/brace-free barewords here; quoted values (e.g.
    human_gate_remaining) are only tested for presence, not parsed.
    """
    m = re.search(rf"\b{re.escape(key)}:\s*(?P<v>[^,}}]+)", rest)
    return m.group("v").strip() if m else None


def parse_milestones(text: str) -> list[dict]:
    milestones: list[dict] = []
    for line in text.splitlines():
        m = _MILESTONE_LINE.search(line)
        if not m:
            continue
        rest = m.group("rest")
        milestones.append({
            "id": m.group("id"),
            "title": _field(rest, "title") or "",
            "status": _field(rest, "status") or "",
            "has_detail": bool(re.search(r"\bdetail:", rest)),
            "has_dangling_gate": bool(re.search(r"\bhuman_gate_remaining:", rest)),
        })
    return milestones


def _is_core(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in CORE_KEYWORDS)


def _is_admin(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in ADMIN_KEYWORDS) and not _is_core(title)


def check(registry_path: Path = REGISTRY) -> list[str]:
    milestones = parse_milestones(registry_path.read_text(encoding="utf-8"))
    violations: list[str] = []

    # Check 1: core-work floor.
    ready = [m for m in milestones if m["status"] == "ready"]
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
        if not m["has_detail"]:
            violations.append(f"{m['id']}: missing `detail:` contract pointer (traceability)")
        if m["status"] == "complete" and m["has_dangling_gate"]:
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
