# Consolidated Human Decision Packet (post safe-preparation)

**Date:** 2026-07-22 · **Verified commit basis:** DT-49/DT-53/DT-51 autonomous
prep merged to `main` (PRs #8–#11) · **Executor:** claude-code (autonomous)

This supersedes the prior `AURELIAN/00_CONTROL/HUMAN_DECISION_PACKET.md`, which
paused *before* doing the autonomous preparation it had identified. That
preparation is now **complete**. Every safely-executable milestone on the
frontier has been done; the remaining frontier is genuinely human-only.

## What was completed autonomously this run (all merged, each CI-green)

| Item | Result | Evidence |
|---|---|---|
| Control plane install + reconciliation (AR-00/01/02) | Real-fact canonical state; corrected the false stopping point | `control/RECONCILIATION_RECORD.md` (PR #8) |
| **DT-49** rights/consent/withdrawal engine (autonomous half) | fail-closed `authorize`; withdrawal graph + deletion **simulation**; claim suspension; 20 adversarial tests | `AURELIAN/07_DATA_AND_PROVENANCE/dt49_evidence/` (PR #9) |
| **DT-53** product-discovery framework (autonomous half) | pseudonymized record schema; falsifiable promises; contradiction audit; 16 tests | `dt53_evidence/` (PR #10) |
| **DT-51** distribution obligation inventory (autonomous half) | component-level copyleft inventory + 3-branch comparison + non-binding recommendation; 22 tests | `dt51_evidence/` + `AURELIAN/04_AUDITS/DT51_DISTRIBUTION_OBLIGATION_INVENTORY.md` (PR #11) |

Baseline held throughout: **536 tests pass** (from 478); audio goldens unchanged;
no DSP/audio behavior changed; no public claim un-quarantined.

## Why execution now pauses (and only now)

Every remaining ready/next milestone is blocked by a decision only a human owner
(and, where noted, qualified counsel) can make. These are hard gates in the
autonomy policy: **product scope, rights/consent/legal, spending, participant
contact, and distribution posture.** There is no reversible internal milestone
left to advance without one of these.

---

## Decision D-A — Product promise & scope  *(unblocks DT-53 → DT-54 → the H1 product line)*

The autonomous framework is ready: `AURELIAN/02_RESEARCH/DT53_DISCOVERY_PROTOCOL.md`
lays out the protocol, job map, and three **falsifiable** promise alternatives:

- **PR-A** — Automatically clean a *single dry* rap/pop vocal.
- **PR-B** — *Assist* cleanup with guided controls (manual control retained).
- **PR-C** — Honest *second opinion* (diagnose, don't process).

- **Human-only:** (1) which promise (or none) and the launch boundary; (2) any
  participant contact/recruitment for discovery interviews.
- **Recommendation:** pick **PR-A or PR-B** as the near-term promise and authorize
  a small approved round of discovery interviews to test its falsifiers; PR-C is
  the safe fallback if discovery falsifies the processing promises.
- **Consequence of deciding:** unblocks DT-54 (strata taxonomy) and the product
  data/evaluation line. **Of not deciding:** roadmap holds the narrow current
  spec; H1 stays blocked.
- **Exact resume action on your answer:** I encode the chosen promise + scope into
  `AURELIAN/03_CANONICAL/PRODUCT_SPEC.md`, mark DT-53 complete, and begin DT-54
  (taxonomy is autonomous once scope is fixed).

## Decision D-B — Rights & consent posture  *(unblocks DT-49 completion → DT-55, DT-62, DT-69)*

The enforcement engine is built and tested on synthetic fixtures (`src/rights/`).
What remains is not code:

- **Human/counsel-only:** consent/contract language; retention/privacy
  obligations; real deletion authority; legal interpretation of rights.
- **Recommendation:** approve a **synthetic-only** posture for now (no real
  audio acquired), and separately have counsel draft the consent/retention terms
  before any real corpus work (DT-55/DT-62).
- **Consequence of deciding:** DT-49 can be marked complete and DT-55/DT-62/DT-69
  unblock. **Of not deciding:** DT-49 stays human-gated; no real-audio pipeline.
- **Exact resume action on your answer:** I wire the approved consent-term
  references into the consent-store interface (still no real PII), record the
  decision in the decision log, and mark DT-49's human gate satisfied.

## Decision D-C — Desktop distribution branch  *(DT-51; owner + counsel)*

Hard fact (DT-50/DT-51): **pedalboard is GPL-3.0 and the bundled FFmpeg is
GPL-3.0-or-later.** A single desktop binary inherits copyleft. Options, fully
inventoried in `AURELIAN/04_AUDITS/DT51_DISTRIBUTION_OBLIGATION_INVENTORY.md`:

1. **gpl_compatible_oss** — ship under GPL, provide source (viable now).
2. **permissive_custom_dsp** — replace pedalboard + GPL FFmpeg first (high cost).
3. **hosted_only** — no binary; copyleft source-offer not triggered (reversible).

- **Recommendation (non-binding):** stay **hosted_only** near-term (already the
  de-facto posture; reversible), and defer the binary branch (1 vs 2) to counsel
  after D-A fixes scope.
- **Consequence of deciding:** the chosen branch unblocks DT-71/DT-88/DT-89.
  **Of not deciding:** desktop binary milestones stay blocked; hosted product
  continues unaffected.
- **Exact resume action on your answer:** I write the distribution ADR recording
  the chosen branch + obligations, close Q-001, and update the roadmap branch.

---

## What I will NOT do without your explicit approval

Contact/recruit participants · spend money · accept consent/contract/license
terms · make the product-scope decision · choose the distribution branch ·
publish any claim · ship a binary · delete real data · promote any audible DSP
change.

## If you answer nothing

The repository is in a safe, consistent, fully-tested state (536 passing;
`main` CI-green). Nothing degrades. Re-running the program will re-derive this
same packet — there is no further autonomous milestone to advance.
