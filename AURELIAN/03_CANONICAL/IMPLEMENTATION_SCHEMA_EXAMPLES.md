# Implementation Schema Examples

**Status:** canonical illustrative contracts v1.2  
**Purpose:** remove avoidable interpretation from DT-45/46/49/56/83. These examples are complete enough to become fixtures, but implementation may choose JSON, typed Python, or database tables so long as semantics and invariants remain identical.

All examples use synthetic identities and contain no real participant or artist data.

## Evaluation bundle

```yaml
schema: drakotune.evaluation_bundle
schema_version: 2.0.0
evaluation_id: eval_01JDTEXAMPLE000000000001
experiment_id: exp_01JDTEXAMPLE000000000001
created_at: 2026-07-21T12:00:00Z
producer:
  code_commit: a3c51637a0c2ed18994a6950a45a72ccb753a93d
  build_id: build_py312_lock_example
  configuration_id: config_clean_v2_example
task:
  intent: repair
  target: harshness
  applicability: applicable
  applicability_reasons: [diagnostic_input_valid, registered_metric_domain]
inputs:
  source_asset_id: asset_synthetic_harsh_001
  treatment_asset_id: render_synthetic_harsh_clean_001
  comparator_asset_id: asset_synthetic_harsh_001
  split_id: split_synthetic_regression_v1
measurements:
  - metric_id: harshness_ratio_v1
    registry_version: 1.0.0
    status: succeeded
    baseline: 0.72
    treatment: 0.58
    effect: -0.14
    uncertainty: {method: not_applicable_deterministic_fixture, lower: null, upper: null}
  - metric_id: mud_ratio_v1
    registry_version: 1.0.0
    status: succeeded
    baseline: 3.1
    treatment: 8.3
    effect: 5.2
    role: collateral_harm
independent_units:
  responses: 0
  listeners: 0
  items: 1
  singers: 0
evidence_tier: T1_synthetic_regression
rights_decision_id: rights_decision_synthetic_fixture_001
verdict_id: verdict_01JDTEXAMPLE000000000001
content_hash: sha256:example_not_a_real_digest
```

## Multiaxis verdict

```yaml
schema: drakotune.verdict
schema_version: 1.0.0
verdict_id: verdict_01JDTEXAMPLE000000000001
evaluation_id: eval_01JDTEXAMPLE000000000001
status: harmful_tradeoff
axes:
  signal_safety: {status: passed, reasons: [finite_output, peak_within_registered_ceiling]}
  target_efficacy: {status: passed, reasons: [harshness_metric_moved_desired_direction]}
  collateral_harm: {status: failed, reasons: [mud_budget_exceeded]}
  intent_preservation: {status: indeterminate, reasons: [no_valid_perceptual_evidence]}
  perceptual_outcome: {status: not_applicable, reasons: [T1_has_no_listeners]}
claim_eligibility:
  engineering: eligible
  bounded_performance: ineligible
  independent_perceptual: ineligible
  product_generalized: ineligible
  reasons: [synthetic_only, collateral_harm, no_independent_listening]
rule_set_id: verdict_rules_v1
```

## Purpose-specific rights grant

```yaml
schema: drakotune.rights_grant
schema_version: 1.0.0
grant_id: grant_synthetic_example_001
subject_or_licensor_id: party_pseudonymous_example_001
evidence_document:
  document_id: document_example_001
  content_hash: sha256:example_not_a_real_digest
  version: 1
effective_at: 2026-07-21T00:00:00Z
expires_at: null
permissions:
  internal_storage: allowed
  development_tuning: allowed
  evaluation_benchmarking: allowed
  model_training: prohibited
  model_distribution: prohibited
  audio_redistribution: prohibited
  public_audio_example: prohibited
  aggregate_result_publication: conditional
  commercial_use: conditional
  claim_support: conditional
conditions:
  - aggregate_result_publication_requires_k_anonymity_review
  - commercial_use_requires_separate_owner_release
withdrawal:
  allowed: true
  contact_method_id: contact_route_protected_001
  response_window: human_decision_required
status: active
reviewed_by: legal_or_rights_owner_required
```

