# DT-46 Completion Evidence — Identity and Provenance Schema v2

**Evidence key:** `dt46_identity_graph_suite`
**Milestone:** DT-46 (lane `evidence`, profile `automatic_internal`, resource_class `low`)
**Generated:** 2026-07-21

## Acceptance criteria (Field 13) — status

| Criterion | Result | Evidence |
|---|---|---|
| Round trip | met | `test_node_roundtrip_and_canonical_hash` |
| Canonical hash | met | node `content_hash` over key-sorted body (DT-45 canonical); stable across round-trip |
| Graph integrity | met | `test_valid_lineage_graph_passes`, broken-edge + prefix/type checks |
| Duplicate detection | met | `test_renamed_file_and_duplicate_audio_detected_by_fingerprint` |
| Legacy unknowns explicit | met | `test_legacy_asset_imports_as_explicit_unknown`, `test_legacy_node_missing_lineage_is_surfaced_not_failed` |
| No ID collisions in fixtures | met | `test_content_id_is_stable_and_collision_free` |

## Adversarial matrix (Field 16)

| Case | Handling | Test |
|---|---|---|
| Same person under aliases | linked via shared `group_id`, direct identity not exposed | `test_aliases_link_through_group_identity` |
| Renamed file | content-addressed ID + fingerprint dedup → same node | `test_renamed_legacy_file_maps_to_same_content_id`, duplicate-fingerprint report |
| Duplicate audio | shared fingerprint surfaced in `duplicate_fingerprints` | `test_renamed_file_and_duplicate_audio_detected_by_fingerprint` |
| Cyclic derivation | DFS cycle detection → `broken_provenance_edge` | `test_cyclic_derivation_detected` |
| Correction overwrite | append-only; original retained + marked `superseded`; replacement is a new node | `test_correction_appends_and_supersedes_without_mutation` |
| Missing source | absent parent → `broken_provenance_edge`; active node without required lineage flagged | `test_missing_source_is_broken_edge`, `test_active_asset_without_lineage_flagged` |

## Verification

- Full suite: **427 passed, 4 warnings** (DT-45 baseline 412 + 15 new DT-46 tests).
- Audio regression: **6/6 fixtures match goldens** — no DSP change.

## Deliverables (write_set: identity_schema, provenance_schema, migration_fixtures)

| Component | Path | sha256 (first 16) |
|---|---|---|
| Typed IDs + node types | `src/provenance/ids.py` | `ac7b50ef4ceca71c` |
| Node + correction records | `src/provenance/nodes.py` | `c999dd3e8eabb0c6` |
| Graph + integrity validator | `src/provenance/graph.py` | `66046b1b2d2035b4` |
| Legacy import | `src/provenance/legacy_import.py` | `743b4a910d2aed34` |
| Package API | `src/provenance/__init__.py` | `bce32edc0767b7b4` |
| Graph suite | `tests/test_provenance_graph.py` | `089e77cd79b7145b` |

## Claim impact (Field 21) / non-authorization (Field 22)

`none`. Provenance enables traceability but creates no quality eligibility and
grants no rights. Rights are recorded as `unknown` on legacy nodes and never
inferred; rights **enforcement** is DT-49.

## Handoff (Field 24)

DT-49 (Rights/Consent/Withdrawal Graph) and DT-56 (Listening Protocol) can now
consume stable identities. DT-48 remains blocked pending DT-47.
