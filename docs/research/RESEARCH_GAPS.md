# DrakoTune Research Gaps

> Questions that cannot responsibly become implementation tasks yet.
> Created 2026-07-10. Promote a gap to a milestone only with an evidence plan.

- **RG-1 — What objectively constitutes vocal harshness?** The 2.5–6 kHz band ratio correlates but perception is timbre/context-dependent; no public benchmark exists (research §31). Needed: listener-rated harshness severities on the M22 corpus before any "harshness score" is exposed to users.
- **RG-2 — What constitutes "smoothness" / "more professional"?** Only definable operationally as blinded preference vs references. No metric may claim it.
- **RG-3 — Distinguishing intentional distortion/Auto-Tune from defects.** No public data; likely needs Tier P examples + engineer labels. Until then: conservative bounds + abstention are the only safe policy.
- **RG-4 — Detecting already-processed (mixed/mastered) input.** Candidate signals: crest factor, spectral tilt, limiter fingerprints — unvalidated. Affects double-processing risk (R18).
- **RG-5 — Preferred amount of upper-mid reduction by artists/genre.** SAFE-DB gives descriptor→EQ hints (speech/instrument mix); real answer needs M24/M29 preference data.
- **RG-6 — When does de-essing cause perceived lisping?** No public threshold data; the M30 de-esser caps reduction at 8 dB as an engineering guard; perceived-lisp rates come from the artifact checklist in the blinded session.
- **RG-6b — Deterministic plosive detection (NEGATIVE RESULT, M32).** Every frame-energy rule family (LF burst factor × voice-band dominance × attack sharpness × 30–120 vs 120–250 Hz shape) plateaued at **31–55% clean FP** on corpus-v1 — on both studio (VocalSet) and consumer-device (vocadito) material — while reaching 100% recall only at strong severity. Real singing onsets are LF-dominant transients too. Plosive detection likely needs phase/onset-shape features or learned models; until then the `plosive_rate` observation is recorded but interpretation-less, and no plosive processor may be gated. The plosive degradation family (recipes v1.1.0) remains for future work.
- **RG-7 — Register-aware high-pass policy.** How should a low male fundamental (E2≈82 Hz) shift the HPF corner? Needs pitch-median estimates + fundamental-loss measurements on the corpus (M25/M26).
- **RG-8 — Can no-reference speech metrics rank singing cleanup at all?** Unknown; test DNSMOS/NISQA rankings against M24 human preferences before trusting them even as proxies.
- **RG-9 — Correct first target genre.** Product docs say underground rap; public validation data can't cover it. Decide after M24 (general defects) + M29 (genre evidence) whether claims lead with genre or with defect classes.
- **RG-10 — Should DrakoTune ever process vocals in mix context?** Current answer: no (isolated vocals only; full-mix input gets an advisory). Revisit only with separation-quality evidence and a licensing review of separation models (provenance concerns, research §20).
- **RG-11 — Reverb-amount estimation on singing.** SRMR-class estimators are speech-tuned; validate on reverb-graded synthetic pairs (M22 grid) before the advisory reverb diagnosis reports numbers.
- **RG-12 — Long-file behavior.** Memory/latency on 3–5 min takes untested; measure in M23 before the pilot invites full songs.
