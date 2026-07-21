# E — Dataset and Provenance Report

**As of:** 2026-07-21  
**Sources:** S-D01–S-D05.

## Finding

No surveyed public dataset is a complete, rights-clear substitute for professionally mixed, target-genre, dry-to-wet vocal evidence. Existing sources are useful only for bounded purposes.

| Source | Useful for | Not established |
|---|---|---|
| VocalSet, CC BY 4.0 | Technique/diversity fixtures, detector research with attribution | Dry-to-wet mix intent; rap/pop production context |
| MedleyDB, non-commercial research | Restricted offline multitrack research/evaluation | Commercial training, distribution, launch claims |
| MUSDB18, mixed licenses/academic access | Restricted separation/evaluation work | Uniform commercial use or redistribution |
| Cambridge multitracks | Mixing practice where terms permit | Training, redistribution, public benchmark publication |
| Current synthetic corpus | Deterministic regression and known-transform diagnosis | Natural failure distribution or preference |

## Required rights model

A single `license` field is insufficient. Each asset must record source/performer/composer/recording identities and explicit grants for internal development, evaluation, training, model distribution, audio redistribution, excerpt publication, benchmark publication, commercial use, retention, derivative creation, and claim support. Restrictions and withdrawal must propagate through a derivation graph.

## Acquisition gap

The project needs consented dry recordings and independently produced treatments covering target strata, with evaluation/training/publication grants negotiated separately. Group splits must isolate singer/song/session/source to prevent leakage.

## Source-by-source rights and utility audit

| Source | Recorded evidence | Bounded utility | Rights/task conflict | Decision and recheck |
|---|---|---|---|---|
| S-D01 MedleyDB | Official site/download terms identify non-commercial research licensing; original collection is multitrack and includes vocal-containing material. | Restricted offline method/evaluation exploration. | Non-commercial posture conflicts with assumed commercial training/distribution; multitrack mix context is not target dry-to-wet truth. | Quarantine from commercial training/claims; review every asset/term version. |
| S-D02 MUSDB18 | Official dataset page describes 150 stereo tracks, about 10 hours, 100/50 split, and mixed source licenses/access. | Restricted separation/context benchmarking. | Mixed rights prevent one blanket commercial permission; stems are not automatically redistributable. | File/use-level authorization only. |
| S-D03 VocalSet | Zenodo record reports 10.1 hours, 20 professional singers, vocal techniques, CC BY 4.0. | Attributed technique/diversity fixtures and detector research. | Isolated technique recordings do not encode professional mixing decisions or target production context. | Use only for named authorized fixture tasks; never call it mix ground truth. |
| S-D04 Cambridge multitracks | Site offers multitracks for mixing practice under site/per-track context. | Human practice or specifically permitted evaluation. | Public download does not establish training, redistribution, benchmark publication, or commercial claim rights. | Quarantine until exact permission record exists. |
| S-D05 repository manifests | Existing governance records VocalSet, vocadito, VoiceBank, MUSAN, OpenSLR, and restricted tiers. | Starting inventory and attribution evidence. | Dataset-level license fields cannot express performer/work/session identity or purpose-specific grants. | Migrate as legacy/unknown fields through DT-46/49. |
| Synthetic corpus | Reproducible generator recipes and known transforms. | T0/T1 regression, calibration mechanics, error discovery. | Transform distribution and tiny cells do not represent real defects, genre, or preference. | Preserve and label synthetic; never promote to launch evidence. |

## Rights uncertainty rule

If the exact asset, rights holder, license/consent version, and requested purpose cannot be linked, the permission is `unknown` and use is blocked. Public accessibility, attribution, or a permissive code license cannot fill missing recording, composition, performer, training, publication, or claim rights.

## Exact dataset snapshot

Counts and labels below are discovery metadata from the cited official records, not blanket authorization. Import must pin the downloaded artifact and its terms.

| Source | Primary-source snapshot | Permitted planning classification | Required import evidence |
|---|---|---|---|
| S-D01 MedleyDB | Official collection materials describe 196 multitrack songs in the original collection; the official download terms use CC BY-NC-SA 4.0/non-commercial research conditions. The DiffVox paper used a 76-track vocal-containing subset and retained 70 after exclusions; that is a paper subset, not the whole corpus. | `restricted_research`; not commercial training, redistribution, public benchmark, or launch-claim evidence. | Dataset/version, exact track IDs, per-asset terms, downloaded terms snapshot, exclusion ledger, compositions/performers where available, requested purpose. |
| S-D02 MUSDB18 | Official page records 150 full-length stereo tracks totaling about 10 hours, divided into 100 training and 50 test tracks at 44.1 kHz; source licenses/access conditions are mixed. | `restricted_research`; authorize file by file and purpose by purpose. | Track/license mapping, access agreement, stem/audio redistribution status, purpose grants, split preservation, artifact checksum. |
| S-D03 VocalSet | Zenodo record reports 10.1 hours from 20 professional singers across vocal techniques under CC BY 4.0. | `attribution_required` for an explicitly approved task; not mix-decision ground truth. | Zenodo record/version, file checksum, attribution text, singer/session grouping, allowed purpose, derived-fixture lineage. |
| S-D04 Cambridge MT | The site supplies practice multitracks, but a public download and practice framing do not themselves grant model training, redistribution, public benchmarking, or commercial claim support. Corpus-wide counts and uniform rights are therefore `unverified`. | `unknown` until exact track and purpose permission are recorded. | Track page and terms snapshots, rights-holder/permission record, requested purpose, publication/redistribution status, withdrawal/contact path. |

## Purpose-gate matrix

| Proposed use | Minimum affirmative rights fields | Default when any field is missing |
|---|---|---|
| Internal objective evaluation | recording, composition, performer/voice, internal evaluation, retention, derivative processing | Block and quarantine. |
| Human listening evaluation | all internal-evaluation rights plus participant presentation, processor/export service where applicable, and consent/privacy basis | Block and quarantine. |
| Model training or tuning | training/tuning grant, derivative/model-output terms, commercial-use posture, retention, withdrawal propagation | Block training and all derived promotion. |
| Redistribute audio or excerpts | audio/excerpt redistribution, publication venue/scope, attribution, composition and performer/publicity clearance | Block export/publication. |
| Distribute weights or learned artifacts | model/weights distribution, training-source compatibility, withdrawal remedy, commercial route | Block packaging/release. |
| Support a public claim | claim-support grant plus population/build/experiment linkage and unexpired evidence | Block claim eligibility. |

Dataset-level permission never overrides a more restrictive asset-, performer-, composition-, consent-, contract-, or jurisdiction-level record. Withdrawal traverses every derived fixture, feature, model, evaluation, export, and claim dependency before deletion or quarantine is considered complete.
