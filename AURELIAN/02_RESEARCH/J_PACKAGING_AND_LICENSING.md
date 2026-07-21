# J — Packaging and Licensing Report

**As of:** 2026-07-21  
**Not legal advice. Sources:** S-L01–S-L04.

## Material findings

- Pedalboard is GPL-3.0. Its inclusion in a distributed desktop application may impose a GPL-compatible distribution posture; counsel must determine the exact obligations and architecture implications.
- FFmpeg is principally LGPL 2.1+ but becomes GPL when configured with GPL components. The audited machine reports `--enable-gpl`, so that binary is unsuitable as evidence for an LGPL-only distribution.
- PySide6/Qt offers LGPLv3/GPLv3 community and commercial routes with conditions. UI framework selection cannot be separated from distribution design.
- PyInstaller bundles applications but does not neutralize component licenses.
- The repository has no top-level `LICENSE`; the README currently says to treat code as all rights reserved. That is incompatible with casually promising a GPL open-source distribution.

## Decision branches

| Branch | Benefit | Cost/risk |
|---|---|---|
| GPL-compatible open-source desktop | Retains Pedalboard; fastest reuse | Requires project licensing decision, source/notice compliance, contributor/IP review. |
| Permissive/custom DSP desktop | Greater commercial flexibility | Reimplementation/revalidation cost; FFmpeg/Qt still require reviewed packaging. |
| Hosted-only | Avoids binary distribution for now | Conflicts with local-first privacy/UX goal; service obligations remain. |

## Required proof before binary distribution

Approved branch; complete dependency/asset/weights inventory; exact license texts; SBOM; reproducible platform build; FFmpeg component/config fingerprint; notices/source-offer process; signing/update plan; counsel sign-off; clean-machine installation/uninstall evidence.

## Component evidence audit

| Component/source | Recorded fact | Ambiguity or obligation risk | Decision effect | Recheck trigger |
|---|---|---|---|---|
| Repository | No top-level license; README instructs all-rights-reserved treatment. | Owner/IP/contributor authority must be established before adopting an open-source distribution license. | GPL-compatible branch cannot be selected casually. | Repository license/ownership decision. |
| S-L01 Pedalboard | Official repository declares GPL-3.0. | Distribution/linking consequences depend on the actual combined work and counsel’s interpretation. | Blocks public binary until DT-51; motivates `DspBackend` seam. | Version/license/architecture change. |
| S-L02 FFmpeg | Official materials describe LGPL base with GPL configuration/components; audited host reports `--enable-gpl`. | Package obligations depend on exact enabled codecs/libraries/build flags, not merely “FFmpeg.” | Build a controlled fingerprinted binary for the selected branch. | Every FFmpeg build/update. |
| S-L03 PySide6/Qt | Official documentation offers LGPLv3/GPLv3 community and commercial licensing routes. | Relinking, notices, source, plugins, and platform packaging must match chosen route. | Framework spike follows distribution decision, not vice versa. | Qt/PySide version/route change. |
| S-L04 PyInstaller | Packaging tool can create application bundles. | Packaging does not erase licenses of bundled code/native libraries/assets. | Treat as build tooling; inventory the final bundle. | Packager/version/build design change. |
| Future models/weights | Research repositories may separate code, weights, data, and runtime terms. | A permissive code license can coexist with restricted weights/data. | Component-level artifact registry and promotion block. | Every candidate/version. |

## Non-legal engineering conclusion

The fastest technically plausible route is not automatically the safest distribution route. DT-51 must compare an actual component graph and desired business posture. Until then, source-run internal desktop work can proceed behind replaceable interfaces, but no public binary promise should harden the wrong dependency architecture.

## Exact bundle-decision extraction

| Artifact | Verified snapshot | Distribution consequence to resolve | Required evidence before promotion |
|---|---|---|---|
| `pedalboard` | Project dependency is `pedalboard>=0.9`; the audited environment resolves 0.9.24. The official repository declares GPL-3.0. | A distributed combined desktop work may require a GPL-compatible posture; exact consequence is an owner/counsel decision, not an engineering assumption. | Locked version/hash, source and license text, native-library inventory, combined-work architecture, notices/source process, written branch decision. |
| FFmpeg | Official licensing is principally LGPL 2.1+ with GPL configuration/components. The host binary used during this audit reports `--enable-gpl`. | That host binary cannot substantiate a planned LGPL-only bundle. The shipped binary’s flags and linked libraries control the evidence. | Controlled build provenance, full `-buildconf`, component/license inventory, checksum, source/offer/notices plan, platform bundle scan. |
| PySide6/Qt | Official Qt for Python material provides LGPLv3/GPLv3 community and commercial routes. No route is selected. | Dynamic-linking/relinking, notices, source obligations, plugins, and platform deployment must match the chosen route or commercial agreement. | Exact Qt/PySide versions and modules, linkage/plugin graph, license route, relinking mechanism where required, notices/source materials, counsel/owner sign-off. |
| PyInstaller | Candidate bundler; its own licensing does not replace the licenses of Python packages, native libraries, codecs, models, assets, or Qt plugins placed in the bundle. | A successful executable build is not a distributable-rights decision. | Pinned packager/spec, reproducible build, complete file/SBOM diff, recursive license scan, clean-machine install/uninstall, signing/update evidence. |
| Repository code/assets | No top-level `LICENSE`; current README says to treat the work as all rights reserved. | The project cannot promise a GPL-compatible open-source release until ownership/contributor authority and license selection are affirmative. | Ownership/contributor ledger, selected project license, third-party notices, asset/font/icon rights, source-publication scope. |

## Promotion stop rule

Each proposed bundle receives a component graph keyed by exact artifact hash, platform, architecture, build configuration, origin, license, selected distribution branch, obligation owner, evidence link, and disposition. An `unknown`, incompatible, or unreviewed node blocks public binary promotion. Replacing or removing a component creates a new bundle identity; it does not retroactively clear an earlier build.
