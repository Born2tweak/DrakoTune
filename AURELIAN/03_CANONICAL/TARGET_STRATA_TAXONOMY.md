# Target-Genre and Recording Strata Taxonomy (DT-54)

**Status:** canonical v1.0.0 — autonomous framework complete; launch-critical
selection (Q-014) + expert review are **human gates** (contract Field 15).
**Source of truth:** `src/product_taxonomy/` (this doc is the human view; the
machine snapshot is `07_DATA_AND_PROVENANCE/dt54_evidence/taxonomy_v1.json`).
**Scope basis:** D-A / D-025 — dry single lead rap/pop vocal.

## Purpose

Give evaluation a stable, observable population definition so results expose
*where the product works, abstains, or harms* instead of averaging over vague
"vocals" (contract Fields 3–4). Claims must name tested strata (Field 21).

## Principles

- **Observable only.** Every label is an audio / performance / language /
  recording property. No demographic or sensitive personal category is a
  dimension or label; the validator's sensitive-proxy guard rejects any attempt
  (Fields 18, 22).
- **Unknown is never a pass.** `unknown` and `not_applicable` are first-class in
  every dimension; a missing dimension resolves to `unknown`, never a positive.
- **Ambiguity is preserved.** Ambiguous genre → a single `unknown`, not a forced
  guess. Multilabel dimensions carry co-occurring labels (rapped + ad-lib).
- **Sparse strata are excluded from confirmatory claims** (tiny-subgroup guard).

## Dimensions and observable labels (v1.0.0)

| Dimension | Multilabel | Labels (+ `unknown`, `not_applicable`) |
|---|:--:|---|
| genre | no | rap, melodic_rap, sung_rap, pop, rap_pop_hybrid |
| vocal_presentation | yes | spoken_rapped, sung_sustained, melodic, belted, falsetto, whisper, layered_stacked, ad_lib, harmony |
| language | no | english, spanish, multilingual_code_switch, other |
| recording_condition | yes | studio_treated, home_untreated, mobile_device, plosive_prone, sibilant_prone, room_reflective, low_snr, clipped_input |

Language is **self-reported / script-derived only** — never inferred from timbre.

## Recommended coverage matrix (NON-BINDING — Q-014 decision)

`priority` (launch_critical / secondary / out_of_scope), `min_coverage`
(minimum items before a stratum may anchor a confirmatory claim), and
`leakage_group` (`performer_session` — never split one performer/session across
train/eval, for DT-63 grouped splits). **This is a proposal for the owner + audio
lead to accept, amend, or reject; it carries no claim authority until they sign.**

| dimension | value | priority | min | rationale |
|---|---|---|--:|---|
| genre | rap / melodic_rap / pop | launch_critical | 12 | core D-A target |
| genre | sung_rap | secondary | 6 | overlaps melodic_rap |
| vocal_presentation | spoken_rapped / melodic | launch_critical | 12 | primary deliveries |
| vocal_presentation | ad_lib | secondary | 6 | layered; hard to isolate |
| vocal_presentation | layered_stacked | out_of_scope | 0 | not a single dry lead (D-A) |
| language | english | launch_critical | 18 | English-first launch |
| language | spanish / code_switch | secondary | 6 | large share; explicit labels |
| recording_condition | home_untreated | launch_critical | 12 | the core non-engineer user |
| recording_condition | plosive_prone / sibilant_prone | launch_critical | 8 | defect-relevant (cf. N-014) |
| recording_condition | studio_treated | secondary | 6 | cleaner baseline |

## Validators (Field 14) and adversarial coverage (Field 16)

`src/product_taxonomy/validate.py` + `tests/test_product_taxonomy.py` (22 tests):
schema/vocabulary, incompatible-label (single-label dims, sentinel-with-positive),
missing→unknown, version migration (unknown source version = hard error),
sensitive-proxy rejection, sparse-stratum flagging. Adversarial cases covered:
ambiguous genre, multilingual code-switch, layered/ad-lib vocal, synthetic label,
tiny subgroup, sensitive proxy.

## Human gate (Q-014) — what remains

The owner + audio lead must: (1) accept/amend the launch-critical set above;
(2) confirm no sensitive category is added; (3) provide expert taxonomy review and
an example-annotation reliability check (Field 23). Until then, no genre-
generalization claim is permitted and DT-55/DT-56 receive the strata as a
*proposed* freeze, not a confirmed one.
