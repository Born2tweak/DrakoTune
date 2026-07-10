# Next Execution Package — M21: Dataset Governance & Evidence Scaffolding

> Immediately actionable. Executable by any coding agent/session without
> inventing scope. Spec source: `docs/implementation/DRAKOTUNE_MASTER_EXECUTION_ROADMAP.md` (M21),
> policy source: `docs/data/DATASET_GOVERNANCE.md`.

## Objective
Create the dataset-governance layer: directory structure, manifest schema +
validator, dataset manifests (metadata only), attribution ledger, git guards.
**No audio is downloaded in this milestone.**

## Inputs
- `docs/data/DATASET_GOVERNANCE.md` (tiers, schema §3, storage rules §2)
- `docs/research/PUBLIC_VOCAL_AUDIO_DATASET_RESEARCH.md` (per-dataset facts: URLs, licenses, sizes)
- Baseline: `main` @ `064be0d`+docs commits; `python -m pytest -q` → 253 passed.

## Constraints
- No new runtime dependencies (stdlib `json`/`dataclasses` for the validator; pytest only).
- No network calls in code or tests. No license acceptance by code, ever.
- Additive only: do not touch `src/dsp*`, `src/decision`, `src/diagnostics`, goldens.
- Follow existing conventions: versioned module constants, dataclasses, tests-per-module.

## Exact tasks
1. **Directories:** create `data/manifests/`, `data/licenses/`, and `.gitkeep`-free placeholders documented in `data/README.md` (explain tiers, link governance doc). Add to `.gitignore`: `data/local/`, `data/restricted/`, `data/derived/`.
2. **Manifest schema + validator:** `src/data_governance/manifest.py` with `DATASET_MANIFEST_VERSION = "1.0.0"`, a `DatasetManifest` dataclass matching governance §3 keys, `load_manifest(path)`, `validate_manifest(dict) -> list[str]` (returns human-readable violations: missing keys, invalid tier, `allowed_ci_use=True` while `tier != "A"`, etc.).
3. **Manifests (metadata only, `checksum: null`, `local_path: null`):** `vocalset.json` (Tier A, CC BY 4.0, https://zenodo.org/records/1193957), `vocadito.json` (Tier A, CC BY 4.0, https://zenodo.org/records/5557945), `voicebank_demand.json` (Tier A, CC BY 4.0, https://datashare.ed.ac.uk/handle/10283/2791), `musan.json` (Tier A, CC BY 4.0, openslr.org/17), `openslr28_rir.json` (Tier A, Apache 2.0, openslr.org/28), `singverse.json` (Tier B, license `unverified — read HF field at download`, https://huggingface.co/datasets/amphion/SingVERSE, `download_method: manual`), `damp.json` (Tier B, Smule Research License, `download_method: email-agreement`, note the damp-edu@smule.com checkpoint), `cambridge_mt.json` (Tier C, education-only, `download_method: manual`, `allowed_eval_use: manual listening only`). Populate factual fields from the research report; anything unknown → `null` + note, never guessed.
4. **Attribution ledger:** `data/licenses/ATTRIBUTIONS.md` with credit lines for the Tier A sets (VocalSet: Wilkins et al., ISMIR 2018, CC BY 4.0; Vocadito: Bittner et al., CC BY 4.0; VoiceBank-DEMAND: Valentini-Botinhao, CC BY 4.0; MUSAN: Snyder et al., CC BY 4.0).
5. **Git guards:** `tests/test_data_governance.py` — (a) every `data/manifests/*.json` passes `validate_manifest`; (b) `git ls-files` contains no `.wav/.mp3/.flac/.ogg/.m4a` outside `fixtures/`; (c) no tracked file exceeds 1 MB except an allowlist (currently empty); (d) tier/ci-use consistency across all manifests.
6. **Docs:** add M21 row to `CURRENT_MILESTONE.md` status table (mark complete only after evidence); note in `docs/data/DATASET_GOVERNANCE.md` header: "enforced by tests/test_data_governance.py since M21".

## Tests / verification
- `python -m pytest -q` → all pass (253 baseline + new). No skips introduced.
- `python scripts/audio_regression.py` → 6 fixtures still match (unchanged).
- Negative tests: a deliberately invalid manifest fixture (in-test dict, not a committed file) yields violations.

## Acceptance criteria
- All 8 manifests validate; guards green; no audio committed; `.gitignore` covers data dirs; no runtime dep added; no behavior change to any existing module (regression proof: audio_regression + full suite).

## Evidence required in completion report
Command outputs (pytest count, regression OK), list of files added, confirmation `git ls-files` guard passes, any facts that could not be verified (left `null`).

## Stop conditions
- If a manifest fact conflicts with the research report and cannot be resolved from the official source page → record `null` + note, do not guess, continue.
- If any existing test fails for reasons unrelated to this work → stop, report, do not "fix" unrelated systems.
- If tempted to download data "to check" → stop; that is M22 with human checkpoints.

## Out of scope
Downloads, corpus building, degradation recipes, metrics, listening tests, DSP changes, UI changes, new dependencies, CI workflow changes.
