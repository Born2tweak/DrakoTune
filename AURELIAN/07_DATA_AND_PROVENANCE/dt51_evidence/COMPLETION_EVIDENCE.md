# DT-51 Autonomous-Portion Evidence — Distribution Obligation Inventory

**Evidence key:** `dt51_signed_distribution_adr` (autonomous inventory subset)
**Milestone:** DT-51 (lane `build`, profile `distribution_decision`, `automatic_completion: false`)
**Generated:** 2026-07-22 · **Executor:** claude-code (autonomous)

## Completion status — HONEST

DT-51's profile is `distribution_decision` with `automatic_completion: false`,
and it depends on DT-49 (whose human gate is open). The milestone **cannot be
completed autonomously**. This record attests only that the Field-15 *Automatic*
half — "bundle comparison, obligation inventory, cost/risk analysis, and
recommendation" — is complete. The **human-only** mandatory product-owner +
qualified-counsel distribution decision is deliberately not made. Milestone stays
`blocked`.

## Acceptance criteria (Field 13) — autonomous subset

| Criterion | Status | Evidence |
|---|---|---|
| Component-level obligations | **met** | `distribution_obligations.json` + `DT51_DISTRIBUTION_OBLIGATION_INVENTORY.md`: pedalboard + GPL ffmpeg flagged strong-copyleft |
| Bundle scenario comparison (3 branches) | **met** | `distribution_scenarios`: gpl_compatible_oss / permissive_custom_dsp (blocked by pedalboard+ffmpeg) / hosted_only |
| Cost/risk + rejected-branch documentation | **met** | inventory §3–§4 |
| One branch accepted with owner/counsel record | **NOT met — human gate** | decision reserved to owner + counsel |

## Automated verification (Field 14) & adversarial (Field 16)

22 tests pass (`dt51_signed_distribution_adr.txt`).

| Adversarial case (Field 16) | Test |
|---|---|
| LGPL not misread as strong GPL | `test_lgpl_not_misread_as_strong_gpl` |
| Transitive/unknown proprietary (e.g. model weights) blocks until reviewed | `test_unknown_license_blocks_permissive_binary` |
| Alternate FFmpeg build (LGPL) changes viability | `test_permissive_only_makes_permissive_binary_viable` |
| Strong copyleft blocks permissive binary, not hosting | `test_strong_copyleft_blocks_permissive_binary_not_hosted` |
| Real SBOM flags pedalboard + ffmpeg | `test_real_sbom_flags_pedalboard_and_ffmpeg_as_strong` |

## Deliverables (write_set: distribution_adr scaffold, license_policy)

| Component | Path |
|---|---|
| License copyleft classifier + 3-branch analysis | `src/tooling/license_policy.py` |
| Inventory generator | `scripts/build_distribution_inventory.py` |
| Machine-readable inventory | `AURELIAN/08_TOOLING/distribution_obligations.json` |
| Human-facing inventory + recommendation | `AURELIAN/04_AUDITS/DT51_DISTRIBUTION_OBLIGATION_INVENTORY.md` |
| Test suite (22) | `tests/test_distribution_inventory.py` |

## Recommendation (Field 15) — NON-BINDING

Lowest-risk reversible near-term = `hosted_only` (already the de-facto posture).
The binary branch (gpl_compatible_oss vs permissive_custom_dsp) is the
consequential decision and is a human product-owner + counsel gate, to be made
once product scope (DT-53) is fixed.

## Non-authorization (Field 22)

Selects no branch, accepts no license obligation, authorizes no release or public
binary. Not a legal determination.
