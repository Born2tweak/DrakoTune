# DT-49 Autonomous-Portion Evidence — Rights, Consent, and Withdrawal Graph

**Evidence key:** `dt49_withdrawal_drill`
**Milestone:** DT-49 (lane `evidence`, profile `rights_spend`, `automatic_completion: false`)
**Generated:** 2026-07-21 · **Executor:** claude-code (autonomous)

## Completion status — HONEST

DT-49's profile is `rights_spend` with `automatic_completion: false`. The
milestone therefore **cannot be marked complete autonomously**. What this record
attests is narrower and exact:

> The **autonomous half** of DT-49 (Field 7 "Grant schema, purpose
> authorization, protected consent store interface, derivation traversal,
> deletion/retract simulation"; Field 15 **Automatic:** graph, authorization,
> withdrawal-plan, and security validation) is **implemented and verified on
> synthetic fixtures**. The **human-only half** (consent/contract language,
> retention/privacy obligations, real deletion authority, legal rights
> interpretation) is deliberately **not** implemented and remains gated.

The milestone stays `ready` (human-gated) in `MILESTONE_REGISTRY.yaml`.

## Acceptance criteria (Field 13)

| Criterion | Status | Evidence |
|---|---|---|
| Unknown fails closed | **met** | `test_no_grant_fails_closed_unknown`, `test_public_example_permission_absent_fails_closed` → `UNKNOWN`, `authorized=False` |
| Withdrawal enumerates all fixture descendants and affected claims | **met** | `test_withdrawal_enumerates_all_descendants_and_nothing_unrelated`, `test_withdrawal_suspends_registry_claims_by_supporting_result` |
| …without unrelated deletion | **met** | same test: unrelated branch untouched; `preserved_node_count == 3` |
| Legal/consent authorization of real data | **NOT met — human gate** | out of scope by contract; consent store is an interface only |

## Automated verification (Field 14) & adversarial (Field 16)

20 tests pass (`dt49_withdrawal_drill.txt`). Adversarial cases covered:

| Adversarial case (Field 16) | Test |
|---|---|
| Conflicting grants (allowed + prohibited) | `test_conflicting_grants_resolve_to_prohibited` → PROHIBITED |
| Expired consent | `test_expiry_blocks_after_expires_at`, `test_a_valid_allow_survives_a_second_expired_grant` |
| Orphan derivative | `test_orphan_derivative_is_affected_by_parent_withdrawal` |
| Re-identified alias | `test_reidentified_alias_group_withdrawal_reaches_all_members` |
| Public-example permission absent | `test_public_example_permission_absent_fails_closed` |
| Purpose matrix / conditional use / expiry | `test_allowed_only_for_covered_purpose`, `test_conditional_use_requires_all_conditions` |
| Redaction (shareable graph) | `test_shareable_grant_redacts_consent_handle_and_owner` |

## Deliverables (write_set: rights_schema, consent_store_interface, withdrawal_graph)

| Component | Path |
|---|---|
| Purpose taxonomy | `src/rights/purposes.py` |
| Rights grant schema | `src/rights/grants.py` |
| Fail-closed authorization | `src/rights/authorize.py` |
| Protected consent-store interface + synthetic impl | `src/rights/consent_store.py` |
| Withdrawal traversal + deletion **simulation** + claim suspension | `src/rights/withdrawal.py` |
| Adversarial test suite (20) | `tests/test_rights_graph.py` |

## Design guarantees

- **Fail closed:** no grant → `UNKNOWN` → not authorized. Most-restrictive-wins
  (a `PROHIBITED` grant beats any `ALLOWED`).
- **No real deletion:** `WithdrawalPlan.executed` is always `False`. DT-49 only
  enumerates a recoverable plan; deletion authority is a human gate.
- **Identity isolation (Field 18):** grants carry only an opaque `consent_ref`;
  `shareable_grants()` redacts the handle and owner.
- **Append-only:** withdrawal supersedes a grant with a new withdrawn record;
  history is retained, never mutated.

## Claim impact (Field 21) / non-authorization (Field 22)

`suspends_rights_invalid_claims`. `suspend_affected_claims` quarantines claims
whose supporting evidence loses rights. Does **not** approve any draft consent,
public dataset use, participant contact, or real deletion.

## Regression

Full suite **498 passed** (baseline 478 + 20 new); no existing test changed.
