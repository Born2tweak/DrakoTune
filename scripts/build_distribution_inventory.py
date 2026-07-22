"""Generate the DT-51 distribution obligation inventory from the SBOM.

Reads the DT-50 SBOM and writes a machine-readable component-level copyleft
inventory + three-branch comparison to
``AURELIAN/08_TOOLING/distribution_obligations.json``.

This is autonomous analysis only (DT-51 Field 15 *Automatic*). It selects no
distribution branch; the recommendation it emits is explicitly non-binding.

Usage: ``PYTHONPATH=. python scripts/build_distribution_inventory.py``
"""

import json
from pathlib import Path

from src.tooling.license_policy import component_obligations, distribution_scenarios

ROOT = Path(__file__).resolve().parents[1]
SBOM_PATH = ROOT / "AURELIAN" / "08_TOOLING" / "sbom.json"
OUT_PATH = ROOT / "AURELIAN" / "08_TOOLING" / "distribution_obligations.json"


def build(sbom: dict) -> dict:
    return {
        "schema": "drakotune.distribution_obligations",
        "schema_version": "1.0.0",
        "generated_for_milestone": "DT-51 (autonomous inventory; decision human-gated)",
        "source_sbom": "AURELIAN/08_TOOLING/sbom.json",
        "components": component_obligations(sbom),
        **distribution_scenarios(sbom),
    }


def main() -> int:
    sbom = json.loads(SBOM_PATH.read_text(encoding="utf-8"))
    inventory = build(sbom)
    OUT_PATH.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    strong = inventory["summary"]["strong_copyleft"]
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"strong-copyleft runtime components: {strong or 'none'}")
    print(f"recommended reversible default: {inventory['recommendation']['suggested_reversible_default']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
