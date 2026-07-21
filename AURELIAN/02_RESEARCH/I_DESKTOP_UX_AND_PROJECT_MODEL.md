# I — Desktop UX and Project Model Report

**As of:** 2026-07-21  
**Confidence:** architecture recommendation; user validation pending.

## Initial workflow

1. Create/open a local project.
2. Import one supported vocal file without modifying it.
3. Inspect preflight findings, scope, and privacy/processing notice.
4. Analyze with visible progress and cancellation.
5. Review proposed actions and confidence/limitations.
6. Render a new revision.
7. Audition original/revision with loudness matching and blindable A/B.
8. Adjust bounded intent controls or restore defaults.
9. Export audio and optional provenance report.

## Project model

The project stores relative asset references where possible, immutable source fingerprints, analysis identity, plan revision, render identities, user intent, audition state, and export history. Large audio should remain as managed files, not embedded opaque blobs. Every state transition is atomic and recoverable; cancellation yields no “completed” result.

## Guardrails

- Local-only by default; no account/cloud dependency.
- Original is read-only and always recoverable.
- Unsupported stereo/context claims are explicit.
- “Improve” is not a control; use intent labels with audible/technical explanations.
- Level-matched audition and bypass are prominent.
- Errors identify recovery actions and preserve logs without source audio by default.

The first UI is a vertical slice, not a DAW or plugin. Context playback and multitrack scope require later evidence.

## Evidence and assumption audit

| Basis | Supported conclusion | Unsupported inference | Design response | Recheck trigger |
|---|---|---|---|---|
| Existing CLI/web workflow | Import/analyze/plan/render/report is technically coherent. | That users understand diagnoses, trust the right things, or prefer a desktop workflow. | Reuse the flow but validate comprehension/recovery at DT-76. | Product discovery/usability findings. |
| Current mono preprocess | Single-vocal projects match executable scope. | That users never need beat/accompaniment context for judgment. | Declare isolated-vocal scope and keep context as Q-009/DT-92 decision. | Repeated user demand or context experiment. |
| Aurelian provenance requirements | Immutable source/revision/build identities support recovery and audit. | That users want to see every technical field. | Progressive disclosure: concise finding with inspectable technical/provenance detail. | Usability results. |
| E-009 loudness evidence | Level matching reduces a major comparison confound. | That level-matched preference alone proves repair or quality. | Record match method; preserve blind/bypass; keep study evidence separate. | Audition validation. |
| Local-first product hypothesis | Avoiding upload addresses confidentiality and transfer concerns. | “Local” means perfectly private or secure. | Offline default, redacted logs, explicit export/share, signed updates, threat model. | Desktop security audit. |
| Project recovery requirements | Atomic state and original preservation reduce catastrophic failure. | A specific database/document format is already selected. | Specify behavior first; benchmark storage choices at DT-69. | Application-service ADR. |

## Usability falsifiers

The slice fails if target users cannot distinguish findings from proof, cannot identify the untouched original, cannot bypass/recover from an intentionally poor plan, believe audio was uploaded when it was not, cannot finish with keyboard/assistive technology, or consistently require accompaniment context for the primary job.
