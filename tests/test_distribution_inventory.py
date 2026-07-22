"""DT-51 — Distribution obligation inventory (autonomous portion).

Field 14 (SBOM scenario diff + license-policy checks where machine-testable) and
Field 16 adversarial cases (transitive GPL, proprietary asset, alternate FFmpeg
build, model weights, updater bundling — represented as classification cases).
Verifies the classifier and the three-branch comparison against synthetic SBOMs
and the real committed SBOM. Makes no distribution decision.
"""

import json
from pathlib import Path

import pytest

from src.tooling.license_policy import (
    BRANCHES,
    CopyleftStrength,
    classify_license,
    component_obligations,
    distribution_scenarios,
)

ROOT = Path(__file__).resolve().parents[1]
SBOM_PATH = ROOT / "AURELIAN" / "08_TOOLING" / "sbom.json"


# -- classifier ------------------------------------------------------------

@pytest.mark.parametrize("lic,expected", [
    ("MIT", CopyleftStrength.PERMISSIVE),
    ("BSD-3-Clause", CopyleftStrength.PERMISSIVE),
    ("Apache-2.0", CopyleftStrength.PERMISSIVE),
    ("ISC License (ISCL)", CopyleftStrength.PERMISSIVE),
    ("BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0", CopyleftStrength.PERMISSIVE),
    ("GNU General Public License v3 (GPLv3)", CopyleftStrength.STRONG),
    ("GPL-3.0-or-later", CopyleftStrength.STRONG),
    ("AGPL-3.0", CopyleftStrength.STRONG),
    ("LGPL-3.0-only", CopyleftStrength.WEAK),
    ("LGPL-2.1-or-later", CopyleftStrength.WEAK),
    ("Mozilla Public License 2.0 (MPL 2.0)", CopyleftStrength.WEAK),
    ("MPL-2.0 AND MIT", CopyleftStrength.WEAK),
    ("", CopyleftStrength.UNKNOWN),
    (None, CopyleftStrength.UNKNOWN),
    ("Some-Bespoke-Proprietary-EULA", CopyleftStrength.UNKNOWN),
])
def test_classify_license(lic, expected):
    assert classify_license(lic) is expected


def test_lgpl_not_misread_as_strong_gpl():
    """Adversarial: LGPL must be weak, never caught by the GPL strong test."""
    assert classify_license("LGPL-3.0-only") is CopyleftStrength.WEAK


# -- synthetic SBOM scenarios ----------------------------------------------

def _sbom(deps, ffmpeg_license="GPL-3.0-or-later"):
    return {
        "direct_dependencies": [
            {"name": n, "version": "1.0", "license": lic} for n, lic in deps
        ],
        "external_tools": {
            "ffmpeg": {"present": True, "version": "8.x", "effective_license": ffmpeg_license},
        },
    }


def test_strong_copyleft_blocks_permissive_binary_not_hosted():
    sb = _sbom([("pedalboard", "GPLv3"), ("numpy", "BSD-3-Clause")])
    scen = distribution_scenarios(sb)
    assert scen["scenarios"]["permissive_custom_dsp"]["viable"] is False
    assert "pedalboard" in scen["scenarios"]["permissive_custom_dsp"]["blocked_by"]
    assert "ffmpeg" in scen["scenarios"]["permissive_custom_dsp"]["blocked_by"]
    # GPL-compatible OSS and hosted-only remain viable
    assert scen["scenarios"]["gpl_compatible_oss"]["viable"] is True
    assert scen["scenarios"]["hosted_only"]["viable"] is True
    assert scen["scenarios"]["hosted_only"]["reversible"] is True


def test_permissive_only_makes_permissive_binary_viable():
    sb = _sbom([("numpy", "BSD-3-Clause"), ("fastapi", "MIT")], ffmpeg_license="LGPL-2.1")
    scen = distribution_scenarios(sb)
    # No strong copyleft => permissive binary viable, nothing blocks it
    assert scen["scenarios"]["permissive_custom_dsp"]["viable"] is True
    assert scen["scenarios"]["permissive_custom_dsp"]["blocked_by"] == []


def test_unknown_license_blocks_permissive_binary():
    """Adversarial: an unrecognized/proprietary component blocks until reviewed."""
    sb = _sbom([("mystery_model_weights", "Some-Bespoke-EULA")])
    obligations = component_obligations(sb)
    weights = next(c for c in obligations if c["name"] == "mystery_model_weights")
    assert weights["copyleft"] == "unknown"
    assert weights["blocks_permissive_binary"] is True


def test_recommendation_is_nonbinding_and_names_human_gate():
    sb = _sbom([("pedalboard", "GPLv3")])
    rec = distribution_scenarios(sb)["recommendation"]
    assert rec["suggested_reversible_default"] == "hosted_only"
    assert "gpl_compatible_oss" in rec["requires_human_gate"]
    assert "permissive_custom_dsp" in rec["requires_human_gate"]
    assert "RECOMMENDATION ONLY" in rec["note"]


def test_branches_constant_is_the_three_dt51_options():
    assert set(BRANCHES) == {"gpl_compatible_oss", "permissive_custom_dsp", "hosted_only"}


# -- against the real committed SBOM ---------------------------------------

def test_real_sbom_flags_pedalboard_and_ffmpeg_as_strong():
    sbom = json.loads(SBOM_PATH.read_text(encoding="utf-8"))
    scen = distribution_scenarios(sbom)
    strong = set(scen["summary"]["strong_copyleft"])
    assert "pedalboard" in strong
    assert "ffmpeg" in strong
    # therefore the permissive-binary branch is not viable as-is
    assert scen["scenarios"]["permissive_custom_dsp"]["viable"] is False
