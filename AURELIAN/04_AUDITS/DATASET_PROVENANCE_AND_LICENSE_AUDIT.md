# Dataset, Provenance, and License Audit

**Verdict:** current governance is directionally good but too coarse for consent withdrawal, leakage control, training, publication, or claims.

## Current strengths

- Existing documentation distinguishes unrestricted/restricted/proprietary tiers.
- Dataset manifests record license, commercial use, redistribution, attribution, and hashes at dataset level.
- Artist consent is acknowledged as a blocker rather than silently assumed.
- Synthetic fixtures are reproducible and valuable for regression.

## Critical gaps

| Gap | Consequence |
|---|---|
| Dataset-level identity only | Cannot reliably group or delete by singer/song/session/take. |
| One license label | Cannot prove separate training/evaluation/publication/redistribution/claim permissions. |
| No immutable rights-grant version | Later term/consent changes cannot be reconstructed. |
| Weak derivation graph | Withdrawal cannot identify clips, features, models, reports, and claims affected. |
| No experiment/listener linkage | Independence, reuse, and privacy are unprovable. |
| No split-policy identity | Singer/song/session leakage can silently inflate results. |
| Public-source optimism | Download access can be mistaken for commercial or training permission. |

## Source dispositions

- VocalSet: potentially usable for attributed isolated-vocal research/fixtures under CC BY 4.0; not mix truth.
- MedleyDB: restricted non-commercial research/evaluation; not a commercial training foundation.
- MUSDB18: mixed licensing and academic access; evaluate file-by-file/use-by-use.
- Cambridge multitracks: practice access does not establish reuse; quarantine pending documented permission.
- Commissioned artists/engineers: desired but no recruitment, spending, or rights are approved yet.

## Required schema

Use globally stable asset/source/performer/work/session/take/derivation/rights/consent/split/experiment/result/claim identifiers. Store grants per purpose, jurisdiction/term, attribution, restrictions, revocation, evidence document hash, owner, review date, and downstream edges. Data with unknown rights is quarantined and cannot support adoption or claims.

## Withdrawal test

A valid system can select one consent grant, enumerate all source and derived artifacts/models/reports/claims, produce an approved delete/rebuild/retract plan, execute it with audit evidence, and demonstrate that unaffected data remains intact.
