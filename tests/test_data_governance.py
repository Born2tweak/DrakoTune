"""Dataset-governance guards (M21).

Enforces docs/data/DATASET_GOVERNANCE.md: manifests validate against the
schema, no audio is tracked outside fixtures/, no oversized files enter git,
and tier/CI-use consistency holds across all manifests. No network access.
"""

import json
import subprocess
from pathlib import Path

import pytest

from src.data_governance import (
    DATASET_MANIFEST_VERSION,
    load_all_manifests,
    load_manifest,
    validate_manifest,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = REPO_ROOT / "data" / "manifests"

AUDIO_EXTENSIONS = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aif", ".aiff")
MAX_TRACKED_FILE_BYTES = 1_000_000
OVERSIZE_ALLOWLIST: set[str] = set()  # repo-relative paths; currently empty


def _git_tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


# --- Manifest schema -------------------------------------------------------

def test_manifest_dir_exists_and_not_empty():
    manifests = sorted(MANIFEST_DIR.glob("*.json"))
    assert manifests, "data/manifests/ must contain at least one manifest"


def test_all_manifests_validate():
    for path in sorted(MANIFEST_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        violations = validate_manifest(raw)
        assert not violations, f"{path.name}: {violations}"
        manifest = load_manifest(path)  # also exercises dataclass construction
        assert manifest.id == path.stem, f"{path.name}: id must match filename"
        assert manifest.version == DATASET_MANIFEST_VERSION


def test_expected_datasets_present_with_expected_tiers():
    tiers = {m.id: m.tier for m in load_all_manifests(MANIFEST_DIR)}
    expected = {
        "vocalset": "A", "vocadito": "A", "voicebank_demand": "A",
        "musan": "A", "openslr28_rir": "A",
        "singverse": "B", "damp": "B", "cambridge_mt": "C",
    }
    for dataset_id, tier in expected.items():
        assert tiers.get(dataset_id) == tier, f"{dataset_id}: expected tier {tier}, got {tiers.get(dataset_id)}"


def test_tier_ci_consistency_across_manifests():
    for m in load_all_manifests(MANIFEST_DIR):
        if m.allowed_ci_use:
            assert m.tier == "A", f"{m.id}: CI use requires Tier A"
        if m.tier in ("B", "C", "D"):
            assert m.commercial_use != "yes", f"{m.id}: non-A tier cannot claim commercial use"
        # Nothing is downloaded yet in M21: checksums/local paths must be unset.
        if m.checksum is not None:
            assert m.local_path is not None, f"{m.id}: checksum without local_path"


def test_validator_rejects_bad_manifests():
    good = json.loads((MANIFEST_DIR / "vocalset.json").read_text(encoding="utf-8"))

    missing = {k: v for k, v in good.items() if k != "license"}
    assert any("missing key: license" in v for v in validate_manifest(missing))

    bad_tier = dict(good, tier="X")
    assert any("invalid tier" in v for v in validate_manifest(bad_tier))

    ci_on_b = dict(good, tier="B", commercial_use="no", allowed_ci_use=True)
    assert any("allowed_ci_use" in v for v in validate_manifest(ci_on_b))

    bad_checksum = dict(good, checksum="not-a-sha")
    assert any("checksum" in v for v in validate_manifest(bad_checksum))

    escaping_path = dict(good, local_path="C:/somewhere/else")
    assert any("local_path" in v for v in validate_manifest(escaping_path))


# --- Git-index guards ------------------------------------------------------

@pytest.fixture(scope="module")
def tracked_files():
    try:
        return _git_tracked_files()
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git not available")


def test_no_tracked_audio_outside_fixtures(tracked_files):
    offenders = [
        f for f in tracked_files
        if f.lower().endswith(AUDIO_EXTENSIONS) and not f.startswith("fixtures/")
    ]
    assert not offenders, f"audio files tracked outside fixtures/: {offenders}"


def test_no_oversized_tracked_files(tracked_files):
    offenders = []
    for f in tracked_files:
        if f in OVERSIZE_ALLOWLIST:
            continue
        path = REPO_ROOT / f
        if path.is_file() and path.stat().st_size > MAX_TRACKED_FILE_BYTES:
            offenders.append((f, path.stat().st_size))
    assert not offenders, f"tracked files exceed {MAX_TRACKED_FILE_BYTES} bytes: {offenders}"


def test_data_audio_dirs_are_gitignored():
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    for entry in ("data/local/", "data/restricted/", "data/derived/"):
        assert entry in gitignore, f".gitignore missing {entry}"
