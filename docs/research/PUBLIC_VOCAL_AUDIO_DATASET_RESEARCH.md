# Public Vocal Audio, Mixing & Audio-Quality Dataset Research

**Project:** DrakoTune — Intelligent Vocal Processing Platform
**Report date:** 2026-07-10
**Scope:** Public datasets, benchmarks, repositories, and open-source resources for vocal diagnosis, DSP validation, vocal enhancement, and mix-quality evaluation
**Status:** Research only. No code, no downloads, no repository changes.

---

## 1. Executive Summary

DrakoTune's core product question — *can deterministic DSP make poor raw vocals noticeably smoother, less harsh, cleaner, and more professionally listenable?* — can be substantially validated with existing public data, but **not with a single dataset**. The public ecosystem is fragmented across singing-voice research, speech enhancement, source separation, and intelligent-music-production communities, each with different licensing regimes.

**The five most important findings:**

1. **A validation corpus is buildable today.** Combining clean solo-singing datasets (VocalSet — CC BY 4.0; Vocadito — CC BY 4.0) with real amateur recordings (DAMP Smule archives — research license) and synthetic degradation (DEMAND/MUSAN noise + public room impulse responses via tools like audiomentations and pyroomacoustics) gives DrakoTune a legally workable clean/degraded paired benchmark for its deterministic alpha **without any model training**.

2. **A true singing-voice-enhancement benchmark finally exists.** SingVERSE (2025, Hugging Face `amphion/SingVERSE`, 3,929 paired clips / 18.1 h, 19 real-world acoustic scenarios with studio-quality clean references) is the first real-world paired benchmark for singing voice enhancement. Before it, the field borrowed speech benchmarks (VoiceBank-DEMAND). SingVERSE should be treated as DrakoTune's primary external validation target, subject to license verification at download time.

3. **The dry-to-professionally-processed vocal pair with known parameters is the ecosystem's biggest gap.** No public dataset pairs raw vocals with professional mixed versions plus the plugin chains and parameter settings used. The closest resources are the SAFE-DB (semantic descriptors + EQ/compressor/reverb/distortion parameter settings, but not vocal-specific), SignalTrain (dry/wet compressor pairs with known settings), the Mix Evaluation Dataset (multiple engineer mixes + ~13,000 listener comments), and Cambridge-MT multitracks (raw stems + reference mixes, education-only license). This gap is the strongest argument for DrakoTune eventually collecting proprietary data.

4. **Licensing is the dominant constraint, not availability.** Almost every music/singing dataset (MUSDB18, MedleyDB, MoisesDB, M4Singer, GTSinger, OpenSinger, CSD, DAMP) is research-/non-commercial-only. Commercially usable audio is concentrated in the speech world (VoiceBank-DEMAND, VCTK, LibriSpeech, Common Voice, MUSAN) plus a handful of singing sets (VocalSet CC BY 4.0, Vocadito CC BY 4.0). DrakoTune must maintain a strict two-tier policy: research-only data for internal evaluation and papers; openly licensed data for anything shipped, redistributed, or embedded in automated CI tests.

5. **Objective metrics exist but none directly measures "professional vocal quality."** Reference-based metrics (SI-SDR, PESQ, ViSQOL, STOI) require clean references and mostly assume speech; non-intrusive predictors (DNSMOS, NISQA, TorchAudio-SQUIM, SingMOS/SingMOS-Pro for singing) are usable proxies but were not trained on mixed-music vocals. "Smoother," "less harsh," and "more professional" claims will ultimately require blinded, loudness-matched human listening tests (MUSHRA-style or pairwise A/B via webMUSHRA/Go Listen). A pragmatic metric stack for the alpha: integrated LUFS + true peak + crest factor + spectral measures (harshness-band energy 2–5 kHz, sibilance-band 5–10 kHz) + DNSMOS/NISQA as sanity proxies + blinded pairwise preference tests.

**Bottom line:** DrakoTune's alpha can be validated within ~2–4 weeks of data work using VocalSet + Vocadito + SingVERSE + VoiceBank-DEMAND + a synthetic degradation pipeline, evaluated with loudness-matched A/B listening plus a small objective metric suite. Contemporary-genre coverage (rap, trap, hyperpop, Auto-Tuned vocals, bedroom recordings on cheap microphones) is essentially absent from public data and is DrakoTune's clearest long-term proprietary-data opportunity.

---

## 2. DrakoTune Context

DrakoTune is a deterministic, offline vocal-cleanup pipeline: FFmpeg normalization (44.1 kHz / 16-bit / mono) followed by a Spotify Pedalboard chain (≈80 Hz high-pass, upper-mid parametric cut, gentle compression, light gate, output gain normalization), producing before/after previews and a processed WAV. There is no ML training planned, no generative processing, no cloning.

Implications for dataset selection:

- **No training data is needed now.** Datasets are needed for *testing, diagnosis calibration, and validation*, which relaxes size requirements (hundreds of clips suffice, not thousands of hours) but raises the bar on realism and diversity.
- **Clean references matter more than volume.** Deterministic before/after validation benefits most from (a) clean vocals that can be synthetically degraded in controlled ways, and (b) real degraded recordings paired with clean references.
- **License risk profile:** using research-only audio to privately evaluate a DSP chain is generally low-risk in practice but is still outside many licenses' permitted use if DrakoTune is a commercial product ("research use" in most licenses means academic research, not corporate R&D). Every dataset below is labeled accordingly; legal review is recommended before relying on any research-only set in commercial development.
- **A licensing footnote on DrakoTune's own stack:** Spotify Pedalboard is licensed **GPL-3.0**. This is unrelated to datasets but is a material fact for a commercial product (GPL obligations attach to distributed software incorporating it; server-side use is typically unaffected). Flagged here because the report is meant to support engineering credibility.

---

## 3. Research Methodology

- **Sources prioritized:** official dataset pages (Zenodo, university hosts, Hugging Face official orgs), original peer-reviewed papers (ISMIR, ICASSP, Interspeech, NeurIPS D&B, DAFx, AES), and official GitHub repositories. Aggregators (Papers with Code, Kaggle, blog posts) were used only for discovery, never as the license authority.
- **Verification performed in this session (July 2026):** licenses and availability were web-verified for the highest-stakes items: VocalSet (CC BY 4.0, Zenodo), Vocadito (CC BY 4.0, Zenodo), CSD (CC BY-NC-SA 4.0), DAMP (Smule research license via CCRMA/email), GTSinger (CC BY-NC-SA 4.0, Hugging Face), M4Singer/OpenSinger (research-only, Mandarin), MUSDB18/MUSDB18-HQ (non-commercial, Zenodo), MoisesDB (CC BY-NC-SA 4.0), MedleyDB (CC BY-NC-SA), VoiceBank-DEMAND (CC BY 4.0, Edinburgh DataShare), Cambridge-MT (education-only, per-FAQ), Mix Evaluation Dataset (brechtdeman.com), SAFE-DB (semanticaudio.co.uk), SingVERSE (HF `amphion/SingVERSE`), SingMOS/SingMOS-Pro (HF), NHSS (NUS EULA), Saarbruecken Voice Database (research emphasis; hosted stimmdb.coli.uni-saarland.de, mirror on Zenodo), OpenAIR (per-item CC licenses), ViSQOL/DNSMOS/NISQA (open-source implementations).
- **Items not individually re-verified this session** are drawn from the model's knowledge base (cutoff January 2026) and are marked **[verify at download]** where license or availability is version-dependent or historically unstable.
- **Honesty rules applied:** nothing invented; discontinued resources (iKala) labeled unavailable; "downloadable" is never equated with "commercially usable"; conflicting statistics are noted where known.

Labels used throughout: `Commercially usable` · `Research only` · `Academic only` · `Education only` · `Permission required` · `License unclear` · `Unavailable` · `Partially available`.

---

## 4. Key Findings

1. **Isolated, dry, high-quality singing exists in useful quantity** — VocalSet (10.1 h, 20 pro singers), CSD (Korean/English pro female), M4Singer (~29.8 h, 20 Mandarin pros), GTSinger (~80.6 h, 20 singers, 9 languages, technique labels), OpenSinger (~50 h Mandarin), OpenCpop — but is heavily biased toward trained singers, Mandarin/classical/pop styles, and studio conditions. Only VocalSet and Vocadito are commercially usable.
2. **Real amateur singing at scale exists in exactly one place:** the DAMP archives (Smule karaoke, tens of thousands of smartphone performances, real-world noise/reverb/device coloration). Research license required; the single most realistic input distribution match for DrakoTune's expected users.
3. **Paired clean/degraded vocal data:** speech has an abundance (VoiceBank-DEMAND, DNS Challenge, EARS, WHAM/WHAMR, REVERB); singing now has SingVERSE (real) and can be manufactured synthetically from clean sets. Before SingVERSE, no accepted singing-enhancement benchmark existed — this is now only a *partially* closed gap (SingVERSE is evaluation-scale, not training-scale).
4. **Defect-specific public benchmarks are almost nonexistent** for the defects DrakoTune cares most about: no public harshness benchmark, no sibilance-severity benchmark, no vocal-specific declipping benchmark, no plosive/mouth-click dataset with severity labels. These must be synthesized or collected.
5. **Mixing-intelligence data exists but is thin:** SAFE-DB (descriptor→parameter mappings for EQ/compressor/reverb/distortion), Mix Evaluation Dataset (multiple mixes + listener comments), Cambridge-MT (raw multitracks + engineer mixes, education-only), MUSDB18-derived automatic-mixing research (Sony/QMUL). None provides vocal-chain parameters at production quality with redistribution rights.
6. **Metrics:** no validated "vocal smoothness" or "professionalism" metric exists. DNSMOS/NISQA transfer imperfectly to singing; SingMOS/SingMOS-Pro target synthesized singing naturalness, not recording quality. Human listening remains the ground truth for DrakoTune's claims.
7. **Contemporary genres are unrepresented.** No serious public dataset covers rap stems, melodic rap, trap/rage/hyperpop vocals, intentional Auto-Tune, or bedroom-condenser-in-untreated-room recordings. Every public singing dataset skews classical/pop/folk/Mandarin-pop. This is a strategic gap and a proprietary-data opportunity.

---

## 5. Immediate Alpha-Relevant Datasets

The short list that should be acquired first (details in later sections):

| Priority | Resource | Why now | License |
|---|---|---|---|
| 1 | **VocalSet** (Zenodo) | 10.1 h clean, dry, pro solo vocals; ideal degradation substrate; technique diversity (breathy, belt, vibrato…) | CC BY 4.0 — `Commercially usable` |
| 2 | **SingVERSE** (Hugging Face) | Real degraded singing + studio clean references; direct before/after validation | `[verify at download]` — research-oriented |
| 3 | **Vocadito** (Zenodo) | 40 solo-vocal clips, 7 languages, varied training levels, **varied recording devices** — small but realism-dense; CC BY 4.0 | `Commercially usable` |
| 4 | **VoiceBank-DEMAND** (Edinburgh DataShare) | Standard paired clean/noisy corpus; calibrates noise-gate/denoise behavior; CC BY 4.0 | `Commercially usable` |
| 5 | **DAMP subsets** (Stanford CCRMA / Smule) | The real-world amateur karaoke distribution DrakoTune will actually face | `Research only` (email agreement) |
| 6 | **MUSDB18-HQ** (Zenodo) | 150 tracks with isolated vocal stems + full mixes; vocal-in-mix context | `Research only` |
| 7 | **DEMAND + MUSAN noise** | Synthetic degradation source material | MUSAN CC BY 4.0; DEMAND CC (share-alike) `[verify version]` |
| 8 | **OpenAIR + OpenSLR-28 RIRs** | Real room impulse responses for reverb degradation and dereverb stress tests | per-item CC / Apache 2.0 |
| 9 | **Cambridge-MT multitracks** | Raw vocal takes with pro reference mixes; manual internal listening only | `Education only` |
| 10 | **Mix Evaluation Dataset** | 180+ mixes, 18 songs, ~13k listener statements — vocabulary and evidence for "what makes a mix better" | mixed; `Research only` in practice |

