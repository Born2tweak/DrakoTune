# F — Automatic Mixing Research Report

**As of:** 2026-07-21  
**Sources:** S-M01–S-M06.

## Finding

Recent differentiable mixing research makes interpretable effect-parameter estimation increasingly plausible, but none of the reviewed work is ready for unqualified DrakoTune adoption.

- Diff-MST addresses multitrack style transfer through a differentiable console; it assumes context/reference structures beyond an isolated vocal.
- DiffVox demonstrates vocal effect-chain estimation (EQ, dynamics, delay/reverb). Its presets/data include MedleyDB and private material, so code availability does not establish deployable weights/data rights or target-genre validity.
- The 2025 inference-time Gaussian-prior work is a useful optimization challenger, but its limited listener evidence and dataset context do not establish broad professional performance.
- DeepAFx is research-licensed; DeepAFx-ST is reference/style-transfer work; dasp-pytorch is a useful Apache-2.0 differentiable-DSP component rather than a complete product method.

## Decision

Do not adopt a learned production path. Preserve deterministic DSP as champion. After rights-clean identity-aware data and valid evaluation exist, reproduce one bounded candidate offline against the champion. Require artifact, latency, memory, interpretability, rollback, and subgroup gates. Style transfer must remain a separate product mode from cleanup.

## Watch signals

Prioritize reproducible vocal-specific studies with public code, explicit weights/data rights, independent listening, target-genre coverage, and on-device resource reporting. Paper metric superiority alone is not a trigger.

## Candidate evidence cards

| Candidate | Task/method | Reported evidence available | Applicability or rights conflict | Disposition/falsifier |
|---|---|---|---|---|
| S-M01 Diff-MST, ISMIR 2024 | Differentiable multitrack mixing-console style transfer using reference/context. | Primary paper and official implementation context describe interpretable console parameters. | Requires multitrack/reference assumptions unlike isolated-vocal cleanup; paper success is not commercial-rights or genre proof. | Defer. Reconsider if a rights-clean isolated-vocal/context experiment can beat the deterministic champion without harm. |
| S-M02 DiffVox, DAFx 2025 | Vocal effect-chain parameter estimation across EQ, dynamics, delay, and reverb. | Paper/code provide a direct vocal-processing research candidate. | Preset/data provenance includes MedleyDB and private material; code license does not grant training/weights/data reuse; style matching differs from repair. | Highest-priority bounded reproduction only after component-rights audit. |
| S-M03 inference-time Gaussian prior, WASPAA 2025 | Prior-guided parameter estimation at inference time. | Paper includes a limited listener study and a modern optimization alternative. | Small evaluation and MedleyDB context do not establish target-genre or on-device readiness. | Offline experiment candidate; require preregistered champion comparison. |
| S-M04 DeepAFx | Learned automatic audio-effects processing. | Primary research/code enables reproducibility study. | Adobe Research License is not assumed production-compatible; task/data differ. | Research reference only unless license and task gates change. |
| S-M05 dasp-pytorch | Differentiable implementations of audio processors. | Apache-2.0 code can support controlled parameter-optimization experiments. | A processing library is not a trained product method and offers no quality evidence by itself. | Potential sandbox building block after dependency/security review. |
| S-M06 DeepAFx-ST | Differentiable style-transfer formulation. | Primary paper supports separation of style matching from repair. | Reference/style task cannot validate clean preservation or defect repair. | Keep in a future style-mode research branch. |

## Comparative conclusion

DiffVox is the most directly relevant candidate, but “most relevant” is not “ready.” The first experiment must reproduce an official result, establish component rights, run on isolated singing vocals, compare against the frozen deterministic champion, and report collateral artifacts, abstention, resource cost, and subgroup behavior.

## Exact method and result extraction

These values are reproduction inputs, not DrakoTune acceptance thresholds. A reproducer must pin the cited paper revision and implementation commit and record any divergence.

