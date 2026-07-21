# Source Registry

**Access date for external sources:** 2026-07-21 unless noted. Primary sources are preferred. A license statement is recorded as evidence, not legal advice.

## Repository evidence

| ID | Source | Role | Key evidence |
|---|---|---|---|
| S-R01 | Commit `a3c51637a0c2ed18994a6950a45a72ccb753a93d` | Audited baseline | Exact code and documentation state. |
| S-R02 | `README.md`, `CURRENT_MILESTONE.md`, `docs/` | Historical/project evidence | Product claims, milestone record, data/licensing drafts. |
| S-R03 | `scripts/run_alpha.py`, `src/orchestration.py`, `src/decision/`, `src/dsp_engine/` | Execution evidence | Default v2 pipeline and deterministic DSP flow. |
| S-R04 | `src/evaluation.py`, reporting/manifest modules | Evaluation evidence | Objective result shape and current trace contract. |
| S-R05 | `scripts/listening_analyze.py` and listening tooling | Protocol evidence | Former sample, tie, clean-safety, and aggregation behavior. |
| S-R06 | `reports/evaluations/perf/20260712-150853.md` | Performance evidence | Runtime/memory scaling and historical MemoryErrors. |
| S-R07 | corpus-v2 benchmark/calibration reports | Data/evaluation evidence | Mixed SI-SDR outcomes, errors, detector false positives. |
| S-R08 | `.github/workflows/ci.yml`, `pyproject.toml` | Reproducibility evidence | Unpinned dependency installation and baseline CI gates. |

## Standards and evaluation methods