## Consent withdrawal event

```yaml
schema: drakotune.withdrawal_event
schema_version: 1.0.0
withdrawal_id: withdrawal_example_001
grant_id: grant_synthetic_example_001
received_at: 2026-08-01T10:30:00Z
status: planned
authorization_hold_applied: true
affected_nodes:
  assets: [asset_example_001]
  derived_artifacts: [render_example_001, features_example_001]
  experiments: [exp_example_001]
  claims: [claim_example_001]
actions:
  - {node_id: asset_example_001, action: delete, approval: human_required}
  - {node_id: render_example_001, action: delete, approval: human_required}
  - {node_id: exp_example_001, action: rebuild_without_subject, approval: human_required}
  - {node_id: claim_example_001, action: suspend, approval: automatic}
verification: {status: pending, evidence_ids: []}
```

## Immutable listening response

```yaml
schema: drakotune.listening_response
schema_version: 2.0.0
response_id: response_example_001
protocol_id: protocol_repair_pairwise_v1
protocol_version: 1.0.0
participant_id: listener_pseudonymous_017
panel_id: professional_engineer
trial_id: trial_harshness_004
item_id: item_harshness_004
assignment_id: assignment_example_004
assignment:
  side_a_stimulus_id: stimulus_blinded_81
  side_b_stimulus_id: stimulus_blinded_22
  order_index: 7
response:
  choice: tie_no_meaningful_difference
  defect_severity: {a: mild, b: mild}
  artifacts: {a: [], b: [slight_pumping]}
environment:
  playback: headphones
  device_check_id: device_check_example_017
  interruptions_reported: false
created_at: 2026-09-01T14:04:00Z
active: true
supersedes_response_id: null
content_hash: sha256:example_not_a_real_digest
```

Uniqueness invariant: only one active response may exist for `(protocol_id, protocol_version, participant_id, trial_id)`. A correction creates a new response whose `supersedes_response_id` points to the prior record.

## Immutable experiment package

```yaml
schema: drakotune.experiment_package
schema_version: 1.0.0
experiment_id: exp_example_001
status: complete
evidence_tier: T3_independent_listening
protocol_id: protocol_repair_pairwise_v1
preregistration:
  id: prereg_example_001
  frozen_at: 2026-08-15T00:00:00Z
  content_hash: sha256:example_not_a_real_digest
data:
  manifest_id: manifest_confirmatory_example_v1
  split_id: split_confirmatory_example_v1
  rights_decision_id: rights_decision_example_v1
treatments:
  champion_build_id: build_champion_example_v1
  comparator_id: original_level_matched
assignment:
  algorithm_id: balanced_pairwise_assignment_v1
  seed_commitment: sha256:example_not_a_real_digest
analysis:
  analysis_plan_id: sap_example_v1
  environment_id: analysis_lock_example_v1
  unblinded_at: 2026-09-15T00:00:00Z
results: [result_example_primary, result_example_harm]
deviations: []
approvals: [independent_method_review_example]
content_hash: sha256:example_not_a_real_digest
```

## Claim record

```yaml
schema: drakotune.claim
schema_version: 1.0.0
claim_id: claim_example_001
exact_wording: "On the named 2026 confirmatory corpus, build X reduced perceived steady-noise severity relative to level-matched original audio for the tested professional-engineer panel."
class: independent_perceptual
surface: internal_release_candidate_notes
scope:
  task: steady_noise_repair
  population: qualified_professional_engineers
  strata: [tested_strata_manifest_example]
  build_id: build_champion_example_v1
supporting_results: [result_example_primary, result_example_harm]
rights_decision_id: rights_decision_publication_example
limitations: [not_overall_mix_quality, not_untested_genres, not_other_builds]
status: candidate
approved_at: null
expires_at: 2027-03-15T00:00:00Z
suspension_triggers: [build_change, rights_withdrawal, analysis_invalidation, material_subgroup_harm]
owner: product_claim_owner
```