---

## 6. Singing-Vocal Datasets

### 6.1 VocalSet — ⭐ top recommendation
- **Source:** Zenodo — https://zenodo.org/records/1193957 · Paper: Wilkins et al., ISMIR 2018 (https://archives.ismir.net/ismir2018/paper/000114.pdf)
- **Content:** 10.1 h monophonic studio recordings; **20 professional singers (9 M / 11 F)** across voice types; **17 vocal techniques** (vibrato, straight, belt, breathy, fry, trill, inhaled, etc.) on 5 vowels, in scales/arpeggios/long tones/excerpts.
- **Format:** WAV, 44.1 kHz mono. Dry, quiet studio recordings. No lyrics/pitch annotations in the base set (see **Annotated-VocalSet**, Zenodo 7061507, which adds F0/note annotations).
- **License:** **CC BY 4.0 — `Commercially usable`**, attribution required. Direct Zenodo download (~4–5 GB). No registration.
- **DrakoTune relevance: very high.** The best clean substrate for synthetic degradation; technique labels enable robustness testing (does the de-harsh EQ ruin an intentionally breathy or belted voice?). Limitations: exercises rather than songs; classical/trained bias; no amateur takes.

### 6.2 DAMP family (Smule / Stanford CCRMA)
- **Source:** https://ccrma.stanford.edu/damp/ · License text: https://ccrma.stanford.edu/damp/ResearchLicense.txt · Access: email damp-edu@smule.com and accept the Research Data License Agreement. Small subsets (DAMP-1k, DAMP-VP1k) mirrored on Zenodo (records 2533364 / 2533417).
- **Content:** multiple archives of amateur karaoke performances from the Smule app: DAMP-MVP (Multiple Songs: ~34,000+ solo performances), DAMP-VSEP (vocal separation pairs: vocal + backing track), DAMP balanced subsets, Intonation dataset (~10k performances selected for pitch quality; IEEE ICASSP 2019). Metadata includes performance/singer IDs, gender, region, "love" counts.
- **Character:** smartphone microphones, untreated rooms, real background noise, real amateur singers, contemporary pop repertoire — **the closest public match to DrakoTune's expected input distribution.**
- **License:** **`Research only`**, per-archive agreement; no redistribution; commercial use not granted. Registration by email required; hosting has been stable at CCRMA and the data remains cited in 2024–2025 papers.
- **Caveats:** vocals recorded over headphone backing tracks — mostly solo vocal audio but with occasional bleed; MP3/M4A compression; no clean references (real-world only, so usable for realism testing and no-reference metrics, not reference-based metrics).