| Source | Exact extraction from the primary source | Reproduction consequence |
|---|---|---|
| S-M02 DiffVox, arXiv v2 | Single-track mono-in/stereo-out matching with fixed processor routing. The differentiable chain has 152 parameters: 14 parametric-EQ, 9 compressor/expander, 8 delay, 119 feedback-delay-network reverb, 1 pan, and 1 send parameter. | Reproduce the published chain before changing processors or topology; a smaller DrakoTune chain is a new experiment. |
| S-M02 data | The evaluation reports 70 retained MedleyDB tracks and 365 retained private tracks after excluding 6 of 76 MedleyDB and 5 of 370 private tracks. Dry/wet correspondence for the private material was recovered with cross-correlation and time alignment. | Preserve exclusion accounting and provenance. Private-data results cannot establish reproducibility or usable rights for DrakoTune. |
| S-M02 optimization | Audio is divided into 12-second segments with 5-second overlap; loss is evaluated on the final 7 seconds; batches contain up to 35 segments. Each track is optimized for 2,000 Adam steps at learning rate 0.01, reported as roughly 20–40 minutes per track on an RTX 3090. | Record segmentation, optimizer, hardware, elapsed time, and peak memory. This cost is an offline baseline, not an interactive-product result. |
| S-M02 matching results | On the private set, the paper reports DiffVox mean spectral score 0.76 left/0.94 mid and mean loudness-difference-ratio score 0.34 left/0.41 mid, versus unprocessed baselines 1.44/2.39 and 1.82/2.08 respectively. On MedleyDB it reports 0.75/0.98 and 0.39/0.45, versus 1.27/2.16 and 1.00/1.35. Lower is treated as better in that paper. | Recompute the named metrics from exported audio and confirm directionality. Do not translate these task-specific scores into professional quality or repair claims. |
| S-M02 limitation | The authors exclude poorly fitted nonlinear or modulation-effect cases. The paper also reports near-zero normality-test p-values for the first 75 principal components of fitted parameters. | Report exclusions as failures, not invisible preprocessing. Do not assume a Gaussian parameter distribution from this corpus. |
| S-M03 Gaussian-prior method, arXiv v2 | The experiment uses 11-second non-overlapping MedleyDB segments, equal A/B partitions, and 1,000 Adam steps at learning rate 0.01. The paper reports 70 tracks, with 5 dropped for insufficient segments. | Freeze the partition rule and exclusion ledger before reproduction. Resolve the relationship between the stated 70-track set and 5 exclusions explicitly in the run record. |
| S-M03 learned baseline | Its regression baseline is trained on 365 private tracks with 17 validation tracks, described as about 4,177 ten-second segments; the paper reports overfitting after approximately 6,500 steps. | The learned baseline is not independently reproducible from public data and cannot be a production candidate without separate weights/data rights. |
| S-M03 result/evaluation | The paper reports up to a 33% reduction in parameter MSE and a subjective evaluation with 16 participants. | Treat the effect as paper-specific. Sixteen participants do not establish professional, target-population, subgroup, or product superiority. |
| S-M01 Diff-MST | The primary abstract specifies a differentiable mixing console, transformer controller, style loss, raw multitracks plus a reference song, arbitrary track counts without source labels, and interpretable/post-hoc control. | Those task assumptions are sufficient to classify it as a style-transfer challenger. Exact corpus, optimization, and listener counts remain `unverified` here and must be extracted from the pinned paper/code before any experiment. |

## Reproduction admission card

A DiffVox-family experiment is admissible only when it records: pinned paper/code versions; every processor and parameter range; public/private/derived component rights; inclusion and exclusion counts; source-, singer-, song-, and session-safe splits; alignment method; optimizer and stopping rule; hardware and runtime; all published metrics with directionality; exported-audio safety and collateral-harm results; and a frozen comparison against the deterministic champion. Failure to reproduce a paper score is retained as a negative result. Reproducing it does not authorize adoption.