## Research-watcher proposal

```yaml
schema: drakotune.roadmap_proposal
schema_version: 1.0.0
proposal_id: proposal_example_001
watcher_run_id: watcher_run_example_001
trigger: new_relevant_primary_paper
source_records: [source_record_arxiv_example_001]
summary: "Candidate method may reduce on-device parameter-search cost."
applicability: uncertain
rights_status: unknown
evidence_strength: weak_until_reproduced
affected:
  risks: [R-011]
  decisions: [D-007]
  milestones: [DT-81]
proposed_diff:
  action: add_candidate_to_DT_81_queue
  automatic_canonical_change: false
validation: reproduce_official_result_then_target_sandbox
rollback: reject_candidate_and_retain_negative_result
required_human_gate: false
review_status: pending_autonomous_evidence_screen
```

## Validation invariants

- Stable IDs are never reused.
- Content hashes cover canonical serialization, not volatile paths.
- `unknown`, `not_applicable`, `error`, and `indeterminate` are distinct.
- Corrections append; raw records never mutate.
- Claim eligibility cannot exceed evidence tier, rights, build, population, or analysis validity.
- A rights hold or withdrawal automatically suspends dependent use and claims.
- Watcher proposals cannot directly mutate canonical state.

## Required-field dictionary

| Record | Required root fields | Conditional requirements |
|---|---|---|
| `evaluation_bundle` | `schema`, `schema_version`, `evaluation_id`, `experiment_id`, `created_at`, `producer`, `task`, `inputs`, `measurements`, `independent_units`, `evidence_tier`, `rights_decision_id`, `verdict_id`, `content_hash` | Applicable reference metrics require comparator/reference identity and alignment record; listener tiers require nonzero independent-unit identities. |
| `verdict` | `schema`, `schema_version`, `verdict_id`, `evaluation_id`, `status`, `axes`, `claim_eligibility`, `rule_set_id` | `passed` target efficacy requires applicable successful primary evidence; any claim eligibility requires reasons and tier/rights/build compatibility. |
| `rights_grant` | `schema`, `schema_version`, `grant_id`, `subject_or_licensor_id`, `evidence_document`, `effective_at`, `permissions`, `conditions`, `withdrawal`, `status`, `reviewed_by` | Conditional permission requires at least one machine- or human-resolvable condition; expiry/withdrawal status requires event/effective time. |
| `withdrawal_event` | `schema`, `schema_version`, `withdrawal_id`, `grant_id`, `received_at`, `status`, `authorization_hold_applied`, `affected_nodes`, `actions`, `verification` | Completion requires verification evidence for every action; destructive actions require recorded human authority. |
| `listening_response` | `schema`, `schema_version`, `response_id`, `protocol_id`, `protocol_version`, `participant_id`, `panel_id`, `trial_id`, `item_id`, `assignment_id`, `assignment`, `response`, `environment`, `created_at`, `active`, `supersedes_response_id`, `content_hash` | A correction requires `supersedes_response_id`; active uniqueness key must validate before commit. |
| `experiment_package` | `schema`, `schema_version`, `experiment_id`, `status`, `evidence_tier`, `protocol_id`, `preregistration`, `data`, `treatments`, `assignment`, `analysis`, `results`, `deviations`, `approvals`, `content_hash` | Confirmatory status requires frozen preregistration before collection and unblinding after analysis/data lock. |
| `claim` | `schema`, `schema_version`, `claim_id`, `exact_wording`, `class`, `surface`, `scope`, `supporting_results`, `rights_decision_id`, `limitations`, `status`, `expires_at`, `suspension_triggers`, `owner` | Approved/public status requires approvals, publication rights, compatible build/scope, and nonexpired supporting results. |
| `roadmap_proposal` | `schema`, `schema_version`, `proposal_id`, `watcher_run_id`, `trigger`, `source_records`, `summary`, `applicability`, `rights_status`, `evidence_strength`, `affected`, `proposed_diff`, `validation`, `rollback`, `required_human_gate`, `review_status` | Automatic merge is allowed only for the maintenance-change classes enumerated in the autonomy policy. |