### 6.3 NUS-48E and NHSS (National University of Singapore)
- **NUS-48E:** 48 English songs, 12 subjects (each sings and *speaks* 4 songs' lyrics), ~169 min, phone-level annotations. Paper: Duan et al., APSIPA 2013. **`Permission required`** (request to NUS HLT lab); research use.
- **NHSS:** successor — 100 songs, 10 singers (5 M/5 F), ~7 h parallel sung + spoken audio with utterance/word alignments. Official page: https://hltnus.github.io/NHSSDatabase/ · EULA: research-only (https://hltnus.github.io/NHSSDatabase/uploads/NUSLicence.pdf). **`Research only`**.
- **Relevance:** moderate — clean English pop singing; parallel speech is useful for studying speech-vs-singing spectral differences when tuning filters that were designed on speech assumptions.

### 6.4 CSD — Children's Song Dataset (KAIST)
- 50 Korean + 50 English children's songs, one professional female singer, two keys each; MIDI + phoneme-level lyric annotations; 44.1 kHz. Official: https://mac.kaist.ac.kr/resources.html, GitHub `emotiontts/emotiontts_open_db`. **CC BY-NC-SA 4.0 — `Research only`.**

### 6.5 Mandarin/Chinese corpora: OpenCpop, OpenSinger, M4Singer
- **OpenCpop:** ~5.2 h, one professional female Mandarin singer, studio quality, phoneme/note annotations; signed agreement, **`Research only`**.
- **OpenSinger:** 66 Mandarin singers (~50 h), high-fidelity pro recordings (Multi-Singer, ACM MM 2021). **`Research only`**.
- **M4Singer:** ~29.8 h, 20 professional Mandarin singers covering SATB ranges, studio quality, lyric/pitch/note/slur annotations (NeurIPS 2022). Access via request form; **CC BY-NC-SA-style `Research only`.**
- **Relevance:** excellent clean substrates and register diversity (SATB); language bias limits phoneme-specific findings (Mandarin sibilants differ from English), but spectral/dynamics behavior transfers.

### 6.6 GTSinger (NeurIPS 2024 D&B)
- ~80.6 h, 20 singers, **9 languages**, 6 singing techniques with technique annotations, realistic music scores; paired speech. HF: https://huggingface.co/datasets/AaronZ345/GTSinger · Paper: arXiv 2409.13832. **CC BY-NC-SA 4.0 — `Research only`.**
- The largest multi-language technique-annotated open singing corpus; strong for robustness testing across languages and techniques.

### 6.7 Japanese corpora
- **JVS-MuSiC:** ~100 singers, one common song + others; research-only (University of Tokyo). **Tohoku Kiritan / Itako, PJS, NIT-SONG070**: single-singer Japanese nursery/enka corpora, research use. Relevance: low-moderate (small, Japanese, synthesis-oriented).
- **jaCappella** (2023): 35 Japanese a cappella ensemble songs, 6-part vocal ensembles; research-only. Useful for choral/backing-vocal edge cases.

### 6.8 MIR-1K and iKala
- **MIR-1K:** 1,000 clips (~133 min), 19 amateur Mandarin karaoke singers; vocals and accompaniment on separate channels; pitch, voiced/unvoiced, lyrics annotations; 16 kHz. Free download (NTU). **License: research-oriented, `License unclear` for commercial use.** Amateur realism is a plus; 16 kHz limits full-band DSP evaluation.
- **iKala:** **`Unavailable`** — distribution discontinued by Academia Sinica/KKBOX years ago. Do not plan around it; mark any copies you encounter as unlicensed.

### 6.9 Vocadito (NYU/MARL)
- 40 short solo singing excerpts, 7 languages, **varied singer training levels and recording devices**, with F0, note, and lyric annotations. Zenodo: https://zenodo.org/records/5557945 · ISMIR-LBD 2021. **CC BY 4.0 — `Commercially usable`.**
- Tiny but disproportionately valuable: it is the only openly licensed set that deliberately includes untrained singers and consumer devices.

### 6.10 SVCC / SVDD challenge data
- **Singing Voice Conversion Challenge 2023** data builds on NUS corpora — research-only, useful mainly to future ML.
- **CtrSVDD / SVDD 2024** (singing deepfake detection) supplies bona-fide + synthesized singing; the **SingMOS** dataset was built from it (see §11).

### 6.11 Other notables
- **MedleyVox** (2023): benchmark for multi-singer separation built from existing corpora — pointers, not new audio.
- **PopBuTFy** (from "Neural Singing Voice Beautifier," ACL 2022): **paired amateur vs. professional renditions by the same singers** — conceptually the single most DrakoTune-relevant dataset design in existence. **`Partially available`**: the Chinese portion was released for research; the English portion was withheld for copyright reasons. Verify current status at https://github.com/MoonInTheRiver/NeuralSVB.
- **MTG-Jamendo:** 55k full CC-licensed songs with tags — full mixes only (no stems); useful for genre-level tonal-profile statistics under mostly CC licenses (per-track; many are NC).

**Summary judgment:** clean pro singing is plentiful (research-only), openly licensed singing is scarce (VocalSet + Vocadito ≈ 10.4 h total), amateur real-world singing is DAMP-or-nothing, and contemporary genres are absent.

---

## 7. Multitrack and Stem Datasets

### 7.1 MUSDB18 / MUSDB18-HQ — the source-separation standard
- **Source:** https://sigsep.github.io/datasets/musdb.html · Zenodo 1117372 (MUSDB18) / 3338373 (HQ, uncompressed WAV).
- **Content:** 150 full tracks (~10 h): mixture + stems {vocals, bass, drums, other}. Train 100 / test 50. Drawn from DSD100, MedleyDB, Native Instruments stems, heavy rock/pop bias.
- **License:** mixed per-track, predominantly **CC BY-NC-SA — `Research only` / `Academic only`**; Zenodo access request.
- **Relevance:** vocal stems are *mixed* stems (processed with EQ/comp/FX printed) — good for "professional vocal target" spectral statistics and vocal-in-mix evaluation, poor as dry raw inputs.

### 7.2 MedleyDB 1.0 / 2.0
- 122 + 74 multitracks with **raw unprocessed stems**, instrument activations, melody F0 annotations; ~70 tracks contain vocals. NYU MARL: https://medleydb.weebly.com/ · Zenodo (request access). **CC BY-NC-SA 4.0 — `Research only`.**
- One of very few sources of genuinely **raw (dry) recorded vocal tracks** alongside the final mixes — directly supports raw-vs-mixed vocal comparison, gain-staging and EQ studies.

### 7.3 Cambridge-MT "Mixing Secrets" Library (Mike Senior)
- **Source:** https://cambridge-mt.com/ms/mtk/ — 600+ multitrack sessions across genres, incl. raw vocal takes, plus forum reference mixes; sizes 100 MB–several GB per song.
- **License (per official FAQ):** free **for educational purposes only**; commercial use requires contributor permission; research use should be individually cleared with contributors. **`Education only` / `Permission required`.**
- **Relevance:** the richest source of realistic raw lead-vocal takes of any public resource (many amateur/semi-pro sessions with real defects: sibilance, room, headphone bleed, popped plosives). Safe use for DrakoTune: **manual internal listening and engineer study only**; do not embed in automated pipelines or redistribute without permissions.

### 7.4 Others
- **DSD100** (SiSEC 2016 predecessor of MUSDB18): 100 tracks, dev/test stems; `Research only`; superseded — use MUSDB18-HQ.
- **MoisesDB** (Music AI / Moises, ISMIR 2023): 240 tracks, ~45 artists, 12 genres, stems in 11 instrument classes incl. separated lead/background vocals; 44.1 kHz. GitHub `moises-ai/moises-db`, registration. **CC BY-NC-SA 4.0 — `Research only`.** Best genre breadth and stem granularity of any stem set.
- **Slakh2100:** 2,100 synthesized MIDI multitracks — **no vocals**; irrelevant except as accompaniment beds.
- **Open Multitrack Testbed (QMUL):** aggregated multitracks incl. Mix Evaluation songs; per-item licenses; hosting historically intermittent — **`Partially available` [verify]**.
- **Shaking Through (Weathervane Music):** pro studio sessions with stems available after free registration; non-commercial listening/education terms — **`Permission required`**; wonderful for engineer study.
- **Mix Evaluation Dataset** — covered in §12/§22.

**Use for DrakoTune:** (1) MUSDB18-HQ/MoisesDB vocal stems → "professional vocal" spectral/dynamic reference profiles; (2) MedleyDB raw stems → raw-vs-mixed deltas (what did engineers actually change?); (3) Cambridge-MT → curated internal defect gallery.

---

## 8. Speech-Enhancement Datasets

Transfer caveat up front: singing differs from speech in F0 range (up to ~1.5 kHz for soprano vs ~300 Hz speech), sustained vowels, vibrato, higher dynamic range, and intentional breathiness. Speech-enhancement data is valid for calibrating **noise, reverb, and device artifacts**, but any threshold tuned on speech (e.g., gate thresholds, HPF corner) must be re-verified on singing — an 80 Hz HPF is safe for speech but a low bass (E2 = 82 Hz) singer's fundamental sits right at the corner.

### 8.1 VoiceBank-DEMAND (Valentini) — ⭐ the standard paired benchmark
- **Source:** Edinburgh DataShare https://datashare.ed.ac.uk/handle/10283/2791 (the 10283/1942 entry is superseded).
- **Content:** paired clean/noisy speech: 28-speaker train (11,572 utts) + 2-speaker test (824 utts); 10 noise types at 0–15 dB SNR (train), unseen noises at 2.5–17.5 dB (test); 48 kHz source, commonly used at 16 kHz.
- **License:** **CC BY 4.0 — `Commercially usable`.** Direct download, ~2–3 GB.
- **Relevance:** immediate — run the DrakoTune chain on noisy inputs, compute PESQ/STOI/SI-SDR against clean refs; establishes whether the gate/EQ helps or hurts under known SNRs. Limitation: 16 kHz convention and short utterances; speech only.

### 8.2 Microsoft DNS Challenge (2020–2023, ICASSP/Interspeech)
- GitHub `microsoft/DNS-Challenge`. Hundreds of GB: clean speech (LibriVox-derived, multiple languages, **includes a singing subset**), large noise corpus (Freesound/AudioSet-derived), RIRs, and a training-set synthesizer. **Licensing is per-component** (public domain LibriVox, CC-mixed Freesound, Apache OpenSLR sets); scripts MIT. **Label: mixed, mostly permissive, `[verify per component]`.**
- Relevance: best single quarry for degradation raw materials (noise + RIR + synthesizer recipes) even without training models.

### 8.3 Other speech corpora
- **VCTK** (110 English speakers, accents; CC BY 4.0 — `Commercially usable`): clean speech substrate.
- **LibriSpeech / LibriTTS(-R)** (CC BY 4.0): 1,000 h / 585 h; audiobook speech; `Commercially usable`.
- **Common Voice** (CC0): massive, crowd-recorded on consumer devices — actually a good *device-variation* corpus; `Commercially usable`.
- **EARS (2024):** 107 speakers, ~100 h anechoic 48 kHz speech incl. emotional/whispered/loud styles, with EARS-WHAM/EARS-Reverb benchmarks. **CC BY-NC 4.0 `[verify]` — `Research only`.** The best full-band speech-enhancement benchmark; DrakoTune-relevant because 48 kHz matters for de-essing/harshness bands that 16 kHz corpora cannot test.
- **CHiME-1..8:** real multi-microphone noisy speech; registration/LDC components; `Research only`/paid — low priority.
- **REVERB Challenge (2014):** reverberant speech benchmark built on WSJCAM0 — **LDC paid license**; use OpenSLR/BUT alternatives instead.
- **WHAM! / WHAMR!:** binaural real ambient noise (+reverb) mixed with WSJ0 speech; noise corpus **CC BY-NC 4.0**; WSJ0 requires LDC. `Research only`.
- **LibriMix:** open recipe (LibriSpeech + WHAM noise) — reproducible, mostly permissive except WHAM noise NC.
- **URGENT Challenge 2024/2025 (Interspeech):** *universal* speech enhancement across distortion types — additive noise, reverb, **clipping, bandwidth limitation, codec artifacts** — with open data recipes; https://urgent-challenge.github.io/urgent2025/. **Highly relevant blueprint** for DrakoTune's multi-defect evaluation design. `Research only` components vary.

---

## 9. Singing-Enhancement Datasets

State of the field: until 2025 there was **no accepted public benchmark for singing-voice enhancement**; papers improvised by degrading clean corpora (VocalSet, NUS-48E, OpenSinger) synthetically. That changed partially:

- **SingVERSE (2025)** — first real-world singing-enhancement benchmark: 3,929 noisy/clean pairs (18.14 h), 19 real acoustic scenarios (concert halls, roadsides, rooms), time-aligned studio-quality clean references. HF: https://huggingface.co/datasets/amphion/SingVERSE · arXiv 2509.20969. License on HF page **[verify at download]**; treat as `Research only` until confirmed. **This should be DrakoTune's headline external validation set.**
- **ReverbFX (2025)** — RIR set derived from *reverb effect plugins* specifically for singing dereverberation (arXiv 2505.20533): useful for building dry↔wet reverb pairs matching music-production reverbs rather than physical rooms.
- **AnyEnhance (2025)** — unified generative enhancement model for speech+singing (denoise, dereverb, declip, super-resolution). A model, not a dataset; relevant as future-ML reference and as an "opponent" baseline (how much better is ML than DrakoTune's deterministic chain?).
- **Neural Singing Voice Beautifier / PopBuTFy** — amateur↔professional paired renditions (§6.11); `Partially available`, research-only.
- **Bandwidth extension / declipping for singing:** no dedicated public singing benchmark. General audio declipping research (Záviška et al. survey, IEEE SPM 2021) provides evaluation methodology and synthetic clipping protocols that transfer directly.

**Explicit statement:** apart from SingVERSE, **no strong accepted public benchmark exists for singing denoising/dereverberation/de-essing/declipping.** Synthetic construction from VocalSet/GTSinger + DEMAND/RIRs is the standard workaround and is legitimate if reported honestly.

---

## 10. Audio Defect and Degradation Datasets

Public data with *explicit defect labels* is scarce. What exists:

- **Audio Degradation Toolbox (ADT, Mauch & Ewert, ISMIR 2013):** MATLAB recipes for reproducible degradations (vinyl, radio, smartphone playback+mic, clipping, dynamic-range compression, noise) — a methodology standard. GitHub `sebastianewert/audio-degradation-toolbox`; also Python ports. `Commercially usable` (code).
- **URGENT challenge corpora (§8.3):** clipping/codec/bandwidth degradations on speech with recipes.
- **Declipping literature:** standard test sets are small (e.g., 10 speech/music excerpts at multiple clipping thresholds, SPADE/A-SPADE papers) — protocols reusable, data trivial to regenerate.
- **FSDnoisy18k / FSD50K:** labeled environmental sounds incl. hum, hiss-like classes — usable as *defect exemplars*, not vocal-defect benchmarks.
- **Codec artifacts:** ODAQ (2024, open dataset of audio quality with coding artifacts + listener scores — Fraunhofer/Netflix; `Research only` [verify]) is the closest thing to a labeled codec-artifact quality set.
- **Hum/electrical noise:** no dedicated public dataset; trivially synthesizable (50/60 Hz + harmonics).

**Deterministic vs ML detectability of DrakoTune's defect list:**
- *Reliably deterministic:* clipping (sample-level flat-top/histogram tests, true-peak), low recording level (RMS/LUFS), excessive LF energy & proximity effect (band ratios), hum (narrow spectral peaks at 50/60 Hz multiples), hiss (HF noise floor in pauses), gross tonal imbalance (long-term spectrum vs reference profile), overcompression (crest factor, loudness range), sibilance energy (5–10 kHz band bursts on unvoiced frames), plosives (LF transients), dynamic inconsistency (short-term loudness variance).
- *Borderline:* room reverb amount (spectral decay / SRMR-style estimators work but are speech-tuned), harshness (2–5 kHz energy correlates but perception is context/timbre-dependent), mud/boxiness (250–500 Hz ratios; genre-dependent), comb filtering/phase (cepstral peaks; noisy).
- *Realistically ML:* nasality, breathiness-as-defect vs style, distinguishing intentional distortion/Auto-Tune from defects, "professional vs amateur" overall judgment, artifact detection in processed output.

---

## 11. Audio-Quality Assessment Datasets and Metrics

### Datasets
- **NISQA Corpus:** >14,000 speech samples with ~97,000 crowdsourced ratings (MOS + dimensions: noisiness, coloration, discontinuity, loudness). GitHub `gabrielmittag/NISQA` (MIT). `Research only` for the corpus [verify]; code MIT.
- **DNS Challenge P.835 sets:** speech MOS (signal/background/overall) used to train DNSMOS.
- **VoiceMOS Challenge (2022–2024):** MOS-prediction benchmarks; 2024 edition added **singing** (SVS/SVC outputs).
- **SingMOS / SingMOS-Pro:** 3,421 clips/4.25 h (SingMOS) → 7,981 clips (Pro) of real+synthesized Chinese/Japanese singing with ≥5 professional MOS ratings each. HF `TangRain/SingMOS-Pro`; arXiv 2406.10911 / 2510.01812. Focus = synthesis naturalness, but it is the only public *singing* MOS data; license [verify at download].
- **ODAQ (2024):** open audio-quality dataset with expert MUSHRA-style scores across processing artifacts (coding, tonal balance) — music-relevant; `Research only` [verify].
- **PEASS / SiSEC subjective data:** separation-artifact perception scores; niche.
- **Audiobox-Aesthetics (Meta, 2025):** no-reference *aesthetic* predictors (production quality, complexity, enjoyment) for speech/music/sound — pretrained model, license **[verify — released under a Meta research-friendly license; the code is MIT-like but confirm weights terms]**. Notably the only public "production quality" predictor; worth evaluating on DrakoTune outputs with skepticism.

### Metric assessment for DrakoTune

| Metric | Type | Speech | Music/Singing | Needs reference | License/impl | Verdict for DrakoTune |
|---|---|---|---|---|---|---|
| PESQ (ITU-T P.862) | intrusive | ✔ | ✘ (invalid for music) | ✔ | ITU-licensed; `pesq` pip exists but commercial use of the algorithm is encumbered | Research-only sanity metric on speech tests |
| POLQA (P.863) | intrusive | ✔ | ✘ | ✔ | **Commercial license required** | Not recommended |
| STOI/ESTOI | intrusive intelligibility | ✔ | ✘ | ✔ | free (pystoi, MIT) | Use on speech tests only |
| SI-SDR / SDR / SIR / SAR | intrusive energy-ratio | ✔ | ✔ | ✔ | free (BSD/MIT impls) | **Implement now** for synthetic-degradation tests |
| ViSQOL v3 / ViSQOLAudio | intrusive perceptual | ✔ | ✔ (audio mode, 48 kHz) | ✔ | **Apache 2.0**, Google GitHub | **Implement now** — the only open reference metric with a music mode |
| DNSMOS (P.835) | no-reference DNN | ✔ | ~ (unvalidated on singing) | ✘ | MIT code+ONNX models (microsoft/DNS-Challenge) | **Implement now** as proxy; report with caveats |
| NISQA | no-reference DNN | ✔ | ~ | ✘ | MIT | Implement now (multi-dimension output is diagnostic-friendly) |
| TorchAudio-SQUIM | no-reference (PESQ/STOI/SI-SDR est.) | ✔ | ~ | ✘ | BSD-2 (torchaudio) | Beta |
| SingMOS predictor | no-reference singing MOS | ✘ | ✔ (synthesized singing) | ✘ | research | Research only |
| PEAQ (BS.1387) | intrusive codec quality | ~ | ✔ codecs | ✔ | ITU; GPL impl (gstpeaq) | Not recommended (codec-specific, dated) |
| FAD (Fréchet Audio Distance) | distributional | ~ | ✔ | corpus-level ref | Apache (google-research/fadtk) | Research (set-level, not per-clip) |
| CLAP similarity | embedding | ~ | ✔ | optional | Apache (LAION) | Research |
| **LUFS-I, LRA, true peak (EBU R128)** | signal | ✔ | ✔ | ✘ | ffmpeg ebur128 / pyloudnorm (MIT) | **Implement now — mandatory for fair A/B** |
| Crest factor / dynamic spread | signal | ✔ | ✔ | ✘ | trivial | **Implement now** |
| Spectral band ratios (harsh 2–5 kHz, sibilant 5–10 kHz, mud 250–500 Hz), spectral flatness, THD proxy | signal | ✔ | ✔ | ✘ | librosa (ISC) | **Implement now — the diagnosis backbone** |
| SRMR (reverb) | no-reference | ✔ | ~ | ✘ | free (srmrpy) | Beta (speech-tuned; validate on singing) |

**Human-correlation honesty note:** none of the no-reference DNN metrics has published validation on *recorded (non-synthesized) singing quality*; correlations claimed in their papers are for speech (DNSMOS ~0.9 with P.835 MOS on speech) or synthesized singing (SingMOS). Treat all of them as directional evidence, never as proof of "sounds more professional."

---

## 12. Automatic Mixing and Intelligent Production Datasets

- **SAFE-DB (Semantic Audio Feature Extraction, Birmingham City/QMUL):** crowd-collected DAW plugin data: descriptor terms ("warm," "bright," "harsh"…) + **full parameter settings** for a parametric EQ, compressor, overdrive, and reverb, + before/after audio features. http://www.semanticaudio.co.uk/datasets/data/ · Stables et al., ISMIR 2014. Free download; license **[verify — academic project, treat `Research only`]**. **Directly usable without ML:** extract median EQ curves associated with "harsh→less harsh" transformations to sanity-check DrakoTune's harshness cut.
- **Mix Evaluation Dataset (De Man & Reiss, DAFx 2017):** 18 songs × ~10 mixes each (180+ mixes) by different engineers + ~13,000 annotated listener statements ("vocal too sibilant," "good vocal presence"). http://www.brechtdeman.com/publications/ and the Open Multitrack Testbed. `Research only` in practice; audio licensing per-song. **Goldmine for perceptual vocabulary and for validating which mix attributes drive preference.**
- **MUSDB18-based automatic mixing (Sony/QMUL, Martínez-Ramírez et al. 2022 "Automatic music mixing with deep learning and out-of-domain data"):** code + pretrained models on GitHub (`sony/ai-mixing` ecosystem, `csteinmetz1/automix-toolkit`). Research licenses.
- **Mixing Style Transfer (Koo et al., ICASSP 2023):** contrastive FXencoder + MixFXcloner; self-supervised from wet multitracks (no dry/wet pairs needed). GitHub `jhtonyKoo/music_mixing_style_transfer` (research). Relevant later for reference-matching.
- **DeepAFx / DeepAFx-ST (Adobe/QMUL):** style transfer for EQ+compression with differentiable/black-box plugins; pretrained models; **research/non-commercial license (Adobe)**.
- **SignalTrain (Hawley et al. 2019):** ~20 h paired dry/wet audio through an **LA-2A compressor with labeled control settings** — one of the only public dry/wet-with-parameters datasets. Zenodo; `Research only` [verify]. Deterministic insight: measurable compressor behavior targets.
- **IDMT-SMT-Audio-Effects (Fraunhofer):** 55k notes (guitar/bass) through 11 effects with settings — instrument-focused, not vocal; `Research only`.
- **FX-normalization / dry-wet research (Sony “FxNorm-automix”):** effect-normalization statistics extracted from large mix corpora; code available, research license.
- **Matchering (GitHub `sergree/matchering`, GPL-3.0):** open reference-mastering tool — deterministic loudness/EQ matching logic worth studying; GPL contamination caution for direct embedding.

**Assessment:** no dataset provides *vocal-chain* parameters at professional quality with reuse rights. SAFE-DB + SignalTrain + Mix Evaluation give partial, complementary evidence: descriptor→EQ mappings, compressor dry/wet ground truth, and mix-preference language respectively.

---

## 13. Dry-to-Processed Vocal Pairs

Direct answer: **no high-quality public dataset of dry vocals paired with professionally processed versions plus known plugin parameters exists.** This is a major ecosystem gap (see §31). Closest approximations, ranked:

1. **MedleyDB** — raw vocal stems + final mixes (no parameters, no isolated processed vocal; `Research only`).
2. **Cambridge-MT** — raw multitracks + many community/pro reference mixes (no parameters; `Education only`).
3. **SignalTrain** — dry/wet **with parameters** but one compressor, not vocal-specific.
4. **SAFE-DB** — parameters + descriptors but audio features only (not full audio), crowd-sourced material.
5. **PopBuTFy/NSVB** — amateur vs professional *performances* (different takes, not processed versions of the same take); partially available.
6. **MUSDB18/MoisesDB vocal stems** — processed vocals without their dry originals.
7. **Mix Evaluation Dataset** — same source, many mixes, listener ratings; DAW sessions for some songs existed in the research but audio/parameter redistribution is limited.

Workaround for DrakoTune: manufacture dry→processed pairs itself by running published "vocal chain recipes" (e.g., from mixing literature) over open dry vocals (VocalSet, Vocadito) with Pedalboard — self-generated ground truth with exact parameters, fully owned. This inverts the gap: DrakoTune can *create* the world's first such dataset from CC BY sources (and could publish it for credibility).
---

## 14. Pitch and Intonation Datasets

DrakoTune does not plan pitch correction, but pitch tracking underpins diagnosis (register detection → safe HPF corner; vibrato detection → don't gate tails; voiced/unvoiced segmentation → sibilance analysis).

| Dataset | Contents | Annotations | Access/License |
|---|---|---|---|
| **MedleyDB melody subset** | 108 tracks w/ melody | frame-level F0 of predominant melody | `Research only` |
| **MIR-1K** | 1,000 karaoke clips | frame F0, V/UV, lyrics | free; license unclear for commercial |
| **vocadito** | 40 solo vocal clips | F0, notes, lyrics | **CC BY 4.0** |
| **MDB-stem-synth** | 230 resynthesized stems | **perfect F0** ground truth (analysis/synthesis) | `Research only`; standard for pitch-tracker eval (CREPE used it) |
| **ADC2004 / MIREX05** | tiny legacy melody sets | frame F0 | free, dated |
| **TONAS** | 72 flamenco a cappella excerpts | F0 + notes | `Research only` (COFLA) |
| **DALI v1/v2** | 5k+ songs | lyrics/notes aligned (audio via YouTube links — fragile) | `Research only`; audio not distributed |
| **RWC Music Database** | 315 songs incl. vocals | beats, melody, structure | **paid media fee + agreement (AIST)**; `Permission required` |
| **CSD / GTSinger / M4Singer** | see §6 | phoneme+note-level | `Research only` |

Practical recommendation: use **CREPE** or **pYIN (librosa)** (both permissively licensed) as the diagnosis pitch tracker; validate on vocadito + MDB-stem-synth.

## 15. Vocal Timbre and Technique Datasets

- **VocalSet** — 17 technique labels from professional singers: the de facto technique-classification benchmark (breathy, belt, fry, vibrato, trill…). CC BY 4.0.
- **GTSinger** — 6 techniques × 9 languages with **phoneme-level technique annotations**; research-only.
- **VocalSound (MIT, 2022):** 21k clips of laughter/sighs/coughs/throat clearing/sniffs — non-linguistic vocal sounds, CC BY-SA; useful for detecting non-sung vocal noises (mouth events).
- **Expressive corpora:** RAVDESS (song subset — 24 actors singing with emotions, CC BY-NC-SA), ESD (emotional speech, research).
- **Singer identity:** Artist20/singer-ID literature uses copyrighted music (not distributable). M4Singer/OpenSinger singer labels serve for timbre-profile studies under research terms.
- No public dataset provides **expert GRBAS-style technique/timbre severity labels for popular-music singing.** Gap noted (§31).

DrakoTune uses: build "vocal type profiles" (spectral centroid/rolloff, F0 range, breathiness via harmonic-to-noise ratio) per VocalSet technique class → verify the default chain doesn't damage protected styles (breathy pop, raspy rock, operatic vibrato).

## 16. Rap and Contemporary Vocal Coverage

Direct answer: **no serious public dataset represents contemporary internet/underground vocals** — no raw rap stems corpus, no melodic-rap/trap/rage/hyperpop set, no intentional-Auto-Tune corpus, no bedroom-condenser corpus. Fragments:

- DAMP contains contemporary pop karaoke covers (amateur, smartphone) — nearest neighbor to bedroom recording conditions.
- MUSDB18/MoisesDB contain a handful of hip-hop/rap tracks (processed stems).
- Cambridge-MT has some hip-hop/electronica sessions (education-only).
- Freesound/Looperman a cappellas exist but with inconsistent/unverifiable licensing — **do not scrape**; Looperman terms prohibit redistribution and many uploads have unclear provenance.
- Academic rap datasets focus on lyrics/MIDI, not audio stems.

**Impact on DrakoTune:** genre bias means every published robustness claim will be strongest for sung pop/classical vocals and weakest for the exact user base (rap/melodic-rap home recordists) DrakoTune likely targets. Mitigations: (1) synthetic bedroom-condition simulation over openly licensed vocals; (2) commissioned in-house recordings (a weekend with 3–5 local artists, consent forms, multiple mics — see §32); (3) treat Auto-Tuned/distorted-by-intent inputs as an explicit "do not process / bypass" detection problem from day one.

## 17. Room Acoustics and Reverberation Datasets

| Resource | Contents | License |
|---|---|---|
| **OpenAIR (York):** https://www.openair.hosted.york.ac.uk/ | dozens of measured spaces (halls, churches, rooms), B-format+stereo IRs | per-item CC (mostly CC BY / CC BY-SA) — many `Commercially usable`, check per IR |
| **Aachen Impulse Response (AIR)** | binaural RIRs: office, lecture, stairway, booth | free for research; `Research only` [verify] |
| **BUT ReverbDB** | real rooms, many mic positions + retransmitted speech | CC BY 4.0 [verify] |
| **MIT IR Survey (McDermott)** | 271 single-channel IRs of everyday spaces | free for research |
| **OpenSLR SLR26/SLR28** | simulated + real RIRs + noises (Kaldi standard) | **Apache 2.0 — `Commercially usable`** |
| **ACE Challenge** | RIRs + noise for T60/DRR estimation benchmark | registration, `Research only` |
| **REVERB Challenge** | see §8.3 — speech is LDC-paid | `Permission required` |
| **ReverbFX (2025)** | plugin-derived reverbs for singing dereverb | research [verify] |
| **pyroomacoustics** (MIT) | synthetic shoebox RIR generator | `Commercially usable` |

DrakoTune uses: convolve clean vocals with small-untreated-room IRs (bedroom simulation) at several wet ratios → test (a) reverb-amount diagnosis, (b) whether the current chain (which has no dereverb) at least doesn't worsen reverberant vocals, (c) future dereverb modules. T60/DRR ground truth from IR metadata enables severity-graded testing.

## 18. Noise Datasets

| Dataset | Categories | License | Notes |
|---|---|---|---|
| **DEMAND** | 18 real environments, 16-ch (domestic, office, street, transport) | CC BY-SA `[verify version]` | recording realism high; the standard for speech mixing |
| **MUSAN** | noise + music + speech (~109 h total) | **CC BY 4.0 — `Commercially usable`** | best license; includes hum-like technical noises |
| **FSD50K** | 51k Freesound clips, 200 AudioSet classes | per-clip CC0/CC BY/CC BY-NC | filter to CC0/CC BY subset for commercial-safe use |
| **ESC-50 / UrbanSound8K** | 50 / 10 classes | CC BY-NC(-SA) mostly | research-only in practice |
| **WHAM! noise** | real ambient (cafés, bars) binaural | CC BY-NC 4.0 | research |
| **DNS Challenge noise** | ~180 h, 150 classes | mixed per-source | research pipeline use |
| **AudioSet** | 2M YouTube clips | labels CC BY 4.0; **audio not distributed** | do not scrape audio |
| **Room tone/HVAC/computer-fan** | inside DEMAND (DKITCHEN, OMEETING…), FSD50K classes | as above | covers DrakoTune's bedroom-noise needs |

Attribution requirement is the common thread: CC BY demands credit even in derived benchmark releases.

## 19. Microphone and Device Variation Datasets

- **VOiCES (SRI/Lab41):** speech re-recorded in real rooms through 12 microphones at varied placements — **CC BY 4.0 — `Commercially usable`**; the best open device/room-variation corpus (speech).
- **BUT ReverbDB** retransmissions; **CHiME-5/6** multi-device home audio (research); **DiPCo** (dinner-party, Amazon, CDLA-Permissive [verify]); **SITW/ VoxCeleb** (in-the-wild device variety, celebrity voices — research/identity concerns).
- **Common Voice** — enormous natural consumer-mic diversity (CC0), speech.
- **Vocadito** — the only *singing* set with intentional device variety (CC BY 4.0, but only 40 clips).
- **Same singing performance through multiple microphones: no public dataset exists.** Gap (§31).
- **Simulation path:** microphone coloration can be approximated by measured mic frequency-response EQ curves + distortion/noise-floor models; sources of response data are informal (manufacturer plots, community measurements) — no licensed public corpus. Vendors like Slate/Antelope model mics commercially; nothing open. Honest framing: simulated mic variation tests robustness to *spectral tilt*, not to true transducer nonlinearity.

## 20. Source-Separation Datasets

Covered largely in §7. Benchmark landscape: **MUSDB18(-HQ)** remains the standard benchmark (SDR on 50-track test set); **SDX/MDX challenges (2021/2023, Sony/Moises)** extended it; **MoisesDB** adds stem granularity; **MedleyVox** benchmarks multi-singer separation; **Divide & Remaster (DnR v2/v3)** targets dialog/music/effects (cinematic, CC BY-SA-ish [verify]) — relevant if DrakoTune ever needs "vocal vs everything" pre-separation.

Pretrained models: **Demucs v4/HT-Demucs (MIT)**, **Open-Unmix (MIT)**, **Spleeter (MIT)**, **BS-RoFormer implementations (varied licenses; current SDR leaders)**. Note: model code licenses are permissive, but the models were **trained on non-commercial data (MUSDB18 etc.)** — a legally gray, industry-common situation. Flag for counsel if separation enters the product.

**Product recommendation:** keep separation **out of the current alpha** (artifacts would corrupt cleanup quality judgments); offer later as an explicit preprocessing option for users who upload mixed files, clearly labeled as lossy.

## 21. Synthetic Degradation Resources

Toolchain (all runnable locally, no training):

| Tool | Role | License |
|---|---|---|
| **audiomentations** | noise/gain/pitch/clip/mp3-compression/RIR augmentation, reproducible seeds | MIT |
| **Pedalboard** | musically realistic degradation (bad EQ, overcompression, distortion, bitcrush) — same engine as the product | **GPL-3.0** |
| **FFmpeg / SoX** | codec round-trips (MP3/AAC/Opus at low bitrate), resampling, clipping via gain | LGPL/GPL |
| **pyroomacoustics** | parametric room simulation (T60 sweep) | MIT |
| **torchaudio** | codec, resampling, convolution, SoX effects | BSD-2 |
| **Audio Degradation Toolbox** | canonical degradation recipes | GPL (MATLAB) / ports |
| **DNS-Challenge synthesizer** | large-scale noisy-mixture recipes | MIT scripts |

Proposed severity grid (documented, seeded, versioned): noise at SNR {30, 20, 10, 5} dB × {room tone, HVAC, street, hum}; reverb at wet {10, 25, 50}% × {booth, bedroom, hall} IRs; clipping at {1, 3, 6, 10}% samples clipped; low level at {−30, −40} LUFS; sibilance exaggeration via +6/+12 dB 6–9 kHz shelf on unvoiced frames; codec at MP3 {64, 96} kbps; proximity via +6 dB <200 Hz shelf.

**Honesty requirement:** synthetic defects are *models* of real defects. Publish claims as "improves recordings degraded with X" until validated on real-world sets (DAMP, SingVERSE); never present synthetic-only results as real-world proof.

## 22. Professional-versus-Amateur Research

- **Mix Evaluation Dataset** (§12): multiple engineers, same songs, preference + free-text — the strongest public evidence base for what "more professional" means operationally (findings from De Man's thesis: preferred mixes correlate with controlled LF, vocal presence, moderate dynamics — directly supports DrakoTune's chain design).
- **PopBuTFy/NSVB:** amateur vs professional *performances* (voice quality, not engineering) — partially available.
- **DAMP + Intonation dataset:** amateur population with popularity ("loves") signals — weak, confounded preference labels.
- **MUSHRA-style mastering studies** exist in AES papers but their audio is rarely released.
- **Measurability verdict:** "cleaner" (noise floor, SNR), "less harsh" (2–5 kHz energy + listener ratings), "more balanced" (long-term spectrum vs genre reference), "smoother" (dynamics variance + ratings) are measurable with defined proxies + blinded listening. **"More professional" is only measurable as blinded listener preference vs professional references** — do not claim it from signal metrics alone.

## 23. Perceptual Descriptor Datasets

- **SAFE-DB** — descriptor→parameter-space mappings ("warm," "bright," "harsh" clusters in EQ space; Stables et al. 2014/2016 showed descriptors form reasonably consistent clusters).
- **SocialFX / SocialEQ (Northwestern, Pardo lab):** crowdsourced adjective→EQ/reverb mappings (~thousands of terms); research; code/data availability intermittent [verify].
- **Mix Evaluation Dataset comments** — 13k statements, mineable vocabulary of mix criticism.
- **Timbre semantics literature** (Zacharakis, Saitis) — small controlled datasets; research.
- **Cambridge Music Technology "Mixing Secrets" critiques** — qualitative, not a dataset.
- Consistency verdict: descriptors like *bright/dark/warm* are fairly consistent across listeners; *harsh, muddy, boxy* are moderately consistent and frequency-band-linkable (harsh≈2–5 kHz, muddy≈150–400 Hz, boxy≈300–600 Hz); *professional/polished* are holistic and listener/genre-dependent → suitable only for learned models or human panels. Deterministic thresholds are defensible for the band-linkable terms if calibrated per genre and validated with listeners.

## 24. Clinical Voice Datasets and Restrictions

**Position: exclude clinical corpora from DrakoTune product development.** They are speech (sustained vowels/sentences), collected under medical ethics frameworks, often with license terms prohibiting non-research use, and using them risks (a) license breach, (b) the appearance of medical diagnosis. DrakoTune must never suggest a user's *voice* (as opposed to their *recording*) is defective.

For completeness: **Saarbruecken Voice Database** (~2,000 speakers, healthy+pathological German speech; free registration, research emphasis; now also mirrored on Zenodo — license terms should be re-read before any use); **MEEI/KayPENTAX** (commercial purchase, clinical); **AVPD, VOICED (PhysioNet), TORGO** (research/credentialed). GRBAS/CAPE-V-rated corpora are mostly institution-locked. The only legitimate transfer is conceptual: perceptual roughness/breathiness measures (jitter, shimmer, HNR) are useful *signal features* implementable from scratch (Praat/parselmouth, librosa) without touching clinical data.

## 25. Open-Source Tools and Repositories

| Repo | Purpose | Lang | License | Maintained | DrakoTune relevance |
|---|---|---|---|---|---|
| github.com/spotify/pedalboard | DSP chain (in product) | Py/C++ | **GPL-3.0** | active | current core — license review advised |
| ffmpeg.org | normalize, ebur128 loudness, codecs | C | LGPL/GPL | active | current core |
| github.com/librosa/librosa | feature extraction (diagnosis backbone) | Py | ISC | active | **adopt now** |
| github.com/csteinmetz1/pyloudnorm | LUFS measurement/normalization | Py | MIT | stable | **adopt now** |
| github.com/google/visqol | reference-based quality (speech+audio modes) | C++ | Apache-2.0 | moderate | **adopt now** |
| github.com/microsoft/DNS-Challenge | DNSMOS models + degradation synthesizer | Py | MIT | active | **adopt now** (DNSMOS ONNX) |
| github.com/gabrielmittag/NISQA | no-reference speech quality (multi-dim) | Py | MIT | stable | adopt now |
| github.com/iver56/audiomentations | reproducible degradation | Py | MIT | active | **adopt now** |
| github.com/LCAV/pyroomacoustics | room simulation | Py | MIT | active | adopt now |
| github.com/marl/crepe (+ librosa pYIN) | pitch tracking | Py | MIT | stable | Phase 2 diagnosis |
| github.com/snakers4/silero-vad | voice activity detection | Py | MIT | active | Phase 2 (analyze only voiced regions) |
| github.com/YannickJadoul/Parselmouth (Praat) | jitter/shimmer/HNR features | Py | GPL-3.0 (Praat) | active | Phase 2 |
| github.com/facebookresearch/demucs | source separation | Py | MIT | community forks | future preprocessing |
| github.com/sigsep/open-unmix-pytorch | separation baseline | Py | MIT | stable | future |
| github.com/deezer/spleeter | separation (legacy) | Py | MIT | maintenance mode | reference only |
| github.com/Rikorose/DeepFilterNet | real-time deep noise suppression | Rust/Py | MIT/Apache dual | active | future denoise module (license-friendly!) |
| github.com/xiph/rnnoise | lightweight classical+NN denoise | C | BSD | active | future low-cost denoise |
| github.com/speechbrain/speechbrain | enhancement/eval recipes | Py | Apache-2.0 | active | future ML |
| github.com/asteroid-team/asteroid | separation/enhancement toolkit | Py | MIT | slower | future ML |
| github.com/sergree/matchering | reference matching/mastering | Py | **GPL-3.0** | stable | study, don't embed |
| github.com/csteinmetz1/automix-toolkit | automatic mixing models/datasets | Py | Apache-2.0 [verify] | research | Phase 7 |
| github.com/mtg/essentia | large audio-analysis suite | C++/Py | **AGPL-3.0** | active | avoid embedding in commercial product; fine for offline research |
| github.com/pytorch/audio (torchaudio) | I/O, SQUIM metrics, effects | Py | BSD-2 | active | beta |
| github.com/sebastianewert/audio-degradation-toolbox | canonical degradations | MATLAB | GPL | dormant | recipe reference (labeled: dormant) |

---

## 26. Master Dataset Comparison

Numbers are official where published; "~" marks community-reported figures; blank = not published. Where versions conflict (e.g., MedleyDB 1.0 vs 2.0 track counts, DAMP archive sizes by subset) the per-section text explains the discrepancy — do not cite this table without the section caveats.

| Dataset | Data Type | Vocal/Speech | Subjects/Artists | Tracks/Files | Duration | Isolated Vocals | Clean/Degraded Pairs | Dry/Wet Pairs | Labels | Sample Rate | License | Commercial Use | Registration | Download Size | Access Difficulty | Best Use | Limitations | Recommended |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| VocalSet | solo singing | vocal | 20 (9M/11F) | ~3,560 files | 10.1 h | ✔ | ✘ (clean only) | ✘ | technique, vowel, singer | 44.1 kHz | CC BY 4.0 | ✔ | ✘ | ~4–5 GB | easy | degradation substrate; technique robustness | exercises, trained singers | ★★★★★ |
| Vocadito | solo singing | vocal | ~29 singers | 40 clips | ~15 min | ✔ | ✘ | ✘ | F0, notes, lyrics | varied | CC BY 4.0 | ✔ | ✘ | <1 GB | easy | device/skill realism, pitch eval | tiny | ★★★★ |
| SingVERSE | real degraded singing + clean refs | vocal | — | 3,929 pairs | 18.14 h | ✔ | ✔ (real) | ✘ | 19 scenario labels | studio/48k | [verify on HF] | likely ✘ | HF account | ~20 GB est. | easy | primary before/after validation | eval-scale; new (2025) | ★★★★★ |
| DAMP-MVP et al. | amateur karaoke | vocal | thousands | 34,000+ perf. | 1000s h | mostly | ✘ | ✘ | singer, gender, region, loves | compressed | Smule research license | ✘ | email + agreement | 100s GB (subsets less) | medium | real-world input distribution | no clean refs; compression | ★★★★★ (research) |
| GTSinger | solo singing | vocal | 20 | — | 80.59 h | ✔ | ✘ | ✘ | techniques, scores, phonemes | 48 kHz | CC BY-NC-SA 4.0 | ✘ | HF | ~100 GB est. | easy | multilingual robustness | research-only | ★★★★ |
| M4Singer | solo singing | vocal | 20 (SATB) | ~700 songs | 29.77 h | ✔ | ✘ | ✘ | pitch, notes, lyrics | 48 kHz | research agreement | ✘ | form | ~30 GB | medium | register (SATB) testing | Mandarin, research-only | ★★★ |
| OpenSinger | solo singing | vocal | 66 | — | ~50 h | ✔ | ✘ | ✘ | singer, lyrics | 24–44.1k | research | ✘ | request | ~30 GB | medium | singer diversity | Mandarin, research-only | ★★★ |
| CSD | solo singing | vocal | 1 | 100 songs | ~4 h | ✔ | ✘ | ✘ | MIDI, phonemes | 44.1 kHz | CC BY-NC-SA 4.0 | ✘ | ✘ | ~2 GB | easy | annotated clean substrate | single singer | ★★★ |
| NHSS | singing + parallel speech | both | 10 | 100 songs | 7 h | ✔ | ✘ | ✘ | word/utterance aligns | 48 kHz | NUS EULA (research) | ✘ | request | ~10 GB | medium | speech-vs-singing analysis | small | ★★★ |
| MIR-1K | karaoke clips | vocal | 19 | 1,000 clips | 2.2 h | ✔ (channel) | ✘ | ✘ | F0, V/UV, lyrics | 16 kHz | unclear | ? | ✘ | ~1 GB | easy | amateur pitch/VAD eval | 16 kHz | ★★★ |
| iKala | karaoke | vocal | — | 352 clips | — | ✔ | ✘ | ✘ | F0, lyrics | 44.1 kHz | discontinued | ✘ | — | — | **unavailable** | — | do not plan | ✘ |
| MUSDB18-HQ | multitrack stems | vocal in mix | ~150 artists | 150 tracks | ~10 h | ✔ (processed) | ✘ | ✘ | genre | 44.1 kHz | mostly CC BY-NC-SA | ✘ | Zenodo request | 22.7 GB | easy | pro-vocal spectral targets; separation | stems are wet | ★★★★ |
| MedleyDB 1+2 | multitrack raw stems | vocal in mix | — | 196 tracks | ~12 h | ✔ (raw!) | ✘ | partial (raw stem vs mix) | melody F0, instrument | 44.1 kHz | CC BY-NC-SA | ✘ | request | ~100 GB | medium | raw-vs-mixed vocal deltas | research-only | ★★★★ |
| MoisesDB | multitrack stems | vocal in mix | 45+ artists | 240 tracks | ~14 h | ✔ (lead/BG split) | ✘ | ✘ | genre, stem taxonomy | 44.1 kHz | CC BY-NC-SA 4.0 | ✘ | signup | ~80 GB | easy | genre-diverse stems | wet stems, research | ★★★★ |
| Cambridge-MT | raw multitracks + ref mixes | vocal in mix | 100s of artists | 600+ sessions | 100s h | ✔ (raw takes) | ✘ | ✔ (raw vs mixed song) | genre | 44.1–96 kHz | education-only | ✘ (permission) | ✘ | per-song 0.1–3 GB | easy | internal defect gallery, engineer study | manual use only | ★★★★ |
| Mix Evaluation Dataset | mixes + ratings | vocal in mix | 18 songs × ~10 mixes | 180+ mixes | ~12 h | partial | ✘ | ✔ (same source, many mixes) | 13k listener statements | 44.1 kHz | per-song, research | ✘ | ✘ | ~10 GB | medium | preference evidence, vocabulary | licensing patchwork | ★★★★ |
| VoiceBank-DEMAND | paired speech | speech | 30 speakers | 12,396 utts | ~15 h | n/a | ✔ (synthetic, standard) | ✘ | SNR, noise type | 48/16 kHz | CC BY 4.0 | ✔ | ✘ | ~3 GB | easy | denoise/gate calibration | speech, 16k convention | ★★★★★ |
| DNS Challenge 5 | speech+noise+RIR | speech (+some singing) | 1000s | — | 100s h | n/a | ✔ (synthesizer) | ✘ | P.835 MOS (test) | 48 kHz | per-component | partial | ✘ | 100s GB | medium | degradation material | bulk; license patchwork | ★★★★ |
| EARS | anechoic speech | speech | 107 | — | 100 h | n/a | ✔ (EARS-WHAM/Reverb) | ✘ | styles | 48 kHz | CC BY-NC 4.0 [verify] | ✘ | ✘ | ~100 GB | easy | full-band enhancement benchmark | speech, NC | ★★★ |
| VCTK | clean speech | speech | 110 | 44k utts | 44 h | n/a | ✘ | ✘ | accents | 48 kHz | CC BY 4.0 | ✔ | ✘ | ~11 GB | easy | clean speech substrate | speech | ★★★ |
| VOiCES | re-recorded speech | speech | 300 | ~375k files | 1000s h | n/a | ✔ (source vs re-recorded) | ✘ | mic, room, distance | 48 kHz | CC BY 4.0 | ✔ | ✘ | ~400 GB (subsets) | medium | device/room variation, commercially usable | speech | ★★★★ |
| MUSAN | noise/music/speech | — | — | ~2,016 files | 109 h | — | — | — | class | varied | CC BY 4.0 | ✔ | ✘ | 11 GB | easy | degradation noise source | — | ★★★★ |
| DEMAND | environment noise | — | — | 18 envs × 16 ch | 1.5 h/env | — | — | — | environment | 48 kHz | CC share-alike [verify] | likely ✔ w/ attribution | ✘ | ~6 GB | easy | realistic noise beds | few classes | ★★★★ |
| FSD50K | labeled sounds | — | — | 51,197 clips | 108 h | — | — | — | 200 classes, per-clip CC | 44.1 kHz | per-clip CC0/BY/BY-NC | partial | ✘ | ~30 GB | easy | defect exemplars (filtered subset) | license filtering needed | ★★★ |
| OpenSLR-28 RIR+noise | RIRs | — | — | — | — | — | — | — | room type | 16 kHz | Apache 2.0 | ✔ | ✘ | ~2 GB | easy | reverb simulation | 16 kHz sims | ★★★ |
| OpenAIR | measured RIRs | — | — | dozens of spaces | — | — | — | — | space metadata | up to 96 kHz | per-item CC | mostly ✔ | ✘ | small | easy | high-quality reverb degradation | few small rooms | ★★★★ |
| BUT ReverbDB | RIRs + retransmitted speech | speech | — | 1,300+ RIRs | — | — | ✔ | — | room, position | 16 kHz | CC BY 4.0 [verify] | ✔ | ✘ | ~40 GB | easy | real-room testing | speech retransmissions | ★★★ |
| SAFE-DB | FX parameters + descriptors | — | crowd | 1000s entries | n/a (features) | — | — | ✔ (feature-level) | descriptor terms + params | n/a | academic [verify] | ? | ✘ | small | easy | descriptor→EQ evidence | no raw audio | ★★★★ |
| SignalTrain | dry/wet compressor audio | — | — | — | ~20 h | — | — | ✔ (with knob settings) | LA-2A settings | 44.1 kHz | research [verify] | ✘ | ✘ | ~20 GB | easy | compression ground truth | one effect | ★★★ |
| SingMOS(-Pro) | singing MOS ratings | vocal | — | 3,421 / 7,981 clips | 4.25 h+ | ✔ | — | — | MOS (≥5 raters) | 16–44.1k | [verify on HF] | ? | HF | ~2 GB | easy | calibrate singing-quality proxies | synthesis-focused | ★★★ |
| Saarbruecken SVD | clinical speech | speech | ~2,000 | ~2k sessions | — | n/a | ✘ | ✘ | pathology | 50 kHz | research emphasis | ✘ | registration | ~10 GB | medium | **excluded from product** | clinical/ethical | ✘ for product |

## 27. Benchmark and Metric Comparison

| Benchmark / Metric | Measures | Speech | Music | Singing | Reference Required | Open Source | Commercial Use | Human Correlation | Real-Time Feasible | Recommended for DrakoTune |
|---|---|---|---|---|---|---|---|---|---|---|
| PESQ (P.862) | speech quality | ✔ | ✘ | ✘ | ✔ | impl. exists; algorithm ITU-encumbered | restricted | high (speech) | ✔ | speech tests only, research |
| POLQA (P.863) | speech quality | ✔ | ✘ | ✘ | ✔ | ✘ | paid | high (speech) | ✔ | no |
| STOI / ESTOI | intelligibility | ✔ | ✘ | ✘ | ✔ | ✔ (MIT) | ✔ | high (intelligibility) | ✔ | speech tests only |
| SI-SDR / SDR / SIR / SAR | signal fidelity / separation | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | moderate | ✔ | **yes — now** (synthetic pairs) |
| ViSQOL v3 (speech & audio modes) | perceptual similarity | ✔ | ✔ | ~ | ✔ | Apache-2.0 | ✔ | good | near | **yes — now** |
| DNSMOS (P.835) | no-ref speech MOS (SIG/BAK/OVRL) | ✔ | ✘ | ~unvalidated | ✘ | MIT | ✔ | high (speech) | ✔ | **yes — now, as proxy w/ caveats** |
| NISQA | no-ref MOS + 4 dimensions | ✔ | ✘ | ~ | ✘ | MIT | ✔ | high (speech) | ✔ | yes — now |
| TorchAudio-SQUIM | no-ref PESQ/STOI/SI-SDR estimates | ✔ | ✘ | ~ | ✘ | BSD-2 | ✔ | good (speech) | ✔ | beta |
| SingMOS predictor | no-ref singing MOS | ✘ | ✘ | ✔ (synthesized) | ✘ | research | ? | moderate | ✔ | research |
| Audiobox-Aesthetics | production quality/enjoyment | ✔ | ✔ | ~ | ✘ | [verify weights license] | ? | emerging | ✔ | research/beta |
| MUSHRA (BS.1534) | subjective, mid-quality anchors | ✔ | ✔ | ✔ | hidden ref | webMUSHRA (open) | ✔ (method) | is the ground truth | ✘ | **yes — beta claims** |
| ITU-R BS.1284 / pairwise A/B | subjective preference | ✔ | ✔ | ✔ | ✘ | Go Listen / webMUSHRA | ✔ | ground truth | ✘ | **yes — now (internal)** |
| PEAQ (BS.1387) | codec impairment | ~ | ✔ | ~ | ✔ | GPL impl | restricted | dated | ✔ | no |
| FAD | corpus-level distribution distance | ~ | ✔ | ~ | corpus ref | Apache | ✔ | moderate (set-level) | ✘ | research |
| CLAP similarity | semantic embedding similarity | ~ | ✔ | ~ | optional | Apache | ✔ | weak-moderate | ✔ | research |
| EBU R128 LUFS/LRA/TP | loudness/dynamics | ✔ | ✔ | ✔ | ✘ | ffmpeg/pyloudnorm | ✔ | n/a (instrument) | ✔ | **yes — mandatory now** |
| Crest factor, band ratios, flatness | signal statistics | ✔ | ✔ | ✔ | ✘ | librosa | ✔ | indirect | ✔ | **yes — now (diagnosis)** |
| SRMR | reverberation amount | ✔ | ✘ | ~ | ✘ | free | ✔ | moderate (speech) | ✔ | beta |
| MUSDB18 SDR benchmark | separation leaderboard | — | ✔ | ✔ | ✔ | ✔ | data ✘ | — | ✘ | future (separation) |

## 28. Licensing and Commercial-Use Analysis

Tiering for DrakoTune (rule: *classify by the most restrictive component actually used*):

- **Tier A — `Commercially usable`, can ship in automated tests / redistributable benchmarks (with attribution):** VocalSet, Vocadito, VoiceBank-DEMAND, VCTK, LibriSpeech/LibriTTS, Common Voice (CC0), MUSAN, VOiCES, OpenSLR-28, most OpenAIR IRs (check per item), FSD50K CC0/CC-BY subset. Tools: librosa, pyloudnorm, ViSQOL, DNSMOS code, NISQA, audiomentations, pyroomacoustics, torchaudio, Demucs/Open-Unmix code.
- **Tier B — `Research only` / NC: internal evaluation and papers; do not redistribute, do not ship, get legal sign-off for commercial R&D use:** MUSDB18(-HQ), MedleyDB, MoisesDB, M4Singer, OpenSinger, GTSinger, CSD, NHSS, DAMP (explicit agreement), EARS, WHAM!, SingVERSE (pending license check), SignalTrain, SingMOS, ODAQ.
- **Tier C — `Education only` / `Permission required`:** Cambridge-MT (contact contributors for research/commercial), Shaking Through, RWC (paid), REVERB/WSJ (LDC paid), ACE (registration).
- **Tier D — excluded:** iKala (unavailable), clinical corpora (SVD/MEEI/VOICED — ethical+license), scraped a cappellas (Looperman/YouTube rips — unlicensed), AudioSet audio (not distributed).

Cross-cutting cautions: (1) "downloadable on Zenodo/HF" ≠ licensed for commercial use — always read the record's license field; (2) CC-NC applies to DrakoTune even for internal R&D by a strict reading — the industry commonly tolerates internal evaluation, but a commercial product's *published claims* should rest on Tier A + proprietary data; (3) attribution (CC BY) must be honored in any published benchmark or paper; (4) pretrained separation/enhancement models carry data-provenance ambiguity; (5) hosting reliability: Zenodo and HF are durable; personal/university pages (Open Multitrack Testbed, SAFE, MIR-1K) decay — mirror internally (where license permits) upon first download.

## 29. DrakoTune Validation Strategy

Answering the fifteen questions:

1. **First test vocals:** VocalSet (clean substrate) + Vocadito (device realism) + 50–100 DAMP clips (real-world) + SingVERSE pairs (real degraded/clean) + 20 Cambridge-MT raw vocal takes (manual listening only).
2. **Legally usable audio:** Tier A above; DAMP/SingVERSE/Cambridge-MT under their respective terms for internal evaluation.
3. **Redistributable in automated tests (CI, shipped fixtures):** only Tier A (VocalSet, Vocadito, VoiceBank-DEMAND, MUSAN, OpenSLR RIRs + self-generated degradations of them).
4. **Manual download only:** DAMP (email agreement), MedleyDB/MUSDB18 (Zenodo request), Cambridge-MT (site), M4Singer/OpenSinger (forms).
5. **Research-but-not-ship:** all Tier B.
6. **Synthetic degradation:** seeded audiomentations/pyroomacoustics/FFmpeg pipeline per §21; degradation recipes versioned in git; one JSON manifest per degraded clip.
7. **Severities:** the §21 grid — 4 SNRs × 4 noise types, 3 reverb wets × 3 rooms, 4 clipping levels, 2 low-level settings, 2 codec rates, sibilance/proximity shelves. ≈ start with ~5 defect families × 3 severities to keep the matrix tractable.
8. **Objective metrics:** LUFS-I/LRA/true peak (pre/post), crest factor, band-energy ratios (LF <120 Hz, mud 250–500 Hz, harsh 2–5 kHz, sibilant 5–10 kHz), spectral flatness in pauses (noise floor), SI-SDR & ViSQOL vs clean refs (synthetic + SingVERSE), DNSMOS/NISQA as no-reference proxies.
9. **Listening-test format:** internal alpha — blinded pairwise A/B (processed vs raw, randomized order, forced choice + 5-point preference strength + free-text artifact box). Beta claims — MUSHRA with hidden reference/anchor via webMUSHRA or Go Listen.
10. **Loudness matching: mandatory** — normalize both stimuli to −23 LUFS (or −18 for casual listening) integrated, true peak ≤ −1 dBTP, *before* comparison; report both matched and unmatched deltas. Louder ≈ "better" bias otherwise invalidates everything.
11. **Bias reduction:** blind labels, randomized A/B order, include 10% catch trials (identical pairs), include some "no processing needed" clean inputs, use listeners not involved in DSP tuning, pre-register the success criterion.
12. **Clip count for a meaningful first test:** ~100–150 clips of 10–20 s (≈ 5 defect families × 3 severities × ~8 source vocals + 20 real-world clips), rated by ≥8–10 listeners → detects a preference effect of ~65%+ win rate with reasonable power. Smaller (30 clips, 5 listeners) is fine for a smoke test, not for claims.
13. **Defects the current chain should improve:** LF rumble/proximity (HPF), moderate harshness (upper-mid cut), inconsistent level (compression + normalization), low-level background noise in pauses (gate), low recording level (gain). 
14. **Defects it must NOT claim to improve:** reverb (no dereverb module), broadband noise during singing (gate can't help), clipping/distortion repair, sibilance (no de-esser yet), hum (no notch), codec artifacts, pitch issues.
15. **Successful alpha definition (proposed):** on the defect families in (13): blinded listener preference for processed ≥ 65% with p < 0.05; no objective regressions (true peak > −1 dBTP, added noise-floor, ViSQOL drop vs clean > threshold on synthetic pairs); on clean inputs, listeners prefer processed ≤ 55% *or* rate it "no difference" (i.e., the chain does no harm); zero clips with reported gating/pumping artifacts at default preset.

**Evaluation matrix (per clip record):** {vocal type, genre, register (est. F0 median), device class, room type, defect type, defect severity, input LUFS, preset, objective deltas (all §29.8 metrics), listener preference %, artifacts reported, pass/fail}.

## 30. Dataset Rankings

Scores 1–5; weights: current-alpha usefulness ×3, legal usability ×3, vocal relevance ×2, realism ×2, others ×1. (Weighted max = 65.)

| Rank | Dataset | Audio qual. | Vocal rel. | Realism | Annot. | Genre div. | Singer div. | Defect div. | Clean ref | Legal | Access | Practicality | Alpha use | Future use | **Weighted** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | VocalSet | 5 | 5 | 2 | 4 | 2 | 4 | 1 | 5 | 5 | 5 | 5 | 5 | 4 | **57** |
| 2 | SingVERSE | 4 | 5 | 5 | 3 | 3 | 3 | 5 | 5 | 3 | 5 | 4 | 5 | 5 | **56** |
| 3 | VoiceBank-DEMAND | 4 | 2 | 3 | 4 | 1 | 3 | 3 | 5 | 5 | 5 | 5 | 4 | 3 | **50** |
| 4 | DAMP | 2 | 5 | 5 | 3 | 3 | 5 | 4 | 1 | 2 | 3 | 3 | 5 | 5 | **49** |
| 5 | Vocadito | 3 | 5 | 4 | 4 | 3 | 4 | 2 | 4 | 5 | 5 | 5 | 3 | 3 | **49** |
| 6 | MUSDB18-HQ | 4 | 4 | 4 | 2 | 3 | 4 | 2 | 3 | 2 | 4 | 4 | 3 | 5 | **44** |
| 7 | Cambridge-MT | 4 | 5 | 5 | 2 | 4 | 5 | 4 | 3 | 2 | 4 | 3 | 4 | 3 | **44*** |
| 8 | GTSinger | 5 | 5 | 2 | 5 | 3 | 3 | 1 | 5 | 2 | 5 | 3 | 3 | 5 | **43** |
| 9 | MedleyDB | 4 | 4 | 4 | 4 | 3 | 4 | 2 | 3 | 2 | 3 | 3 | 3 | 4 | **42** |
| 10 | MoisesDB | 4 | 4 | 4 | 3 | 4 | 4 | 2 | 3 | 2 | 4 | 3 | 3 | 4 | **42** |
| 11 | Mix Evaluation DS | 4 | 4 | 4 | 5 | 3 | 3 | 3 | 3 | 2 | 3 | 4 | 3 | 4 | **42** |
| 12 | MUSAN/DEMAND (noise) | 4 | n/a | 4 | 3 | n/a | n/a | 4 | n/a | 5 | 5 | 5 | 4 | 3 | **(enabler)** |

\*Cambridge-MT score assumes manual internal use within education terms.

## 31. Gap Analysis

| Gap | Why it matters | Blocks alpha? | Synthetic fix? | Collect proprietary? |
|---|---|---|---|---|
| No raw→professionally-mixed vocal dataset with parameters | Can't learn/verify "what pros actually do" | No (alpha is deterministic) | Partially — self-generate recipes (§13) | **Yes — flagship opportunity** |
| No vocal harshness benchmark | "Less harsh" claim lacks external ground truth | No — use band proxy + listeners | Partially (exaggerated-EQ stimuli + ratings) | Yes (severity labels) |
| No sibilance-severity benchmark | De-esser development/validation | No (de-esser is Phase 4) | Yes (shelf-boost stimuli) + listener calibration | Yes |
| No bedroom-rap / melodic-rap / underground-vocal dataset | Target-user mismatch; genre-biased claims | **Partially** — alpha claims must be genre-scoped | Weakly (condition simulation ≠ style) | **Yes — urgent by beta** |
| No same-performance multi-microphone singing corpus | Device-robustness evidence | No | Tilt/noise simulation only | Yes (cheap to record) |
| No standardized vocal smoothness / "professionalism" metric | Marketing claims unverifiable objectively | No — human tests substitute | No | Preference data enables a learned score later |
| No vocal-processing preference dataset | Preset tuning is guesswork | No | No | **Yes — every listening test should be logged as future data** |
| No defect→corrective-DSP mapping dataset | Adaptive DSP (Phase 3) has no external prior | No | Partially (SAFE-DB hints) | Yes (engineer annotations) |
| No intentional-distortion vs defect discrimination data | Overprocessing risk on stylized vocals | **Yes, partially** — mitigate with conservative bypass rules | No | Yes |
| Singing-enhancement training-scale paired data | Future ML | No | Yes (synthesis is the field's norm) | Later |

## 32. Proprietary Dataset Strategy

**Stage plan:**
1. **Internal Alpha Evaluation Set (now):** curated Tier A clips + seeded synthetic degradations + manifests. Fully owned/CC-compliant; shippable in CI.
2. **Controlled Degradation Benchmark (Phase 5):** frozen version of (1) with published recipes — a credibility asset; consider public release (DrakoTune would own the first open vocal-defect benchmark).
3. **Artist-Contributed Vocal Corpus (Phase 6):** 20–50 consenting artists upload raw takes (+optional instrumentals/mixes). Target the underrepresented styles: rap, melodic rap, trap, R&B, hyperpop, bedroom pop.
4. **Engineer-Annotated Processing Dataset:** 2–3 mix engineers process contributed vocals in-DAW with logged chains/parameters + rationale notes; artists rate results.
5. **Genre-Specific Vocal Benchmark** and **Production-Quality Preference Dataset:** accumulate every blinded A/B result (stimuli hashes, listener IDs, preferences) from day one — this becomes the preference-modeling dataset for free.

**Collection protocol:** multiple takes per artist; ≥2 microphones (one budget USB/phone + one studio condenser) recording *simultaneously* where possible (closes the multi-mic gap); room described (treated/untreated/booth); dry export mandatory, processed export optional; input gain and device metadata captured automatically from upload questionnaire.

**Metadata & labels:** as specified in the brief — genre, style, register, device/mic/interface, room, distance, gain, sample rate/bit depth, prior processing, known defects, artist intent; severity labels (0–3) for noise/harshness/sibilance/clipping/reverb/mud/boxiness/dynamics/tonal imbalance; overall quality; processing-required and intensity; preferred output. Annotation: engineer + artist + general listeners, pairwise blind A/B, artifact reports, ≥2 raters per item with inter-rater agreement (Krippendorff's α) tracked; low-agreement labels flagged, not averaged silently.

**Legal/ethical requirements (non-negotiable):** written consent covering commercial use and (separately, opt-in) model training; artists retain ownership of compositions, license recordings to DrakoTune for defined purposes; voice-identity protections — no cloning, no biometric use, no impersonation, contractual + technical (no TTS/SVC training on the corpus without separate consent); withdrawal and deletion procedures with propagation to derived artifacts; clear statement of ownership of processed outputs (artist owns them); minors excluded or guardian consent; store consent records with the audio.

## 33. Integration Roadmap

- **Phase 1 — Real Vocal Alpha Validation (weeks 1–4):** acquire Tier A sets + DAMP + SingVERSE; build seeded degradation corpus (~150 clips); implement metric suite (LUFS/TP/LRA, band ratios, crest, SI-SDR, ViSQOL, DNSMOS, NISQA); run chain; loudness-matched blinded A/B with 8–10 listeners; log failures per evaluation matrix; tune preset; write up against §29.15 success criteria.
- **Phase 2 — Vocal Diagnosis (weeks 4–8):** deterministic detectors for: LF excess, mud, boxiness, harshness, sibilance, noise floor, reverb estimate (SRMR-class), clipping, low level, dynamic range extremes, tonal imbalance vs genre profile; plus pitch/VAD (pYIN/CREPE + silero-vad) for register-aware analysis. Calibrate thresholds on the degradation corpus (known ground truth); validate on DAMP/SingVERSE.
- **Phase 3 — Adaptive Deterministic DSP:** rule table mapping diagnosis → parameter ranges with confidence scores; hard safety bounds (max cut/boost, max GR); bypass when confidence low or input clean (the "first, do no harm" rule from §29.15); genre-aware constraints from stem-derived profiles (MUSDB18/MoisesDB statistics — research-tier, so keep profiles as aggregate statistics, reviewed by counsel).
- **Phase 4 — Expanded Processing:** de-esser (validate on sibilance-exaggerated stimuli + listener tests), dynamic EQ/resonance suppression, plosive/breath control, hum notch, loudness targeting, clip detection with repair *referral* (declipping is Phase 7 ML territory); DeepFilterNet/RNNoise as optional permissively-licensed denoise.
- **Phase 5 — Formal Benchmarking:** freeze benchmark v1; MUSHRA panel; publish methodology + results (only Tier A / proprietary audio in any public artifact).
- **Phase 6 — Proprietary Collection:** per §32.
- **Phase 7 — ML (only after deterministic limits documented):** defect classification, quality prediction (fine-tune NISQA/DNSMOS-style heads on proprietary labels), parameter recommendation, learned denoise/dereverb (SingVERSE + synthetic pairs), preference modeling from accumulated A/B logs.

## 34. Final Recommendations

**Top 10 to access immediately (alpha, no training):** 1) VocalSet — Zenodo direct, CC BY, ~5 GB; first experiment: degrade 20 clips with the §21 grid, process, A/B. 2) SingVERSE — HF; first experiment: run chain on 100 real pairs, measure ViSQOL/SI-SDR toward clean. 3) Vocadito — Zenodo; device-realism smoke test. 4) VoiceBank-DEMAND — Edinburgh; gate/denoise calibration on known SNRs. 5) DAMP-1k/-VP1k then full via Smule email — realism panel. 6) MUSAN — degradation noise. 7) OpenAIR + OpenSLR-28 — reverb material. 8) MUSDB18-HQ — pro-vocal spectral targets. 9) Cambridge-MT (5–10 sessions) — internal defect gallery. 10) Mix Evaluation Dataset — mine 13k comments for the descriptor lexicon.

