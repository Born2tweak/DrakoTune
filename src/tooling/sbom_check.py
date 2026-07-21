"""SBOM and environment-fingerprint validation (DT-50).

Consumes the artifacts produced by ``scripts/build_sbom.py`` and checks the
invariants a reproducible-evidence gate needs: the SBOM schema is well formed,
every declared direct dependency is present and pinned in the lockfile, and the
external FFmpeg license is captured (not silently assumed permissive).

License *classification* is reported; accepting a license obligation or a
distribution posture is a human-only gate (DT-51) and is never done here.
"""

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
TOOLING_DIR = _ROOT / "AURELIAN" / "08_TOOLING"
SBOM_PATH = TOOLING_DIR / "sbom.json"
FINGERPRINT_PATH = TOOLING_DIR / "env_fingerprint.json"
LOCK_PATH = TOOLING_DIR / "requirements.lock"

REQUIRED_DIRECT = (
    "pedalboard", "numpy", "soundfile", "librosa", "pyloudnorm",
    "scipy", "httpx", "fastapi", "uvicorn", "python-multipart",
)


def load_sbom(path: Path = SBOM_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_lock(path: Path = LOCK_PATH) -> dict[str, str]:
    """Parse ``name==version`` lock lines into a normalized {name: version}."""
    pins: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, version = line.split("==", 1)
        pins[name.strip().lower().replace("_", "-")] = version.strip()
    return pins


def validate_sbom(sbom: dict, lock: dict[str, str]) -> list[str]:
    """Return a list of problems (empty = valid)."""
    problems: list[str] = []
    if sbom.get("schema") != "drakotune.sbom":
        problems.append("sbom.schema_missing_or_wrong")
    if not sbom.get("runtime", {}).get("python_version"):
        problems.append("sbom.runtime.python_version_missing")

    direct = {d["name"].lower().replace("_", "-"): d for d in sbom.get("direct_dependencies", [])}
    for dep in REQUIRED_DIRECT:
        key = dep.lower().replace("_", "-")
        if key not in direct:
            problems.append(f"direct_dependency_missing:{dep}")
            continue
        if not direct[key].get("version"):
            problems.append(f"direct_dependency_unpinned:{dep}")
        if key not in lock:
            problems.append(f"direct_dependency_not_in_lock:{dep}")
        elif direct[key]["version"] != lock[key]:
            problems.append(f"lock_version_mismatch:{dep}")

    ffmpeg = sbom.get("external_tools", {}).get("ffmpeg", {})
    if not ffmpeg:
        problems.append("ffmpeg_fingerprint_missing")
    elif ffmpeg.get("present") and not ffmpeg.get("effective_license"):
        problems.append("ffmpeg_license_not_captured")
    return problems


def ffmpeg_license(sbom: dict) -> str | None:
    return sbom.get("external_tools", {}).get("ffmpeg", {}).get("effective_license")
