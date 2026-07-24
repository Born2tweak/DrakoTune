# Consolidated Human-Decision Packet — H1 Study Line (DT-57 / DT-55 / DT-58)

**Date:** 2026-07-24 · **Executor:** claude-code (autonomous) · **Basis:** origin/main
after DT-57/55/58 autonomous groundwork. Supersedes nothing in the earlier D-A/B/C
packet (`CONSOLIDATED_HUMAN_DECISION.md`); this is the next frontier.

Every autonomous, no-spend, no-contact, non-legal, non-claim portion of DT-57, DT-55,
and DT-58 is **complete and merged** (tests green). What remains below is **only**
choices a human owner (and, where noted, counsel) must make. Nothing here has been
decided or actioned on your behalf.

## Why execution pauses here

The remaining frontier requires setting statistical thresholds, spending money,
contacting participants, or approving legal/consent terms — all hard human gates. No
further milestone advances without at least one of these.

---

## Decision H1-A — Statistical thresholds & method sign-off  *(DT-57 → unblocks the confirmatory design line)*

The analysis method, immutable preregistration schema, power simulator, and
adversarial suite are built and validated (`src/analysis/`, `STATISTICAL_ANALYSIS_PLAN.md`).
The plan **cannot be frozen** until you set 4 values (`freeze()` refuses while PENDING):

- **δ_sup** — superiority margin for repair efficacy (processed-preference over 0.5).
- **δ_ni** — non-inferiority margin for do-no-harm on clean input.
- **α** per primary endpoint (family-wise controlled via Holm).
- **target power** and the **catch-trial exclusion rate**.
- **Independent statistical method review** (a person other than the implementer).

Not decided here (Field 22). Final sample size `n` is **not** set now — it follows
pilot variance at DT-60. On your values: I encode them, `freeze()` produces the
analysis lock, and DT-57 completes.

## Decision H1-B — Corpus acquisition budget & consent terms  *(DT-55 → unblocks DT-62 acquisition)*

The rights-clean inventory, an **88-clip launch-strata coverage gap**, purpose matrix,
validators, and parameterized cost scenarios are built (`src/acquisition/`,
`ACQUISITION_PLAN.md`). Public CC-BY singing data covers only `english`; every rap/pop
and home-recording stratum needs acquisition. Human-only:

- **Budget ceiling + source mix** (e.g. commissioned dry/wet vs marketplace vs
  professional treatments; illustrative scenarios ~$2.8k–$3.5k, **not quotes**).
- **Counsel-drafted consent / retention / withdrawal terms + license grants** per purpose.
- **Outreach / commissioning authorization**; **owner-audio public-example** approval.

No spending, outreach, or contract performed (Field 22). On approval: I wire the
approved consent-term references + source mix into the plan and DT-55 completes.

## Decision H1-C — Expert-pilot budget, consent & go/no-go  *(DT-58 → unblocks DT-59 pilot)*

Screener/qualification, randomization/blinding/session/withdrawal procedures, the
fair-rate formula, and an end-to-end mock dry-run are built (`src/pilot/`,
`PILOT_RECRUITMENT_PLAN.md`). Human-only:

- **Base compensation rate + total ceiling + contingency** (formula ready; rate is yours).
- **Recruitment channel + outreach authorization**.
- **Consent/contract language + payment handling** (counsel).
- **Final go/no-go** (D-016/D-017). Pilot is non-confirmatory; a 2–3 person pilot is
  exploratory (feeds variance to DT-60), never a claim.

No contact, enrollment, or spend performed (Field 22).

---

## Decision H1-D — Private paired-corpus rights ruling — **RESOLVED 2026-07-24 (D-029)**

> Owner override: approved for **local, internal, evaluation-only** processing
> (counsel not consulted; owner accepts the risk). Leaked + AI-isolated files stay
> rejected permanently; no redistribution/training/claims; artifacts gitignored;
> deletion path documented. Original packet text retained below for the record.

*(original packet text, added 2026-07-24; gates DT-55A…H real-corpus execution)*

The owner supplied a local folder of ~31 commercial acapella MP3s (Juice WRLD,
Lil Uzi Vert, Lil Tecca, Kid LAROI, Travis Scott; YouTube-sourced, one **leaked**,
one AI-isolated) forming ~10 raw/wet candidate pairs — exactly the paired
calibration data the quality gap needs. Under D-026 and the fail-closed ingestion
rule, **DrakoTune may not process this audio** until you (with counsel where you
deem it needed) rule on its use.

- **Autonomously done regardless:** local gitignored manifest + rights
  classification (leaked → rejected permanently; AI-isolated wet → rejected;
  duplicate flagged); the entire pairing/alignment/delta/oracle machinery built +
  validated on rights-clean surrogates (`PAIRED_CORPUS_ORCHESTRATION_PLAN.md`).
- **Your choices:** (1) approve/deny **local, internal, evaluation-only**
  processing of the non-rejected files (no redistribution, no public example, no
  training, no claim; documented deletion path), or (2) decline and route the
  same need through the rights-clean **commissioned dry/wet** scenario already
  costed in H1-B. Option 2 is the clean path; option 1 is a legal-risk judgment
  that is yours, not mine.
- Regardless of the ruling: leaked file stays rejected; nothing from this corpus
  ever leaves the machine or enters git/claims/training.

## Dependency audit result (DT-57 must precede confirmatory collection)

Verified: the graph already enforces freeze-before-confirmatory
(DT-57 → DT-59 pilot → DT-60 threshold LOCK → DT-66/67 confirmatory). An explicit
guard was added (`DEPENDENCY_GRAPH_AND_CRITICAL_PATH.md`): pilot data informs only the
confirmatory `n`; endpoints/direction are frozen in the DT-57 lock; thresholds are set
at DT-60 before any confirmatory data. No reorder was required.

## What I will NOT do without your explicit approval

Set/adjust any statistical threshold or α; spend money; contact/recruit participants;
accept consent/contract/license terms; commission audio; publish owner audio; make any
perceptual-quality claim; choose the confirmatory sample size.

## If you answer nothing

The repository stays safe, consistent, and fully tested. DT-54 and DT-56 are complete;
DT-57/55/58 autonomous halves are done and merged; the frontier is exactly the three
decisions above. Re-running re-derives this same packet.
