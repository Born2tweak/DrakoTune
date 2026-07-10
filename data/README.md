# data/ — Dataset governance layer

Policy: [`docs/data/DATASET_GOVERNANCE.md`](../docs/data/DATASET_GOVERNANCE.md) (ADR 0003).
Enforced by `tests/test_data_governance.py` since M21.

| Directory | Committed? | Contents |
|---|---|---|
| `manifests/` | ✅ | one JSON per dataset (schema: `src/data_governance/manifest.py`, v1.0.0) |
| `licenses/` | ✅ | license copies, signed agreements, `ATTRIBUTIONS.md` |
| `local/` | ❌ gitignored | raw downloads of Tier A/B datasets |
| `restricted/` | ❌ gitignored | Tier C data and signed-agreement data (e.g., DAMP), artist data (Tier P) |
| `derived/` | ❌ gitignored | degraded pairs / corpus builds — always regenerable from seeded recipes |

Rules (short form):
- **No audio is ever committed here.** CI fixtures live in `fixtures/` and must be Tier A-derived or synthetic, ≤ 1 MB per file, ≤ 25 MB total.
- **No script downloads restricted data or accepts a license.** Registration, click-throughs, and agreements are human-performed checkpoints; record them in `licenses/` and update the manifest (`checksum`, `local_path`, `last_verified`).
- Unknown manifest facts stay `null` with a note — never guessed.
