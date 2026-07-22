# DT-51 Distribution Obligation Inventory (autonomous prep)

**Status:** autonomous inventory + recommendation complete; **the distribution
branch decision is a human product-owner + qualified-counsel gate and is NOT
made here.** · **Generated:** 2026-07-22 · from `AURELIAN/08_TOOLING/sbom.json`

> This is a conservative engineering inventory to inform counsel, **not a legal
> determination**. Machine-readable form: `AURELIAN/08_TOOLING/distribution_obligations.json`
> (regenerate with `PYTHONPATH=. python scripts/build_distribution_inventory.py`).

## 1. Component-level copyleft inventory (runtime surface)

| Component | Version | License | Copyleft | Blocks a permissive binary? |
|---|---|---|---|---|
| pedalboard | 0.9.23 | GPL-3.0 (GPLv3) | **strong** | **yes** |
| ffmpeg | 8.1.1 (`--enable-gpl --enable-version3`) | GPL-3.0-or-later | **strong** | **yes** |
| numpy | 2.4.6 | BSD-3-Clause/… | permissive | no |
| scipy | 1.17.1 | BSD | permissive | no |
| librosa | 0.11.0 | ISC | permissive | no |
| soundfile | 0.13.1 | BSD | permissive | no |
| pyloudnorm | 0.2.0 | MIT | permissive | no |
| fastapi | 0.139.0 | MIT | permissive | no |
| uvicorn | 0.51.0 | BSD-3-Clause | permissive | no |
| httpx | 0.28.1 | BSD | permissive | no |
| python-multipart | 0.0.32 | Apache-2.0 | permissive | no |

**Hard fact (confirms DT-50):** the two strong-copyleft components —
`pedalboard` (the DSP backend) and the GPL-configured `ffmpeg` binary — are on
the actual runtime path. A single bundled binary that includes either inherits
GPL-3.0 copyleft over the whole distributed work.

### Transitive weak-copyleft (full closure; file-scoped, lower risk)

The SBOM closure (101 pkgs) also contains weak-copyleft transitives: `soxr`
(LGPL-2.1, via librosa), `certifi` (MPL-2.0), `tqdm` (MPL-2.0), `fpdf2`
(LGPL-3.0), `browser-cookie3` (LGPL). These are file-/library-scoped: they carry
notice + component-source-offer obligations but do **not** relicense the app.
They are not runtime-blocking for any branch and are excluded from the
"blocks a permissive binary" test above, but counsel should confirm the notice
set at packaging time.

## 2. The three branches, mechanically compared

| Branch | Viable as-is? | Blocked by | Obligation to accept | Reversible? |
|---|---|---|---|---|
| **gpl_compatible_oss** | ✅ yes | — | Ship whole work under GPL-3.0-or-later + provide corresponding source. Accepts pedalboard + GPL ffmpeg as-is. | ❌ no |
| **permissive_custom_dsp** | ❌ no | pedalboard, ffmpeg | Replace/re-implement both strong-copyleft runtime components with permissive/original DSP before a permissive binary can ship. | ❌ no |
| **hosted_only** | ✅ yes | — | Serve over the network; ship no binary. GPL/LGPL/MPL source-offer is **not** triggered by hosting (no AGPL component present). Keeps both binary branches open. | ✅ yes |

## 3. Recommendation (NON-BINDING — decision is a human gate)

- **Lowest-risk reversible near-term:** `hosted_only`. It ships value without
  accepting an irreversible license posture and preserves both binary options.
  (DrakoTune already runs as a hosted FastAPI service, so this is the current
  de-facto posture.)
- **The consequential, harder-to-reverse choice** is the binary branch:
  `gpl_compatible_oss` (accept copyleft, go open source) vs
  `permissive_custom_dsp` (invest in replacing pedalboard + GPL ffmpeg). This
  should be decided with **qualified counsel** and only once product scope
  (DT-53) is fixed, because the target user/job changes the cost/benefit.

## 4. Cost/risk sketch (for the human decision)

| Branch | Eng cost | Legal risk | Strategic cost |
|---|---|---|---|
| gpl_compatible_oss | low | low (well-understood GPL obligations) | must open-source; competitors can fork |
| permissive_custom_dsp | **high** (re-implement DSP + drop GPL ffmpeg features) | medium (must prove clean-room / no GPL leakage) | keeps code proprietary |
| hosted_only | low (already hosted) | low | no desktop offline product; server cost/ops |

## 5. Human gate (do NOT proceed autonomously)

The mandatory product-owner + qualified-counsel **distribution-branch decision**.
Until it is made, DrakoTune stays internal source-run / hosted, and the desktop
binary milestones (DT-71, DT-88, DT-89) remain blocked (Field 19).