**Top 10 for current DSP validation:** SingVERSE; VoiceBank-DEMAND; VocalSet(+synthetic); Vocadito(+synthetic); DAMP; DEMAND; MUSAN; OpenAIR/OpenSLR RIRs; MUSDB18-HQ vocal stems; EARS-WHAM/-Reverb (full-band stress, research).

**Top 10 for vocal diagnosis:** synthetic degradation corpus (own); SingVERSE (scenario labels); DAMP (real defects); VoiceBank-DEMAND (SNR ground truth); BUT ReverbDB / ACE (T60/DRR ground truth); VOiCES (mic/distance labels); MIR-1K (V/UV + amateur); vocadito + MDB-stem-synth (pitch-tracker validation); NISQA corpus (quality-dimension calibration); Cambridge-MT (defect exemplars).

**Top 10 for future vocal enhancement:** SingVERSE; GTSinger; M4Singer; OpenSinger; VocalSet; EARS; DNS Challenge; PopBuTFy (if released); CSD; DAMP-VSEP.

**Top 10 for future automatic mixing:** Mix Evaluation Dataset; SAFE-DB; MedleyDB; Cambridge-MT (with permissions); MoisesDB; MUSDB18-HQ; SignalTrain; IDMT-SMT-Audio-Effects; DeepAFx-ST assets; FxNorm-automix statistics.