| ID | Source | Authority/use | Applicability limit |
|---|---|---|---|
| S-E01 | [ITU-R BS.1116-3](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1116-3-201502-I%21%21PDF-E.pdf) | Controlled listening for small impairments | Expensive/expert setting; not a generic preference label. |
| S-E02 | [ITU-R BS.1534-3](https://www.itu.int/rec/R-REC-BS.1534) | MUSHRA for intermediate-quality systems with hidden reference and anchors | Do not call an arbitrary multi-stimulus test “MUSHRA.” |
| S-E03 | [ITU-R BS.1770-5](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I%21%21PDF-E.pdf) | Loudness and true-peak measurement | Safety/level comparability, not artistic quality. |
| S-E04 | [EBU R 128 v5](https://tech.ebu.ch/publications/r128) | Program loudness operational guidance | Broadcast target is not automatically a dry-vocal target. |
| S-E05 | [ITU-R BS.1387-2 / PEAQ](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1387-2-202305-I%21%21PDF-E.pdf) | Full-reference perceptual audio-quality method | Device/codec impairment domain; not wet-vs-dry creative preference. |
| S-E06 | [ViSQOL](https://github.com/google/visqol) | Apache-2.0 full-reference speech/audio metric implementation | Requires a legitimate reference and domain validation. |
| S-E07 | [webMUSHRA](https://github.com/audiolabs/webMUSHRA) | Browser framework supporting MUSHRA/AB designs | Older project; source-specific license review required. |
| S-E08 | [Baayen, Davidson, Bates 2008](https://quantling.org/~hbaayen/publications/baayenDavidsonBates.pdf) | Crossed random-effects rationale | Model specification still depends on experiment design. |
| S-E09 | [Simulation-based power for mixed models](https://pmc.ncbi.nlm.nih.gov/articles/PMC8613146/) | Power planning for clustered data | Requires plausible variance/effect assumptions from pilot data. |
| S-E10 | [Hierarchical bootstrap](https://pmc.ncbi.nlm.nih.gov/articles/PMC7906290/) | Cluster-aware uncertainty option | Cluster hierarchy must match data generation. |
| S-E11 | [Davidson tie model](https://www.tandfonline.com/doi/abs/10.1080/01621459.1970.10481082) | Pairwise comparisons with ties | Candidate model; validate assumptions and implementation. |

## Automatic mixing and differentiable audio research

| ID | Source | Evidence | Readiness decision |
|---|---|---|---|
| S-M01 | [Diff-MST](https://arxiv.org/abs/2407.08889) | Interpretable differentiable multitrack style-transfer console, ISMIR 2024 | Research candidate; multitrack/reference assumptions differ. |
| S-M02 | [DiffVox paper](https://arxiv.org/abs/2504.14735) and [code](https://github.com/SonyResearch/diffvox) | DAFx 2025 vocal effect-chain matching; MIT code | Research candidate; training presets include MedleyDB/private data. |
| S-M03 | [Inference-time Gaussian prior](https://arxiv.org/abs/2505.11315) | WASPAA 2025 parameter-estimation approach; limited listening study | Offline challenger only after rights/eval gates. |
| S-M04 | [DeepAFx](https://github.com/adobe-research/DeepAFx) | ICASSP 2021 automatic audio effects | Adobe Research License; not assumed production-compatible. |
| S-M05 | [dasp-pytorch](https://github.com/csteinmetz1/dasp-pytorch) | Apache-2.0 differentiable processors | Useful research building block; no product-quality proof. |
| S-M06 | [DeepAFx-ST](https://arxiv.org/abs/2207.08759) | Differentiable style-transfer research | Reference/style-transfer scope requires separate product mode. |

## Candidate enhancement/separation/quality tools

| ID | Source | License/evidence | Constraint |
|---|---|---|---|
| S-C01 | [DeepFilterNet](https://github.com/Rikorose/DeepFilterNet) | Apache-2.0/MIT code; speech enhancement | Singing-vocal applicability and weights/data rights require review. |
| S-C02 | [Demucs](https://github.com/facebookresearch/demucs) | MIT repository; archived 2025-01-01 | Maintenance and separation-artifact risk. |
| S-C03 | [RNNoise](https://github.com/xiph/rnnoise) | BSD-3-Clause speech denoiser | Speech domain; treat as challenger. |
| S-C04 | [NISQA](https://github.com/gabrielmittag/NISQA) | MIT code; model weights CC BY-NC-SA 4.0 | Speech communications domain and non-commercial weights. |

## Datasets and recording sources

| ID | Source | Stated properties | Allowed posture pending record review |
|---|---|---|---|
| S-D01 | [MedleyDB](https://medleydb.weebly.com/) / [downloads](https://medleydb.weebly.com/downloads.html) | Multitracks; non-commercial research CC BY-NC-SA 4.0 | Restricted research/evaluation only. |
| S-D02 | [MUSDB18](https://sigsep.github.io/datasets/musdb.html) | 150 stereo tracks, ~10h, 100/50 split; mixed licenses/access terms | Restricted research/evaluation only. |
| S-D03 | [VocalSet](https://zenodo.org/records/1193957) | 10.1h, 20 professional singers, CC BY 4.0 | Isolated technique/detector fixtures after attribution; not mix-pair truth. |
| S-D04 | [Cambridge MT multitracks](https://cambridge-mt.com/ms3/mtk/) | Downloads for mixing practice; per-track/terms context | Permission/education only until documented. |
| S-D05 | Repository data-governance records | VocalSet, vocadito, VoiceBank, MUSAN, OpenSLR and restricted tiers | Follow existing tiers, expanded with use-purpose rights. |

## Desktop, DSP, packaging, and distribution

| ID | Source | Stated license/posture | Consequence |
|---|---|---|---|
| S-L01 | [Spotify Pedalboard](https://github.com/spotify/pedalboard) | GPL-3.0 | Current DSP dependency may determine distributed-work license obligations. |
| S-L02 | [FFmpeg legal](https://ffmpeg.org/legal.html) and [license](https://github.com/FFmpeg/FFmpeg/blob/master/LICENSE.md) | Base LGPL 2.1+; optional GPL components/configuration | Record exact build flags/components; audited host has `--enable-gpl`. |
| S-L03 | [Qt for Python licensing](https://doc.qt.io/qtforpython-6/commercial/index.html) | LGPLv3/GPLv3/community and commercial options | Candidate UI framework only after distribution design review. |
| S-L04 | [PyInstaller](https://pyinstaller.org/) | Bootloader/project licensing with bundled-component obligations | Packaging does not resolve dependency licenses. |

## Recruitment and professional practice

| ID | Source | Evidence | Use |
|---|---|---|---|
| S-P01 | [Prolific payment model](https://researcher-help.prolific.com/en/articles/445230-prolific-s-payment-model) and [pricing](https://researcher-help.prolific.com/en/articles/445239-what-is-your-pricing) | Current minimum/recommended hourly guidance | General/trained listener recruitment benchmark, not expert sourcing alone. |
| S-P02 | [SoundBetter](https://soundbetter.com/) | Marketplace of audio professionals | Candidate expert sourcing; explicit study/reuse contract still needed. |
| S-P03 | [AirGigs](https://www.airgigs.com/) | Marketplace of music professionals | Candidate expert sourcing; explicit study/reuse contract still needed. |
| S-P04 | [AES sections](https://aes.org/community/section/) and [education directory](https://aes.org/community/education-students/aes-education-directory/) | Professional/academic audio community | Candidate outreach/qualification channel subject to approval. |

## Continuous research infrastructure

| ID | Source | Evidence | Control |
|---|---|---|---|
| S-W01 | [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html) | Official query API | Respect terms/rate guidance; store metadata and identifiers. |
| S-W02 | [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | Public scholarly metadata | Abstract/full-text rights vary; metadata is not adoption evidence. |
| S-W03 | [OpenAlex authentication](https://developers.openalex.org/guides/authentication) | 2026 freemium/key and daily-credit posture | Cost/terms health check; fail closed on change. |
| S-W04 | GitHub REST APIs for releases/advisories | Primary release/security metadata | Use APIs, pinned repositories, and deduplication; no brittle scraping. |

## Registry rules

Every future entry must include stable ID, exact URL or repository identity, publisher, publication/update date if known, access date, evidence type, license/terms snapshot, applicability, contradiction notes, and all downstream decisions/claims. A source being authoritative does not make it applicable to every DrakoTune task.
