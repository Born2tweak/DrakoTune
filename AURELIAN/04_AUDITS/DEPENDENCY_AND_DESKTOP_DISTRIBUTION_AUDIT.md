# Dependency and Desktop Distribution Audit

**Verdict:** no public desktop binary is presently authorized.

## Baseline dependency posture

`pyproject.toml` uses minimum versions without a lockfile. A fresh 2026-07-21 install therefore resolves current packages, not a reproducible historical set. Native audio behavior also depends on the external FFmpeg binary/configuration. CI installs current FFmpeg and Python dependencies each run.

## Material obligations and ambiguity

| Component | Observed posture | Distribution issue |
|---|---|---|
| Repository code | No top-level license; README says all rights reserved | Cannot casually publish as GPL-compatible source without owner/IP decision. |
| Pedalboard | GPL-3.0 | Current DSP runtime may impose GPL-compatible application distribution. |
| FFmpeg | LGPL base, GPL when configured accordingly | Audited binary has `--enable-gpl`; exact codecs/config must be controlled. |
| PySide6/Qt candidate | LGPLv3/GPLv3 or commercial | Linking, relinking, notices, source, platform packaging require review. |
| PyInstaller candidate | Packaging tool | Does not change bundled-component obligations. |
| Future models/weights | Component-specific | Code, weights, training data, and runtime assets need separate rights. |

## Mandatory decision

Before freezing the desktop stack, choose and document one branch: GPL-compatible open source, replacement/permissive DSP, or hosted-only. Counsel reviews the actual proposed bundle, not an abstract dependency list.

## Reproducibility and release gates

- Lock Python and native dependencies per platform.
- Build or source a known FFmpeg configuration and retain configuration/license output.
- Generate SBOM, license/notice bundle, hashes, build provenance, and source-offer artifacts where applicable.
- Run clean-machine install, launch, process, update, rollback, and uninstall tests.
- Sign/notarize installers and updates; protect signing credentials outside the repository.
- Scan dependency vulnerabilities/advisories and define a supported-version window.

Internal source execution may continue while the branch is decided; public binary distribution may not.
