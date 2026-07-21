"""DT-50 reproducible-environment and SBOM suite.

Acceptance (Field 13): the SBOM/fingerprint are well formed, every direct
dependency is pinned and lock-consistent, and the external FFmpeg config/license
is captured. The "two clean environments resolve identical artifacts" criterion
is exercised by CI (`.github/workflows/ci.yml`), not by this in-process suite.
"""

from src.tooling import (
    ffmpeg_license,
    load_lock,
    load_sbom,
    validate_sbom,
)
from src.tooling.sbom_check import REQUIRED_DIRECT


def test_sbom_and_fingerprint_exist_and_parse():
    sbom = load_sbom()
    assert sbom["schema"] == "drakotune.sbom"
    assert sbom["runtime"]["python_version"]
    assert sbom["full_closure_count"] >= len(REQUIRED_DIRECT)


def test_sbom_validates_against_lock():
    sbom = load_sbom()
    lock = load_lock()
    problems = validate_sbom(sbom, lock)
    assert problems == [], problems


def test_all_direct_dependencies_pinned_and_locked():
    sbom = load_sbom()
    lock = load_lock()
    names = {d["name"].lower().replace("_", "-") for d in sbom["direct_dependencies"]}
    for dep in REQUIRED_DIRECT:
        key = dep.lower().replace("_", "-")
        assert key in names, f"{dep} missing from SBOM direct deps"
        assert key in lock, f"{dep} missing from lockfile"


def test_ffmpeg_license_is_captured_not_assumed():
    sbom = load_sbom()
    ff = sbom["external_tools"]["ffmpeg"]
    if ff.get("present"):
        # The captured build must state its effective license; GPL must not be
        # silently treated as permissive.
        assert ffmpeg_license(sbom)
        if ff.get("gpl"):
            assert "GPL" in ffmpeg_license(sbom)


def test_missing_direct_dependency_is_flagged():
    sbom = load_sbom()
    lock = load_lock()
    broken = dict(sbom)
    broken["direct_dependencies"] = [
        d for d in sbom["direct_dependencies"]
        if d["name"].lower() != "numpy"
    ]
    problems = validate_sbom(broken, lock)
    assert any("numpy" in p for p in problems)


def test_lock_version_mismatch_is_flagged():
    sbom = load_sbom()
    lock = dict(load_lock())
    lock["numpy"] = "0.0.0-not-real"
    problems = validate_sbom(sbom, lock)
    assert any(p.startswith("lock_version_mismatch:numpy") for p in problems)
