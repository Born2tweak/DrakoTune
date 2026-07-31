# Project State

**State date:** 2026-07-21  
**Audited commit:** `a3c51637a0c2ed18994a6950a45a72ccb753a93d`  
**Planning epoch:** H0 complete; 2026-07-23 reconciliation resolved the consolidated human decision (D-A/D-B/D-C) — frontier now DT-54 (H1)  
**Delivery posture (updated 2026-07-31):** DT-45–DT-58 autonomous portions complete; DT-77 measurement phase produced N-016..N-022. **V3 Engine track: DT-93–DT-98 and DT-100 complete** (graph routing, three audible modes, substantive processors, workstation, doubling, and the full pitch-correction pipeline — contour, scale target, correction curve, TD-PSOLA resynthesis, formant behaviour, three characters). DEF-003 is re-scoped (D-030) to gate *public quality claims only*. **The autonomous audio frontier is now exhausted (F-23):** the only unblocked autonomous milestone is DT-105, a visual system that does not reduce the measured audio gap. Every remaining milestone that would — DT-101 denoising/room reduction above all — is gated on an owner decision: DT-101 on rights/spend, DT-102/103/104 transitively on DT-99's public surface. Q-016 (what an automated search may optimise) remains unresolved and continues to bar objective-driven promotion claims; everything in DT-98/DT-100 proceeded because it is authored and bounded rather than searched. System scorecard: NOT RELEASABLE for public claims. See `AURELIAN/05_ROADMAP/MILESTONES/DT_93_106.md`
**Planning package:** Aurelian v1.2

## Verified baseline

- Fresh Python 3.12 environment installs successfully with `.[dev,web]`; `pip check` is clean.
- `python -m pytest -q`: 362 collected, 360 passed, 2 skipped, 5 warnings.
- `python scripts/audio_regression.py`: all six fixtures match their goldens.
- The v2 decision engine is the CLI default. `--legacy` selects the legacy chain; `--plan` is a deprecated no-op.
- A representative `harsh.wav` v2 run completed and produced audio, report, manifest, trace, and objective results.
- The public pilot code is a FastAPI upload/job/download service with retention, signed links, rate limiting, and concurrency controls.

## Product truth

DrakoTune is a deterministic, inspectable vocal-processing prototype. It is not yet validated as an automatic professional vocal mixer. It can analyze a mono vocal, construct a bounded DSP plan, render it, measure selected signal changes, and explain what it did. Its strongest assets are deterministic execution, traceability, tests, and a conservative safety layer. Its central weakness is that objective movement is too often treated as evidence of perceptual improvement.

## Evidence status

| Claim area | Current status | Consequence |
|---|---|---|
| Determinism and software regression | Supported locally | May describe as a tested deterministic prototype. |
| Signal safety | Partially supported | Clipping/finite/output-ceiling checks are useful but incomplete. |
| Defect reduction | Synthetic and metric evidence only | No generalized perceptual claim. |
| Professional quality | Unsupported | Requires independent, rights-clean, preregistered listening evidence. |
| Genre robustness | Unsupported | Current corpus is synthetic and not representative of rap/pop production variation. |
| Clean-vocal do-no-harm | Unsupported | Existing analyzer can pass harmful outcomes. |
| Desktop distribution | Undecided | Pedalboard/FFmpeg/Qt licensing and packaging branch must be resolved first. |
| Public hosted pilot | Code exists | Live production status was not independently verified in this audit. |

## Immediate execution boundary

The planning package was accepted on 2026-07-21 (PR #1 merged to `main`) and `DT-45 Evidence Semantics and Claim Quarantine` is **complete** (evidence: `07_DATA_AND_PROVENANCE/dt45_evidence/`). No model adoption, paid recruiting, dataset acquisition, public claim, or binary distribution is authorized by this state record.

Now ready: DT-47 (Metric Applicability Registry) and DT-49 (Rights/Consent/Withdrawal Graph — schema/graph/withdrawal-drill autonomous; consent/legal/deletion human-gated) in the `evidence` lane; DT-50 (Reproducible Environment and SBOM) in the `build` lane; DT-53 (Product Promise Discovery) discovery work in `product_data` — its scope decision is a human-only `product_scope` gate. DT-45 and DT-46 are complete. Dependency-independent internal work runs automatically in up to four lanes under the canonical autonomy policy. Routine engineering, research, documentation, and reversible implementation do not require repeated approval; money, people, credentials, rights/legal decisions, public claims, production/release, and irreversible deletion remain human-only.

### Verified baseline (DT-45 execution environment)

- Python 3.14.0 (Windows) system interpreter; all declared runtime deps import.
- `python -m pytest -q`: 412 passed, 4 warnings (baseline 362 + 50 new DT-45 tests).
- `python scripts/audio_regression.py`: 6/6 fixtures match goldens (no audio change).
- Env note: the 2 tests recorded as skipped under Python 3.12 execute and pass under 3.14; recorded as an environment difference, not a behavior change.

`05_ROADMAP/MILESTONE_REGISTRY.yaml` is the machine authority for each milestone's status, dependencies, lane, execution profile, resource class, write set, completion-evidence key, claim impact, and default quarantine behavior. The milestone detail documents are execution contracts; their Field 15 rows distinguish automatic checks from human-only gates.

## Known drift reconciled

- The old statement that legacy processing is the default is false for the audited commit.
- “362 tests” means collected tests at this baseline, not 362 passing tests.
- M24’s former `n >= 8` listening gate is invalid because it counts rows, not independent listeners, and mishandles ties and clean-safety outcomes.
- M29’s artist-consent protocol remains a draft requiring owner/legal review.
- M44 rate-limiting code is present; completion evidence is preserved in history, while the next roadmap starts at DT-45.

## Next review triggers

Update this file when a milestone changes state, a blocking decision is made, external evidence materially changes, or a canonical specification is superseded.
