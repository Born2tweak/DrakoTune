# ADR 0005 — Compression policy: strict defect-correction + explicit "polished" style preset

- **Status:** accepted (2026-07-12, product-owner decision)
- **Context:** M33 measured that the legacy dynamics threshold (CV > 0.40,
  calibrated on synthetic tones) planned a compressor for **100% of clean real
  vocals** (natural singing: CV 0.54–0.82 on corpus-v1). Recalibrating to 0.90
  made compression rare and objectively cleaner — but audibly changed the
  sound the product owner had already evaluated and liked ("more solid"),
  because gentle compression was effectively an unconditional style. Fidelity
  metrics cannot decide this: they punish all compression, while listeners
  often prefer it.
- **Decision:** two explicit presets:
  1. **`clean` (default):** strict defect correction. Compression only fires
     on evidence (CV > 0.90 gain-jump-class inconsistency; overcompression
     abstention applies). This is the scientifically defensible default and
     the preset used for all benchmark/listening validation of defect claims.
  2. **`polished` (opt-in style):** adds a gentle style compressor whose
     threshold is set relative to the measured post-gain RMS (so it actually
     engages at any input level), plus the post-compression de-esser guard.
     Labeled in plans/reports as **style, not defect correction**; excluded
     from defect-claim evidence; validated by listener preference only.
- **Consequences:** the do-no-harm CI gate binds the `clean` preset; `polished`
  intentionally alters clean input and says so. Claims language must never
  attribute defect repair to the style compressor. Listening sessions that
  test the polished preset are separate from defect-correction sessions.
- **Superseded if:** blinded preference data (M24-class) shows a different
  default serves users better.