## Canonical enums

| Enum | Allowed values |
|---|---|
| Result/verdict status | `passed`, `failed`, `unsafe`, `harmful_tradeoff`, `indeterminate`, `not_applicable`, `error`, `cancelled`, `quarantined` |
| Applicability | `applicable`, `not_applicable`, `unknown`, `out_of_domain`, `missing_required_reference`, `invalid_input` |
| Measurement status | `succeeded`, `failed`, `error`, `cancelled`, `not_applicable`, `quarantined` |
| Evidence tier | `T0_unit_safety`, `T1_synthetic_regression`, `T2_held_out_real_data`, `T3_independent_listening`, `T4_replicated_product_evidence` |
| Rights permission | `allowed`, `prohibited`, `conditional`, `unknown`, `expired`, `withdrawn` |
| Grant status | `draft`, `active`, `expired`, `withdrawn`, `superseded`, `quarantined` |
| Claim class | `engineering`, `bounded_performance`, `independent_perceptual`, `product_generalized` |
| Claim status | `candidate`, `approved_internal`, `approved_public`, `suspended`, `expired`, `retracted`, `rejected` |
| Pairwise response choice | `a`, `b`, `tie_no_meaningful_difference`, `cannot_judge`, `technical_failure` |
| Experiment status | `draft`, `frozen`, `collecting`, `analysis_locked`, `complete`, `invalidated`, `cancelled`, `quarantined` |
| Milestone status | `proposed`, `ready`, `in_progress`, `blocked`, `complete`, `failed_experiment`, `superseded` |
| Human-gate category | `spending`, `people_contact`, `contract_consent`, `rights_legal_privacy`, `credentials_identity`, `confirmatory_method_freeze`, `unblinding`, `material_audio_promotion`, `license_legal`, `distribution_posture`, `public_claims`, `signing_distribution`, `production_change`, `production_release`, `product_scope`, `irreversible_deletion` |

Unknown enum values are schema errors, not aliases. Schema-version migration must explicitly map or quarantine a former value.

## Identity and canonical serialization

- IDs are opaque stable strings with a type prefix; consumers must not derive meaning from sequence or timestamp.
- Timestamps are UTC RFC 3339 with explicit `Z` or offset.
- Canonical content is UTF-8, Unicode-normalized, key-sorted, and serialized with no comments or volatile local paths.
- `NaN`, positive/negative infinity, and implicit numeric strings are forbidden; missing, unknown, and not-applicable use typed states.
- Content hashes use SHA-256 over canonical serialization with the `content_hash` field omitted during hashing.
- Direct identity and protected document locations never enter shareable canonical serialization.
- Floating-point tolerance belongs to the registered metric/test, not the serialization format.

## Validation error contract

Every rejection returns `error_id`, `schema`, `schema_version`, `record_id` when readable, `error_code`, JSON-style field path, safe message, retryability, quarantine action, and correlation ID. Minimum error codes are:

`missing_required_field`, `unknown_enum`, `invalid_identity`, `invalid_timestamp`, `nonfinite_number`, `hash_mismatch`, `duplicate_active_response`, `broken_provenance_edge`, `rights_not_authorized`, `rights_expired_or_withdrawn`, `split_leakage`, `protocol_not_frozen`, `build_or_scope_mismatch`, `claim_evidence_ineligible`, and `unsupported_schema_version`.

Validation never repairs rights, identity, protocol, or evidence-tier ambiguity silently. Mechanical normalization that cannot alter meaning may be recorded as an ingestion transform with its own identity and hash.
