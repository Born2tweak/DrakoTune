# Quality Target and Intent Specification

**Status:** canonical v1.0

## Principle

“Better” is not a scalar. DrakoTune evaluates a declared task against multiple axes and may return beneficial, equivalent, harmful, indeterminate, inapplicable, or errored. No weighted average may hide a hard safety or collateral-harm failure.

## Intent classes

| Intent | Product meaning | Required context | Examples | Claim boundary |
|---|---|---|---|---|
| Preserve | Avoid audible change to a clean/satisfactory vocal | Original; optional mix context | Bypass-equivalent cleanup | Equivalence/do-no-harm evidence |
| Repair | Reduce an identified recording defect | Defect applicability; ideally known/clean reference for synthetic tests | Hum/noise/click/clipping mitigation | Defect-specific evidence only |
| Control | Bring dynamics/tone into a declared bounded range | Vocal role and user goal | Peak control, gentle tonal balance | Range attainment plus harm review |
| Fit | Place vocal relative to accompaniment | Music context | Masking/level/spatial fit | Out of initial scope |
| Style | Match a declared creative reference/intent | Legitimate reference and separate mode | Effect-chain/style transfer | Preference/similarity, never called repair |

## Outcome axes

1. **Signal integrity and safety:** decode validity, finite samples, clipping/true peak, DC, duration/alignment, channel/sample-rate integrity.
2. **Target efficacy:** defect severity or declared control target changes in the desired direction by a meaningful amount.
3. **Collateral harm:** new/increased sibilance, mud, harshness, pumping, modulation, noise breathing, transient loss, spectral holes, spatial change, latency/misalignment.
4. **Intent preservation:** identity, phrasing, dynamics/style not targeted for change, and user-declared protected attributes.
5. **Perceptual outcome:** task-appropriate expert/user judgment, including ties/no-difference and artifacts.
6. **Confidence/applicability:** whether inputs, references, calibration, strata, and model domain permit interpretation.
7. **Operational outcome:** runtime, memory, failure/recovery, determinism.

## Verdict rules

- Hard safety failure → `unsafe`, regardless of other scores.
- Inapplicable primary endpoint → `not_applicable`, not fail or zero.
- Missing/error primary evidence → `indeterminate` or `error`, never pass.
- Target benefit with collateral budget exceeded → `harmful_tradeoff`, not pass.
- Clean preserve task → require prespecified equivalence/no-difference and artifact limits; processed non-preference is insufficient.
- Repair task → require applicable target benefit, no hard harm, and confirmatory perceptual evidence at claim level.
- Subgroup failure → scope claim to passing strata or block, per preregistration.
- Internal/synthetic evidence → engineering eligibility only.

## Metric applicability record

Every metric registers task, signal/reference needs, domain/training/calibration, direction, meaningful threshold, uncertainty method, failure modes, transformations/alignment, license, and prohibited interpretations. Full-reference metrics are used only where the reference is valid. Loudness/true peak are safety/comparability measures, not artistic-quality verdicts.

## Audition requirements

Comparisons are loudness matched with recorded method, delay aligned, assignment balanced/randomized where blinded, and bypassable. Loudness matching itself is reported and must not erase treatment-relevant loudness when loudness is the estimand.

## User intent

Intent is immutable per plan revision and includes targeted attributes, protected attributes, context availability, desired strength, references, and user overrides. Controls expose bounded concepts (“reduce steady noise,” “gentle peak control”) and technical details; they do not promise improvement.

## Claim elevation

Engineering observation → bounded dataset result → independent perceptual result → replicated product claim. Each elevation requires rights, identities, preregistration, valid statistics, subgroup reporting, claim approval, and expiry. A later contradictory result reopens the claim.

Threshold authority and every intentionally unknown margin/budget are tracked in [`THRESHOLD_REGISTRY.md`](THRESHOLD_REGISTRY.md). A missing threshold produces abstention or a threshold-setting milestone, never an improvised pass rule.
