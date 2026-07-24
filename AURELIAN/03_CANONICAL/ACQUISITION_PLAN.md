# Rights-Clean Corpus Acquisition Plan (DT-55, autonomous portion)

**Status:** autonomous plan complete; **no asset acquired, no spend, no outreach,
no contract, no legal terms approved** (Field 22). Machine form: `src/acquisition/`;
gap + scenarios: `07_DATA_AND_PROVENANCE/dt55_evidence/coverage_and_scenarios.json`.
Strata basis: accepted DT-54 launch set (D-028).

## 1. Requirement → strata map & coverage gap

Targets derive from the DT-54 coverage matrix (`min_coverage`). Current rights-clean
inventory is VocalSet + vocadito (CC BY 4.0, clean **singing**), which cover only
`language=english`; every rap/pop and home-recording stratum is uncovered.

| Stratum | Target | Have | Gap |
|---|--:|--:|--:|
| genre: rap / melodic_rap / pop | 12 each | 0 | 12 each |
| vocal_presentation: spoken_rapped / melodic | 12 each | 0 | 12 each |
| language: english | 18 | 40 | 0 |
| recording_condition: home_untreated | 12 | 0 | 12 |
| recording_condition: plosive_prone / sibilant_prone | 8 each | 0 | 8 each |
| **Total launch gap** | | | **88 clips** |

**Finding:** public CC-BY singing data cannot supply the target rap/pop, home-recorded,
defect-relevant strata. Acquisition is genuinely required (contract Field 5).

## 2. Source × purpose grant matrix

`src/acquisition/purpose_matrix.py`. Purpose-specific rights are distinct (D-014).

| Source | internal_eval / listening | public_example | model_training |
|---|---|---|---|
| public CC-BY (VocalSet/vocadito) | granted | granted +attrib | granted +attrib |
| owner-controlled | granted | needs counsel | granted |
| synthetic (self-generated) | granted | granted +attrib | granted |
| commissioned dry/wet | **needs spend + contract** | " | " |
| marketplace | **needs counsel** | " | " |
| professional treatment | **needs spend + contract** | " | " |

Only the license-clear, no-spend cells are autonomously usable
(`autonomously_usable`). Everything paid/contract/counsel is gated.

## 3. Validators (Field 14)

`src/acquisition/validators.py` + `withdrawal.py` (13 tests, `tests/test_acquisition.py`):
rights-completeness (every asset carries source/license/attribution/checksum/
permitted-use), checksum duplicate detection, performer/session **leakage** conflict
detection (grouped splits, DT-63), ingestion schema (consent_ref mandatory), and
consent-withdrawal / grant-expiry simulation (revokes purposes, suspends dependent
claims, produces a deletion **plan** — real deletion is human-executed, DT-49 posture).

## 4. Cost / time / storage scenarios (parameters only — no committed spend)

`src/acquisition/costing.py`. Rates are inputs; the owner sets ceilings. Any nonzero
cost flags `requires_human_authorization`.

| Scenario | Cost (w/ 15% contingency) | Needs authorization |
|---|--:|:--:|
| public + synthetic only | $0 | no (but does not fill the rap/pop gap) |
| commissioned dry/wet ×60 @ $50 | $3,450 | **yes** |
| professional reference treatments ×20 @ $120 | $2,760 | **yes** |

(Illustrative unit rates, not quotes.)

## 5. What is completed without counsel or spending

- Requirement/strata map, coverage-gap quantification, rights-clean inventory with
  provenance, purpose matrix, validators, withdrawal/expiry simulation, parameterized
  costing, and this plan. **All done.**

## 6. Human-only choices (→ consolidated packet)

Acquisition budget ceiling + source mix; counsel-drafted consent/retention/withdrawal
terms and license grants; any outreach or commissioning; whether to publish owner
audio as public examples. **None performed or approved here.**
