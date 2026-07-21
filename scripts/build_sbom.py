"""Generate the software bill of materials and environment fingerprint (DT-50).

Captures, for the current interpreter, the pinned dependency closure with
versions and licenses, plus the runtime fingerprint (Python, platform, and the
external FFmpeg build/configuration/license) so a test or render result — and a
later desktop build — can be reconstructed and audited.

Run:  python scripts/build_sbom.py

This records facts only. It does **not** accept any license obligation or
distribution posture — that is a human-only gate (DT-51). The FFmpeg build here
is GPL (`--enable-gpl --enable-version3`); that fact is captured, not resolved.
"""

import hashlib
import importlib.metadata as md
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

TOOLING_DIR = Path(__file__).resolve().parents[1] / "AURELIAN" / "08_TOOLING"

# Direct dependencies declared in pyproject (runtime + optional groups).
_DIRECT = [
    "pedalboard", "numpy", "soundfile", "librosa", "pyloudnorm",
    "pytest", "scipy", "httpx",
    "fastapi", "uvicorn", "python-multipart",
]


def _license_of(dist: md.Distribution) -> str:
    meta = dist.metadata
    expr = meta.get("License-Expression")
    if expr:
        return expr
    classifiers = [c for c in meta.get_all("Classifier") or [] if c.startswith("License ::")]
    if classifiers:
        return "; ".join(c.split("::")[-1].strip() for c in classifiers)
    lic = meta.get("License")
    return (lic.strip().splitlines()[0] if lic else "UNKNOWN")[:120]


def _installed_closure() -> list[dict]:
    out = []
    for dist in sorted(md.distributions(), key=lambda d: (d.metadata.get("Name") or "").lower()):
        name = dist.metadata.get("Name")
        if not name:
            continue
        out.append({
            "name": name,
            "version": dist.version,
            "license": _license_of(dist),
            "direct": name.lower() in {d.lower() for d in _DIRECT},
        })
    return out


def _ffmpeg_fingerprint() -> dict:
    try:
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=20)
        text = res.stdout
    except (FileNotFoundError, subprocess.SubprocessError):
        return {"present": False, "note": "ffmpeg not found on PATH"}
    version = ""
    m = re.search(r"ffmpeg version (\S+)", text)
    if m:
        version = m.group(1)
    config = ""
    mc = re.search(r"configuration:(.*)", text)
    if mc:
        config = mc.group(1).strip()
    gpl = "--enable-gpl" in config
    version3 = "--enable-version3" in config
    return {
        "present": True,
        "version": version,
        "configuration": config,
        "gpl": gpl,
        "version3": version3,
        "effective_license": (
            "GPL-3.0-or-later" if (gpl and version3) else "GPL-2.0-or-later" if gpl else "LGPL/other"
        ),
        "configuration_sha256": hashlib.sha256(config.encode("utf-8")).hexdigest(),
    }


def build_sbom() -> dict:
    closure = _installed_closure()
    return {
        "schema": "drakotune.sbom",
        "schema_version": "1.0.0",
        "generated_for_milestone": "DT-50",
        "runtime": {
            "python_version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "external_tools": {"ffmpeg": _ffmpeg_fingerprint()},
        "direct_dependencies": [c for c in closure if c["direct"]],
        "full_closure_count": len(closure),
        "full_closure": closure,
    }


def content_hash(payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()


def main() -> None:
    TOOLING_DIR.mkdir(parents=True, exist_ok=True)
    sbom = build_sbom()
    sbom_path = TOOLING_DIR / "sbom.json"
    sbom_path.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    fingerprint = {
        "schema": "drakotune.build_fingerprint",
        "schema_version": "1.0.0",
        "runtime": sbom["runtime"],
        "ffmpeg": sbom["external_tools"]["ffmpeg"],
        "direct_dependency_versions": {
            d["name"]: d["version"] for d in sbom["direct_dependencies"]
        },
        "sbom_content_hash": content_hash(sbom),
    }
    (TOOLING_DIR / "env_fingerprint.json").write_text(
        json.dumps(fingerprint, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote sbom ({sbom['full_closure_count']} pkgs) + fingerprint to {TOOLING_DIR}")
    print(f"ffmpeg effective license: {sbom['external_tools']['ffmpeg'].get('effective_license')}")


if __name__ == "__main__":
    main()
