# Product Specification

**Status:** canonical v1.0 planning specification  
**Baseline:** post-M44  
**Evidence posture:** claims quarantined beyond tested prototype behavior

## Product definition

DrakoTune is a local-first, inspectable assistant that analyzes an isolated lead-vocal recording, proposes a conservative signal-processing plan, renders a non-destructive revision, explains limitations, supports level-matched audition, and exports audio with optional provenance.

The initial product is not a DAW, mastering service, vocal generator, autonomous professional engineer, multitrack mixer, or guaranteed style-transfer system.

## Product promise (D-A, decided 2026-07-23; see DECISION_LOG D-025)

Two statements are recorded separately: a *target promise* (direction) and the
*currently-supportable claim* (what evidence backs today). A target promise is
**not** a validated claim.

- **Target product promise (aspirational, gated on perceptual evidence):**
  *"Automatically produce a technically safe, polished lead-vocal processing
  candidate from a supported dry rap/pop vocal, with no required engineering
  knowledge, optional user adjustment, and explicit abstention when reliable
  processing cannot be supported."*
  The word **"polished" is perceptual and remains UNVALIDATED** — quarantined in
  the claim registry until a rights-clean, preregistered blinded listening study
  supports it (DEF-003; DT-55/62/56/57/66/67). "Processing candidate," not "mix":
  single lead vocal, not accompaniment/multitrack mixing.

- **Currently-supportable claim (evidence-backed today):**
  *"DrakoTune produces a reproducible, non-destructive lead-vocal processing
  candidate subject to defined technical safety checks and abstention rules."*

Abstention is a first-class outcome: when reliable processing cannot be supported,
the system declines rather than emitting a low-confidence result.

## Target users and job

Primary hypothesis: independent rap/pop vocal creators and technically engaged engineers who possess an isolated lead-vocal file and want a quick, understandable cleanup starting point without uploading unreleased material. This hypothesis requires independent discovery/usability evidence before launch positioning.

Core job: “Help me identify and conservatively reduce common recording/tonal/dynamic issues, let me hear and control the tradeoff, and never endanger my original.”

## Supported initial scope

- One local isolated lead-vocal asset per project.
- Explicitly documented supported formats/durations/platform.
- Non-destructive import, analysis, plan, render revision, audition, export.
- Defect/tone/dynamics observations with applicability and confidence.
- Conservative cleanup intent controls and reset/bypass.
- Exact source/build/config/provenance record.
- Offline-first operation with no account requirement.

## Out of scope until separately specified and evidenced

- Accompaniment-aware mix placement, stereo/multitrack editing, mastering.
- Creative/reference style transfer represented as cleanup.
- Real-time DAW plugin or live monitoring.
- Training on user audio, cloud sync, social/publishing workflows.
- Public desktop binaries before distribution approval.
- “Professional,” “studio quality,” or generalized improvement claims.

## Functional requirements

| ID | Requirement | Acceptance class |
|---|---|---|
| P-01 | Import preserves original bytes/read-only fingerprint and never overwrites source. | Automated + recovery test |
| P-02 | Unsupported/corrupt inputs fail safely with actionable error and no completed artifact. | Adversarial tests |
| P-03 | Analysis records task applicability, findings, uncertainty, and limitations. | Contract tests |
| P-04 | Plan shows ordered actions, parameters, rationale, safety bounds, and reversibility. | Contract + usability |
| P-05 | Render is deterministic for identical input/build/config within defined tolerance. | Cross-build goldens |
| P-06 | Progress, cancellation, and crash recovery leave atomic project state. | End-to-end tests |
| P-07 | Audition supports bypass and loudness-matched original/revision comparison. | Audio + usability tests |
| P-08 | Adjustments are bounded intent controls; every change creates a revision. | Property + UX tests |
| P-09 | Export is a new file and records format, hash, render identity, and warnings. | End-to-end test |
| P-10 | Privacy defaults local/off; telemetry/upload require explicit consent. | Security/UX tests |
| P-11 | Evidence and public language follow the claim registry. | Release gate |
| P-12 | Rights/consent restrictions block prohibited use and support withdrawal. | Provenance simulation |

## Quality attributes

- Safety: finite output, bounded peaks, original preservation, validated parsing.
- Honesty: unknown/inapplicable/error are visible; no fabricated confidence.
- Inspectability: decisions and provenance can be audited.
- Reproducibility: locked build and stable identities.
- Performance: named maximum duration on named minimum hardware.
- Accessibility: keyboard operation, readable state, non-color-only outcomes, transcript/explanation equivalents.
- Recoverability: atomic writes, durable project state, rollback/revision history.

## Success hierarchy

1. No source loss, prohibited data use, or misleading claim.
2. Users understand scope and can recover/bypass.
3. Safety and defect-specific engineering gates pass.
4. Independent target-population evidence shows bounded benefit without subgroup harm.
5. Performance and distribution are supportable.

Engagement, render count, or metric movement cannot override levels 1–4.

## Release stages

- Internal engineering: synthetic/consented fixtures; no public claims.
- Closed research pilot: approved consent/rights and protocol; no generalized claim.
- Limited desktop evaluation: approved distribution branch and target-hardware proof.
- Public release: replicated claim evidence, security/privacy/license review, support/update/rollback readiness.

## Open product decisions

Resolved 2026-07-23: the **cleanup-versus-style promise** (D-A → auto-clean with
optional adjustment + abstention; style transfer stays out of scope) and the
**distribution branch** (Q-001 → hosted_only near-term; D-027). First platform,
exact duration/hardware, and accompaniment context remain human-owned questions
Q-002, Q-008–Q-010.
