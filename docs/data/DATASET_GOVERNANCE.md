# DrakoTune Dataset Governance

> Policy for acquiring, storing, using, and citing audio datasets.
> Source analysis: `docs/research/PUBLIC_VOCAL_AUDIO_DATASET_RESEARCH.md` (§28).
> Status: adopted 2026-07-10 (ADR 0003). Applies to all agents and contributors.
> Enforced by `tests/test_data_governance.py` since M21 (schema:
> `src/data_governance/manifest.py`, manifests: `data/manifests/`).

## 1. Usage tiers

Classify every dataset by its **most restrictive component actually used**.

| Tier | Label | Allowed | Forbidden | Examples |
|---|---|---|---|---|
| A | `commercially-usable` | internal eval, CI fixtures, redistribution of derived clips (with attribution), published benchmarks, product claims | — | VocalSet (CC BY 4.0), Vocadito (CC BY 4.0), VoiceBank-DEMAND (CC BY 4.0), MUSAN (CC BY 4.0), OpenSLR-28 (Apache 2.0), most OpenAIR IRs (check per item) |
| B | `research-only` | local internal evaluation, papers; legal sign-off required before results support commercial claims | redistribution, CI fixtures, shipping, automated pipelines that re-download | MUSDB18-HQ, MedleyDB, MoisesDB, GTSinger, M4Singer, CSD, DAMP (per signed agreement), SingVERSE (pending license check), EARS |
| C | `permission-required` / `education-only` | manual internal listening/study within stated terms | any automated use, any redistribution, research use without contributor contact | Cambridge-MT, Shaking Through, RWC, LDC corpora |
| D | `excluded` | nothing | everything | clinical voice DBs (Saarbruecken, MEEI, VOICED), scraped a cappellas (Looperman/YouTube), iKala (unavailable), AudioSet audio |
| P | `proprietary` | per signed artist consent scope | anything outside consent; voice cloning; biometric use | future artist-contributed corpus |

Rules of interpretation:
- "Downloadable" ≠ "usable". The Zenodo/HF license field is authoritative, read it at download time and record it.
- CC BY attribution must appear in any published benchmark, report, or paper that used the data.
- Tier B data may inform *engineering decisions*; published *product claims* must rest on Tier A + Tier P evidence (or pass legal review).

## 2. Storage and Git rules

```
data/                      # NEVER committed except metadata/manifests
  manifests/               # committed: one JSON per dataset (schema below)
  licenses/                # committed: license text copies + attribution notes
  local/                   # gitignored: raw downloads (Tier A/B)
  restricted/              # gitignored: Tier C + signed-agreement data (DAMP)
  derived/                 # gitignored: degraded pairs, corpus builds (regenerable)
fixtures/                  # committed: ONLY small Tier-A-derived or synthetic clips
reports/evaluations/       # committed: benchmark result JSON/markdown (no audio)
```

- Add to `.gitignore`: `data/local/`, `data/restricted/`, `data/derived/`.
- Hard limits: no committed audio file > 1 MB; no committed audio that is not Tier A or self-generated synthetic; total committed fixture budget ≤ 25 MB.
- Derived audio must be regenerable from a manifest + seeded recipe, never hand-edited.

## 3. Manifest schema (one JSON per dataset in `data/manifests/`)

Required keys: `id`, `version`, `official_name`, `official_url`, `paper_url`, `license`, `tier` (A/B/C/D/P), `commercial_use` (yes/no/unclear), `redistribution` (yes/no), `registration_required`, `attribution_text`, `download_method` (direct/zenodo-request/email-agreement/manual), `checksum` (sha256 of archive, null until downloaded), `file_count`, `duration_hours`, `sample_rate`, `bit_depth`, `channels`, `vocal_type`, `language`, `genre`, `recording_device`, `clean_reference` (yes/no), `defect_labels` (yes/no/list), `local_path`, `preprocessing`, `derived_fixtures` (list), `allowed_eval_use`, `allowed_ci_use` (bool), `notes`, `last_verified` (date).

## 4. Manual approval checkpoints (never automated)

| Dataset | Gate |
|---|---|
| DAMP | email `damp-edu@smule.com`, human signs Research Data License; store agreement in `data/licenses/` |
| MUSDB18(-HQ), MedleyDB | Zenodo access request click-through by a human |
| Cambridge-MT | human reads FAQ terms; research/commercial use requires contacting contributors — record any correspondence |
| SingVERSE, SingMOS | human reads HF license field at download time; record it in the manifest |
| MoisesDB | human signup; CC BY-NC-SA acknowledged |
| Any Tier C/D | do not download without an explicit recorded decision |

No script may accept licenses, submit registration forms, use credentials, or bypass click-throughs. Scripts may verify checksums and build derived fixtures from already-approved local data.

## 5. CI fixture policy

- CI may contain: synthetic signals (current fixture library), and short (≤10 s) excerpts derived from Tier A data with attribution recorded in `data/licenses/` and the manifest's `allowed_ci_use: true`.
- CI must not fetch remote datasets. Benchmarks over Tier B data run locally only; their **result files** (metrics, no audio) may be committed.

## 6. Proprietary / artist data policy (Tier P)

Collection may not begin before an approved consent protocol containing: written consent covering commercial use; **separate opt-in** for any future model training; recording ownership statement; no voice cloning / biometric identification / impersonation, contractually and technically; withdrawal + deletion procedure that propagates to derived data; minors excluded (or guardian consent); processed-output ownership stays with the artist; retention period stated. Consent records stored alongside audio in `data/restricted/artist/<id>/`. Listening-test responses (no audio, no PII beyond listener role) are logged from day one under `reports/evaluations/` — they are the seed of the future preference dataset.

## 7. Attribution ledger

`data/licenses/ATTRIBUTIONS.md` lists every Tier A dataset in use with its required credit line. Any published artifact (benchmark, paper, blog, product page citing results) must reproduce the relevant lines.
