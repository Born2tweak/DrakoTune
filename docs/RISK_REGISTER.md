# DrakoTune Risk Register (living)

> Created 2026-07-10 (post-dataset-research). Review at every milestone
> completion report. Severity = impact × likelihood (H/M/L).

| ID | Risk | Sev | Status / evidence | Mitigation | Owner gate |
|---|---|---|---|---|---|
| R01 | Audio artifacts from gate/compressor on real vocals (breath/word-tail truncation, pumping) | H | Unknown — never tested on real vocals | M24 artifact checklist; M26 fixes + clean-input do-no-harm CI gate | M24 |
| R02 | Overprocessing / intentional-style destruction (Auto-Tuned, deliberately distorted vocals) | H | No detector exists | Conservative bounds (in place); preflight advisory; research gap RG-3; abstain when confidence low (in place) | M25/M27 |
| R03 | Loudness bias in all informal listening to date | H | Confirmed: exports not loudness-matched | M23 matched exports; evaluation already warns | M23 |
| R04 | Diagnosis error controlling DSP (precedent: M17 muddiness 100% FP) | H | Partially mitigated (confidence caps, corroboration, bounds) | M25 graded calibration + confusion matrices; new diagnoses advisory-only | M25 |
| R05 | False confidence from speech-trained metrics (DNSMOS/NISQA/SRMR) on singing | M | Not yet used | Developer-only proxies, labeled, never product-facing (validation plan §3) | M23 |
| R06 | Dataset licensing breach (restricted audio in git / commercial claims from NC data) | H | No data present yet | Governance tiers + git guards (M21); manual checkpoints; legal review before commercial claims from Tier B | M21 |
| R07 | Dependency licensing: **pedalboard GPL-3.0**; FFmpeg build-dependent | M | Confirmed in audit | Fine for local/server use; **legal checkpoint before any distributed closed-source binary**; document FFmpeg build | pre-distribution |
| R08 | Artist rights / voice identity / privacy in future data collection | H | No collection yet | Governance §6 consent protocol is a hard gate before M29; no cloning/biometrics ever | M29 |
| R09 | Unsupported scientific claims ("professional", genre universality) | H | Currently well-gated (pilot docs) | Claims policy (validation plan §7); genre-scoped until M29 | continuous |
| R10 | Genre/microphone/language bias: corpus skews trained-singer/pop/Mandarin/speech; target genre (rap/bedroom) absent from public data | H | Confirmed by research §16 | Genre-scoped claims; synthetic bedroom simulation; M29 proprietary mini-corpus | M29 |
| R11 | Speech→singing transfer of thresholds (HPF corner vs low registers; gate thresholds) | M | 80–100 Hz HPF vs E2≈82 Hz fundamental — exposure small but real | M25 register estimate; M26 register-aware policy only if evidence shows damage | M26 |
| R12 | Product scope creep (separation, pitch correction, mastering, frontend rebuild, cloud) | M | Pressure exists (old Phase 0–7 plan, agent configs) | Roadmap gates; 05-plan SUPERSEDED; standing prohibition list | continuous |
| R13 | ML prematurity | M | None planned (good) | ADR-gated: deterministic limits documented + data rights cleared first | future |
| R14 | Performance/long-file memory | M | **Measured (M36):** linear ~180 MB peak alloc per audio minute, ~0.07× realtime; a 5-min file peaks ~900 MB — risky under system memory pressure (two MemoryErrors observed 2026-07-12 with browsers loaded) | Perf benchmark + CI budget test (test_performance.py); chunked/streaming processing is the fix if >10-min files become a use case | monitored |
| R15 | Insufficient real-audio fixtures in CI (6 synthetic goldens only) | M | Confirmed | M22 adds Tier-A-derived CI fixtures (≤ 25 MB, attributed) | M22 |
| R16 | Inadequate listener sample → noise read as signal | M | No listeners yet | Pre-registered criteria, ≥ 8 listeners, catch trials, binomial tests (validation plan §5–6) | M24 |
| R17 | Documentation drift (CONTEXT_EXPORT stale; AutoClaw agent configs reference dead orchestrator) | L | Confirmed in audit | Mark stale docs superseded in next housekeeping commit; single canonical roadmap maintained | M21 housekeeping |
| R18 | Double-processing already-mixed vocals (no detector for prior processing) | M | Confirmed gap | Input guidance (M27); research gap RG-4; advisory diagnosis candidate | M27 |
| R19 | Golden-fixture ossification (thresholds frozen around synthetic behavior) | L | M17 precedent shows healthy process | Goldens regenerate only with evidence-backed version bumps | continuous |
