"""License copyleft classification and distribution-branch analysis (DT-51).

DT-51's *decision* — which distribution posture DrakoTune adopts — is a
human-only gate (product owner + qualified counsel). This module builds only the
Field-15 *Automatic* half: classify each dependency's copyleft strength from the
DT-50 SBOM, and mechanically compare the three candidate branches so a human has
a component-level obligation inventory and a (non-binding) recommendation.

Classification is deliberately conservative:

- **strong** copyleft (GPL/AGPL, not "lesser"): bundling into a single
  distributed work propagates the license to the whole work.
- **weak** copyleft (LGPL/MPL/EPL): file-/library-scoped obligations
  (notice + offer to modify the component) but does not relicense the whole app.
- **permissive** (MIT/BSD/ISC/Apache/Zlib/0BSD/CC0/PSF): attribution only.
- **unknown**: anything unrecognized — treated as blocking until reviewed.

This is a heuristic inventory to *inform* counsel, not a legal determination.
"""

from enum import Enum


class CopyleftStrength(str, Enum):
    STRONG = "strong"
    WEAK = "weak"
    PERMISSIVE = "permissive"
    UNKNOWN = "unknown"


_PERMISSIVE_TOKENS = (
    "MIT", "BSD", "ISC", "APACHE", "ZLIB", "0BSD", "CC0", "PSF", "PYTHON-2",
    "UNLICENSE", "WTFPL",
)


def classify_license(license_str: str | None) -> CopyleftStrength:
    """Classify one license string by copyleft strength (conservative)."""
    if not license_str:
        return CopyleftStrength.UNKNOWN
    s = license_str.upper()

    # Lesser/library and file-scoped copyleft first, so "LGPL" is not caught by
    # the "GPL" strong test below.
    if "LGPL" in s or "LESSER GENERAL PUBLIC" in s:
        return CopyleftStrength.WEAK
    if "MPL" in s or "MOZILLA PUBLIC" in s or "EPL" in s or "ECLIPSE PUBLIC" in s:
        # Mixed expressions like "MPL-2.0 AND MIT" are still file-scoped weak.
        return CopyleftStrength.WEAK

    if "AGPL" in s or "AFFERO" in s:
        return CopyleftStrength.STRONG
    if "GPL" in s or "GENERAL PUBLIC LICENSE" in s:
        return CopyleftStrength.STRONG

    # Permissive only if EVERY named token is permissive (a strong term anywhere
    # would have been caught above; this guards mixed permissive expressions).
    if any(tok in s for tok in _PERMISSIVE_TOKENS):
        return CopyleftStrength.PERMISSIVE

    return CopyleftStrength.UNKNOWN


def _runtime_components(sbom: dict) -> list[dict]:
    """Runtime-relevant components: direct deps + the FFmpeg external tool.

    Dev-only tooling in the full closure (e.g. a test/reporting helper) is not a
    distribution obligation for the shipped app, so the inventory is anchored on
    the declared runtime surface plus the FFmpeg binary that actually ships.
    """
    comps: list[dict] = []
    for d in sbom.get("direct_dependencies", []):
        comps.append({
            "name": d.get("name"),
            "version": d.get("version"),
            "license": d.get("license"),
            "kind": "python_dependency",
        })
    ff = sbom.get("external_tools", {}).get("ffmpeg")
    if ff and ff.get("present"):
        comps.append({
            "name": "ffmpeg",
            "version": ff.get("version"),
            "license": ff.get("effective_license"),
            "kind": "external_binary",
            "configuration": ff.get("configuration"),
        })
    return comps


def component_obligations(sbom: dict) -> list[dict]:
    """Per-component copyleft classification for the runtime surface."""
    out = []
    for c in _runtime_components(sbom):
        strength = classify_license(c.get("license"))
        out.append({
            **c,
            "copyleft": strength.value,
            "blocks_permissive_binary": strength in (
                CopyleftStrength.STRONG, CopyleftStrength.UNKNOWN
            ),
        })
    return out


# The three candidate distribution branches (DT-51 objective).
BRANCHES = ("gpl_compatible_oss", "permissive_custom_dsp", "hosted_only")


def distribution_scenarios(sbom: dict) -> dict:
    """Mechanically compare the three branches against the obligation inventory.

    Returns, for each branch: viability, the components that block it (if any),
    and the obligation a human/counsel must accept. No branch is *chosen*.
    """
    obligations = component_obligations(sbom)
    strong = [c for c in obligations if c["copyleft"] == "strong"]
    unknown = [c for c in obligations if c["copyleft"] == "unknown"]
    weak = [c for c in obligations if c["copyleft"] == "weak"]

    strong_names = sorted(c["name"] for c in strong)

    scenarios = {
        "gpl_compatible_oss": {
            "viable": True,
            "blocked_by": [],
            "obligation": (
                "Release the whole distributed work under GPL-3.0-or-later and "
                "provide corresponding source. Accepts every strong-copyleft "
                f"component as-is ({', '.join(strong_names) or 'none'})."
            ),
            "reversible": False,
        },
        "permissive_custom_dsp": {
            # Only viable if the strong-copyleft runtime components are replaced.
            "viable": len(strong) == 0,
            "blocked_by": strong_names,
            "obligation": (
                "Replace or re-implement every strong-copyleft runtime component "
                f"({', '.join(strong_names) or 'none'}) with permissive/original "
                "DSP before a permissive binary can ship."
            ),
            "reversible": False,
        },
        "hosted_only": {
            # Hosting is not "conveying" for GPL-3.0/LGPL/MPL (no AGPL present),
            # so strong-copyleft components do not trigger source-offer here.
            "viable": True,
            "blocked_by": [],
            "obligation": (
                "Serve over the network; do not distribute a binary. GPL/LGPL/MPL "
                "source-offer obligations are not triggered by hosting (no AGPL "
                "component is present). Keeps the binary branch decision open."
            ),
            "reversible": True,
        },
    }

    return {
        "summary": {
            "strong_copyleft": strong_names,
            "weak_copyleft": sorted(c["name"] for c in weak),
            "unknown": sorted(c["name"] for c in unknown),
        },
        "scenarios": scenarios,
        "recommendation": _recommend(scenarios),
    }


def _recommend(scenarios: dict) -> dict:
    """A non-binding recommendation. The decision remains a human gate."""
    return {
        "note": (
            "RECOMMENDATION ONLY — not a decision (DT-51 is a human product-owner "
            "+ counsel gate). Lowest-risk reversible near-term option is "
            "`hosted_only`: it ships value without accepting an irreversible "
            "license posture and keeps both binary branches open. The binary "
            "choice (gpl_compatible_oss vs permissive_custom_dsp) is the "
            "consequential, harder-to-reverse decision and should be made with "
            "counsel once product scope (DT-53) is fixed."
        ),
        "suggested_reversible_default": "hosted_only",
        "requires_human_gate": ["gpl_compatible_oss", "permissive_custom_dsp"],
    }
