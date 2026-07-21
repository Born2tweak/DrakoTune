# C — Audio Quality and Listening Standards Report

**As of:** 2026-07-21  
**Sources:** S-E01–S-E07.

## Applicable findings

- ITU-R BS.1770 and EBU R 128 provide loudness/true-peak measurement conventions. They help level matching and safety; they do not judge artistic quality.
- ITU-R BS.1116 targets controlled expert evaluation of small impairments. It is relevant to subtle artifact/do-no-harm validation when its environmental and training requirements are met.
- ITU-R BS.1534 defines MUSHRA for intermediate-quality systems, including a known reference, hidden reference, and anchors. A generic browser A/B or multi-stimulus test must not be labeled MUSHRA.
- PEAQ and ViSQOL are full-reference methods with domain assumptions. They may be applicable to controlled degradations where a clean reference is scientifically legitimate, not to arbitrary dry-versus-processed creative preference.
- webMUSHRA is a candidate experiment framework, not validation by itself; implementation, version, license, assignment, and telemetry must be audited.

## Method map

| Task | Objective evidence | Listening evidence |
|---|---|---|
| Clipping/non-finite/true peak | Direct safety measurement | Usually unnecessary unless limiter artifacts matter. |
| Synthetic known degradation recovery | Full-reference metrics plus defect-specific measures | Confirm artifact and generalization on held-out real examples. |
| Clean do-no-harm | Level/delay alignment, collateral metrics | BS.1116-style expert impairment or preregistered equivalence/no-difference design. |
| Creative style/reference matching | Parameter/feature diagnostics only | Properly referenced preference/similarity study. |
| Overall professional usefulness | None sufficient alone | Qualified, representative, independent panels in realistic context. |

## Prohibited shortcuts

Never average inapplicable metrics, use loudness change as improvement, call arbitrary trials MUSHRA, or infer professional quality from internal listening.

## Source-by-source evidence audit

| Source | Method requirements relevant here | Valid use | Invalid shortcut | Decision/recheck |
|---|---|---|---|---|
| S-E01, ITU-R BS.1116-3 (2015) | Controlled expert assessment for small impairments; reference, training, environment, repeatability, and reporting matter. | Subtle clean-preservation/artifact investigation when the controlled conditions can be met. | Calling a casual remote preference task a small-impairment validation. | Candidate basis for expert do-no-harm task; recheck on revision. |
| S-E02, ITU-R BS.1534-3 (2015) | Intermediate-quality multi-stimulus design with explicit reference, hidden reference, and anchors. | Tasks with a legitimate reference and anchor construction. | Branding any browser multi-stimulus or A/B page “MUSHRA.” | Use only through a registered protocol card. |
| S-E03, ITU-R BS.1770-5 (2023) | Defines loudness/true-peak measurement algorithm. | Safety, normalization audit, and comparison-level control. | Treating a loudness movement or target as artistic improvement. | Register as safety/comparability measure. |
| S-E04, EBU R 128 v5 | Operational program-loudness guidance, including the broadcast reference level and associated descriptors. | Documented playback/program workflow where that operational target applies. | Applying the broadcast program target blindly to an isolated dry vocal. | Task-specific target required. |
| S-E05, PEAQ/BS.1387-2 (2023) | Full-reference objective perceptual assessment with stated domain/implementation limits. | Controlled device/codec-like degradation research after alignment/applicability validation. | Overall creative wet-vs-dry mix score. | Observation-only unless DT-47 card proves applicability. |
| S-E06, ViSQOL | Full-reference similarity implementation with speech/audio modes and a clean reference assumption. | Known clean/degraded repair fixtures with validated alignment/domain. | No-reference quality, artistic preference, or professional usefulness. | Candidate metric card; validate singing vocals first. |
| S-E07, webMUSHRA | Software can implement AB/MUSHRA-style experiments and hidden references/anchors. | Audited UI framework if license/version/accessibility/security fit. | Treating software choice as protocol validity. | Review source license/maintenance before DT-61. |

## Conflict resolution

Standards answer different questions. BS.1116 sensitivity, MUSHRA ranking, BS.1770 loudness, and full-reference similarity must remain separate registered endpoints. A method’s authority does not make it applicable to DrakoTune’s creative task.

## Protocol requirement extraction

| Method | Required protocol facts to freeze | Passing interpretation | Explicit non-interpretation |
|---|---|---|---|
| BS.1116-style small-impairment task | Expert-listener qualification/training; controlled reproduction chain and room/headphone evidence; reference and coded conditions; randomized presentation and repetitions; grading scale; session duration; exclusion rule; analysis plan. | Evidence about detectability or severity of small impairments under the registered conditions. | General preference, mix readiness, or a remote convenience panel. |
| BS.1534/MUSHRA | Known reference; hidden reference; at least one defined anchor; simultaneous multi-stimulus presentation; randomized condition order; scale labels; listener training; screening and analysis declared before outcomes. | Comparative intermediate-quality evidence for the registered stimuli and population when reference and anchors are scientifically legitimate. | Any ordinary A/B test, an unanchored multi-stimulus screen, or a creative dry-versus-wet preference task without a normative reference. |
| BS.1770/R128 | Algorithm/revision and implementation version; channel mapping; gating; integrated measurement interval; true-peak settings; normalization gain; pre/post values. | Reproducible loudness and peak comparability or safety evidence. | Better timbre, clarity, emotion, balance, or professional quality. |
| PEAQ/BS.1387 | Pinned conforming implementation/profile; legitimate clean reference; sample-rate/channel constraints; delay and level handling; algorithm outputs; known domain limits. | Full-reference impairment evidence within the validated device/codec-like domain. | A no-reference score or overall creative-processing verdict. |
| ViSQOL | Pinned implementation and speech/audio mode; clean reference; sample-rate/channel preparation; alignment policy; per-item failures and outputs. | Exploratory full-reference similarity for known-transform fixtures after singing-vocal calibration. | Preference, target-genre validity, or proof that the processing intent was correct. |

No numeric threshold is inherited merely because a standard defines a measurement or test procedure. DrakoTune thresholds remain `unset` until the responsible milestone records the target task, population, error costs, pilot evidence, and decision authority in the threshold registry.

## Listening-study audit packet

Every listening result must preserve the protocol card, preregistration hash, stimulus and transform identities, loudness/alignment evidence, assignment manifest, listener qualification and consent status, playback/environment telemetry, raw response lineage, exclusions with predeclared reasons, analysis code/version, diagnostics, and a result-to-claim mapping. Missing hidden-reference or anchor behavior invalidates the MUSHRA label; it does not silently turn the study into valid generic evidence.
