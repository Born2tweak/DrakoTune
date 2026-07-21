# A — Product and User Evidence Report

**As of:** 2026-07-21  
**Confidence:** low-to-moderate; repository evidence is strong, independent user evidence is not.

## Finding

The smallest defensible product is a local-first assistant for processing one isolated lead-vocal file, preserving the original, explaining a conservative cleanup plan, offering level-matched audition, and exporting a processed copy plus provenance. The current code supports much of the computational spine, but not a validated user promise.

“Professional vocal mixing” conflates at least four jobs: removing recording defects, controlling dynamics/tone, fitting a vocal into musical context, and creative styling. An isolated mono file can support the first two only within measured limits. It cannot prove in-mix placement or style intent without accompaniment/reference/context.

## Current evidence

- CLI and web flows demonstrate import → analyze → plan → render → evaluate → export.
- Reports expose deterministic actions and caveats.
- No independent interview/usability corpus establishes target users, acceptable controls, or trust language.
- No genre-stratified real-recording evidence establishes rap/pop robustness.

## Decision impact

Launch promise should remain “inspectable vocal cleanup assistant” until independent evidence supports more. Conservative cleanup and creative/reference matching must be separate modes with separate evaluation. The desktop slice should make limitations and the untouched original visible.

## Required disconfirmation

Test whether target users can correctly predict what the tool will change, recover from a poor result, and prefer the assisted outcome in representative context. Failure to beat a simple baseline or repeated demand for accompaniment context narrows the product further.

## Evidence audit

| Evidence | Method/version | Atomic finding | Limitation or conflict | Decision effect | Recheck trigger |
|---|---|---|---|---|---|
| S-R03 CLI/web execution flow | Code trace and representative run at `a3c5163` | DrakoTune already supports a coherent import → analyze → plan → render → report workflow. | Executability does not establish usefulness, comprehension, or demand. | Preserve the computational spine. | Application-service or product-flow change. |
| S-R04 reports/manifests | Schema and artifact inspection | The system can expose actions and provenance rather than operate as a black box. | Current verdict semantics can still overstate benefit. | Inspectability remains a core product principle, gated by DT-45/48. | Evidence-schema migration. |
| Repository product documents | Historical claim/workflow review | The intended audience is a non-engineer seeking vocal cleanup. | No independent discovery corpus verifies the audience, job frequency, or willingness to use a local desktop tool. | Treat target user and promise as hypotheses in DT-53. | Completed discovery study. |
| Mono preprocessing behavior | Source trace | The current engine has enough information for isolated-vocal repair/control tasks. | It lacks accompaniment context needed for mix placement, masking, and many artistic judgments. | Keep “fit” and general mixing out of v1. | Context-aware prototype/evidence. |
| Independent user evidence | Repository search | No consented independent interview/usability dataset is available. | Informal owner experience may guide hypotheses but is not independent evidence. | Product rating remains moderate confidence; do not invent market conclusions. | New authorized interviews/usability pilot. |

## Contradiction register

The aspirational goal of “professional” or “expensive” vocals conflicts with the observable information available to an isolated mono processor. The roadmap resolves this by making conservative cleanup the initial testable promise and keeping creative style and accompaniment fit as separate future decisions rather than quietly weakening their evidence standards.
