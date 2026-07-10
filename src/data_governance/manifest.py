"""Dataset manifest schema and validator (M21).

Policy source: docs/data/DATASET_GOVERNANCE.md (ADR 0003). Every dataset that
may be brought near this repository has one JSON manifest in data/manifests/.
Manifests are metadata-only; raw audio is never committed. This module performs
no network access and never accepts a license on anyone's behalf.
"""

import json
import re
from dataclasses import dataclass, fields
from pathlib import Path

DATASET_MANIFEST_VERSION = "1.0.0"

VALID_TIERS = ("A", "B", "C", "D", "P")
VALID_COMMERCIAL_USE = ("yes", "no", "unclear")
VALID_DOWNLOAD_METHODS = ("direct", "zenodo-request", "email-agreement", "manual")

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class DatasetManifest:
    """One dataset's governance record. Unknown facts are None, never guessed."""

    id: str
    version: str                    # manifest schema version
    official_name: str
    official_url: str
    paper_url: str | None
    license: str
    tier: str                       # A | B | C | D | P (governance §1)
    commercial_use: str             # yes | no | unclear
    redistribution: bool
    registration_required: bool
    attribution_text: str | None
    download_method: str            # direct | zenodo-request | email-agreement | manual
    checksum: str | None            # sha256 of downloaded archive; null until downloaded
    file_count: int | None
    duration_hours: float | None
    sample_rate: int | None
    bit_depth: int | None
    channels: int | None
    vocal_type: str | None
    language: str | None
    genre: str | None
    recording_device: str | None
    clean_reference: bool
    defect_labels: str | None
    local_path: str | None          # null until downloaded; must be under data/
    preprocessing: str | None
    derived_fixtures: tuple = ()
    allowed_eval_use: str = ""
    allowed_ci_use: bool = False
    notes: str | None = None
    last_verified: str | None = None  # YYYY-MM-DD


_REQUIRED_KEYS = tuple(f.name for f in fields(DatasetManifest))


def validate_manifest(data: dict) -> list[str]:
    """Return human-readable violations; an empty list means valid."""
    violations: list[str] = []

    for key in _REQUIRED_KEYS:
        if key not in data:
            violations.append(f"missing key: {key}")
    if violations:
        return violations  # shape is wrong; further checks would be noise

    if data["version"] != DATASET_MANIFEST_VERSION:
        violations.append(
            f"version {data['version']!r} != schema {DATASET_MANIFEST_VERSION!r}"
        )
    if data["tier"] not in VALID_TIERS:
        violations.append(f"invalid tier: {data['tier']!r} (expected one of {VALID_TIERS})")
    if data["commercial_use"] not in VALID_COMMERCIAL_USE:
        violations.append(f"invalid commercial_use: {data['commercial_use']!r}")
    if data["download_method"] not in VALID_DOWNLOAD_METHODS:
        violations.append(f"invalid download_method: {data['download_method']!r}")

    # CI fixtures may derive only from Tier A data (governance §5).
    if data["allowed_ci_use"] and data["tier"] != "A":
        violations.append("allowed_ci_use is true but tier is not A (governance §5)")
    # Redistribution/commercial-use may not exceed what a non-A tier grants.
    if data["tier"] in ("B", "C", "D") and data["commercial_use"] == "yes":
        violations.append(f"tier {data['tier']} cannot declare commercial_use=yes")
    if data["tier"] == "D" and data["allowed_eval_use"] not in ("", "none"):
        violations.append("tier D datasets allow no evaluation use")

    checksum = data["checksum"]
    if checksum is not None and not _SHA256_RE.match(str(checksum)):
        violations.append("checksum must be null or a lowercase sha256 hex digest")

    local_path = data["local_path"]
    if local_path is not None and not str(local_path).replace("\\", "/").startswith("data/"):
        violations.append("local_path must be null or under data/")

    last_verified = data["last_verified"]
    if last_verified is not None and not _DATE_RE.match(str(last_verified)):
        violations.append("last_verified must be null or YYYY-MM-DD")

    for key in ("id", "official_name", "official_url", "license", "allowed_eval_use"):
        if not isinstance(data[key], str) or (key != "allowed_eval_use" and not data[key]):
            violations.append(f"{key} must be a non-empty string")

    for key in ("redistribution", "registration_required", "clean_reference", "allowed_ci_use"):
        if not isinstance(data[key], bool):
            violations.append(f"{key} must be a boolean")

    return violations


def load_manifest(path: str | Path) -> DatasetManifest:
    """Load and validate one manifest JSON. Raises ValueError on violations."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    violations = validate_manifest(raw)
    if violations:
        raise ValueError(f"invalid manifest {path}: " + "; ".join(violations))
    raw = dict(raw)
    raw["derived_fixtures"] = tuple(raw.get("derived_fixtures") or ())
    return DatasetManifest(**raw)


def load_all_manifests(directory: str | Path = "data/manifests") -> list[DatasetManifest]:
    """Load every *.json manifest in a directory (sorted for determinism)."""
    return [load_manifest(p) for p in sorted(Path(directory).glob("*.json"))]
