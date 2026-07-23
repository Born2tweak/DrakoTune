# ADR-0001 — Distribution branch: hosted_only (near-term)

- **Status:** Accepted (2026-07-23) · **Decision:** D-027 · **Closes:** Q-001 · **Milestone:** DT-51
- **Owners:** product owner (counsel deferred)

## Context

DrakoTune's runtime DSP depends on **Spotify Pedalboard (GPL-3.0)** and a bundled
**FFmpeg build that enables GPL (`--enable-gpl --enable-version3`, effective
license GPL-3.0-or-later)** — see `AURELIAN/08_TOOLING/env_fingerprint.json` and
`AURELIAN/04_AUDITS/DT51_DISTRIBUTION_OBLIGATION_INVENTORY.md`. A single
distributed desktop **binary** that bundles either would inherit copyleft over the
whole distributed work. The three inventoried branches:

1. **gpl_compatible_oss** — ship under GPL-3.0-or-later + provide corresponding source (viable now).
2. **permissive_custom_dsp** — replace pedalboard + GPL FFmpeg before a permissive binary can ship (high cost).
3. **hosted_only** — serve over the network, ship no binary; the copyleft *distribution* source-offer is not triggered (reversible).

Note: "distribution" here means **software packaging**, not music distribution
(see RECONCILIATION_RECORD §7 glossary).

## Decision

Adopt **hosted_only** for the near term. It is already the de-facto posture, ships
no binary, avoids triggering copyleft distribution obligations, and is fully
reversible. It unblocks nothing that requires a binary and blocks nothing that the
hosted product needs.

## Consequences

- DT-51 complete; the hosted product continues unaffected.
- Desktop-binary milestones (DT-71 build spike, DT-88 packaging proof, DT-89 signed
  updates) stay **deferred**; choosing between branch 1 and 2 re-opens **with
  counsel** only if a desktop binary is pursued.
- If reversed, record a superseding ADR + decision-log entry.

## Obligations while hosted_only holds

- No public desktop binary may ship (enforced by PRODUCT_SPEC out-of-scope + claim gate).
- Continue tracking GPL obligations in `src/tooling/license_policy.py` /
  `AURELIAN/08_TOOLING/distribution_obligations.json` so a future binary branch has current data.