**Top 10 for source separation:** MUSDB18-HQ; MoisesDB; MedleyDB; DSD100; MedleyVox; DnR; DAMP-VSEP; Slakh (accompaniment); jaCappella (ensembles); SDX challenge data.

**Top 10 for genre/style expansion:** GTSinger (9 languages, techniques); DAMP (contemporary pop covers); MoisesDB (12 genres); M4Singer (SATB); VocalSet (techniques); Vocadito (7 languages); TONAS (flamenco); jaCappella (choral); CSD (children's); MTG-Jamendo (genre-tag statistics).

**Top 10 GitHub repos (immediate usefulness order):** librosa; pyloudnorm; audiomentations; microsoft/DNS-Challenge (DNSMOS); google/visqol; NISQA; pyroomacoustics; silero-vad; crepe; DeepFilterNet.

**Top academic benchmarks:** speech enhancement — VoiceBank-DEMAND, DNS Challenge, URGENT, EARS; singing separation/enhancement — MUSDB18-HQ, SingVERSE; audio quality — VoiceMOS, NISQA corpus, ODAQ, SingMOS-Pro; dereverberation — REVERB, EARS-Reverb, ACE; source separation — MUSDB18/SDX; melody extraction — MedleyDB, MDB-stem-synth, MIREX; automatic mixing — Mix Evaluation Dataset (no larger accepted benchmark exists); restoration — URGENT, declipping literature protocols.

**Metrics:** implement **now** — LUFS-I/LRA/true peak, crest factor, band-energy ratios, spectral flatness (noise floor), SI-SDR, ViSQOL, DNSMOS, NISQA. **Beta** — SQUIM, SRMR, MUSHRA infrastructure. **Research only** — FAD, CLAP, SingMOS, Audiobox-Aesthetics, PESQ/STOI (speech-side checks). **Not recommended** — POLQA, PEAQ.

**Listening tests:** internal — blinded, loudness-matched pairwise A/B with catch trials (webMUSHRA or Go Listen); artists — preference + "would you release this?" framing; engineers — MUSHRA + artifact annotation; crowd — pairwise with screening/anchors (Prolific-class panel, gold-standard trials); product claims — pre-registered MUSHRA with hidden reference/anchors, ≥15 post-screened listeners, loudness-matched, statistics reported (means, CIs, per-defect breakdown).

## 35. References

Singing datasets: VocalSet — Wilkins et al., ISMIR 2018, https://zenodo.org/records/1193957 · Annotated-VocalSet — https://zenodo.org/records/7061507 · DAMP — https://ccrma.stanford.edu/damp/ (license: /ResearchLicense.txt) · Intonation — Wager et al., ICASSP 2019, https://ieeexplore.ieee.org/document/8683554/ · NUS-48E — Duan et al., APSIPA 2013 · NHSS — https://hltnus.github.io/NHSSDatabase/ (Speech Communication 2021, arXiv:2012.00337) · CSD — https://mac.kaist.ac.kr/resources.html, github.com/emotiontts/emotiontts_open_db · OpenCpop — opencpop.github.io · OpenSinger — Huang et al., ACM MM 2021 · M4Singer — Zhang et al., NeurIPS 2022 · GTSinger — arXiv:2409.13832, https://huggingface.co/datasets/AaronZ345/GTSinger · MIR-1K — Hsu & Jang, NTU · vocadito — https://zenodo.org/records/5557945 (ISMIR-LBD 2021) · PopBuTFy/NSVB — Liu et al., ACL 2022, github.com/MoonInTheRiver/NeuralSVB · MedleyVox — github.com/jeonchangbin49/MedleyVox · jaCappella — LINE Corp 2023.

Multitrack/separation: MUSDB18 — https://sigsep.github.io/datasets/musdb.html, Zenodo 1117372/3338373 · MedleyDB — https://medleydb.weebly.com/, Bittner et al. ISMIR 2014 · MoisesDB — Pereira et al., ISMIR 2023, github.com/moises-ai/moises-db · DSD100/SiSEC — sisec.inria.fr · Slakh2100 — Manilow et al. 2019 · Cambridge-MT — https://cambridge-mt.com/ms/mtk/ (FAQ: /ms3/mtk-faq/) · Open Multitrack Testbed — multitrack.eecs.qmul.ac.uk · DnR — Petermann et al.

Speech enhancement: VoiceBank-DEMAND — https://datashare.ed.ac.uk/handle/10283/2791 (Valentini-Botinhao 2017) · DNS Challenge — github.com/microsoft/DNS-Challenge (ICASSP 2021–2023 papers) · EARS — Richter et al., Interspeech 2024 · VCTK — Edinburgh DataShare · WHAM!/WHAMR! — wham.whisper.ai · LibriMix — github.com/JorisCos/LibriMix · URGENT — https://urgent-challenge.github.io/urgent2025/ · CHiME — chimechallenge.org · REVERB — reverb2014.dereverberation.com.

Singing enhancement/quality: SingVERSE — arXiv:2509.20969, https://huggingface.co/datasets/amphion/SingVERSE · ReverbFX — arXiv:2505.20533 · AnyEnhance — 2025 · SingMOS — arXiv:2406.10911; SingMOS-Pro — arXiv:2510.01812, HF TangRain/SingMOS-Pro · VoiceMOS 2024 — arXiv:2409.07001 · NISQA — Mittag et al., github.com/gabrielmittag/NISQA · DNSMOS — Reddy et al., ICASSP 2021/2022 · ViSQOL v3 — arXiv:2004.09584, github.com/google/visqol · ODAQ — Torcoli et al., ICASSP 2024 · Audiobox-Aesthetics — Meta 2025.

Mixing intelligence: SAFE — Stables et al., ISMIR 2014, http://www.semanticaudio.co.uk/datasets/data/ · Mix Evaluation Dataset — De Man & Reiss, DAFx 2017, http://www.brechtdeman.com/publications/ · Automatic mixing w/ out-of-domain data — Martínez-Ramírez et al. 2022 · Mixing Style Transfer — Koo et al., ICASSP 2023, github.com/jhtonyKoo/music_mixing_style_transfer · DeepAFx(-ST) — Martínez-Ramírez/Steinmetz et al. · SignalTrain — Hawley et al. 2019 · automix-toolkit — github.com/csteinmetz1/automix-toolkit.

Rooms/noise: OpenAIR — https://www.openair.hosted.york.ac.uk/ · AIR — RWTH Aachen · BUT ReverbDB — Brno UT · MIT IR Survey — McDermott Lab · ACE — IEEE ACE Challenge 2015 · OpenSLR 26/28 — openslr.org/28 · DEMAND — Thiemann et al. 2013 (Zenodo) · MUSAN — Snyder et al. 2015, openslr.org/17 · FSD50K — Fonseca et al. 2022 · VOiCES — Richey et al. 2018, iqtlabs/voices.

Degradation/methodology: Audio Degradation Toolbox — Mauch & Ewert, ISMIR 2013 · Declipping survey — Záviška et al., IEEE SPM 2021 · audiomentations — github.com/iver56/audiomentations · pyroomacoustics — Scheibler et al. · webMUSHRA — Schoeffler et al., AES · Go Listen — Barry et al. 2021 · EBU R128 / ITU-R BS.1770 · MUSHRA — ITU-R BS.1534-3.

Clinical (excluded from product): Saarbruecken Voice Database — https://stimmdb.coli.uni-saarland.de/ (Zenodo mirror 16874898) · TORGO, VOICED (PhysioNet), MEEI (KayPENTAX, commercial).

---

*Uncertainty labeling: items marked **[verify]** or **[verify at download]** have version-dependent or unconfirmed license/availability details and must be checked on the official page before acquisition. iKala is confirmed unavailable. All other resources were verified to exist via official pages or peer-reviewed papers as of July 2026 (web-checked) or January 2026 (model knowledge).*
