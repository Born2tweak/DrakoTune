# DT-77 Improvement Brief — Evidence-Led Failure Taxonomy

Seeds for the DT-77 milestone (Evidence-Led Failure Taxonomy and Improvement
Brief). Each brief is a *candidate experiment*, not a change. Promotion requires
the DT-57→DT-60 preregistered study line; none is promoted here.

## B-1 — Planner under-engages on real rap acapella  *(highest leverage; from F-1)*

**Evidence:** `reports/evaluations/paired-corpus/FINDINGS.md` F-1; N-015.
On 7/9 real rap-acapella pairs the champion applied **0 actions** despite the
diagnosis measuring high mud (6.6), an audible noise floor (−44.5 dBFS), and a
dark centroid on the best-aligned pair (P-01) — because objective confidences fall
below the action gate (`reduce_noise` fired at 0.22 → `report_only`).

**Hypothesis:** the planner's confidence/threshold gating is calibrated to
synthetic degradations + clean studio singing; real home-recorded rap sits in a
feature region where it under-fires. Recalibrating engagement (not the DSP)
recovers most of the perceived gap.

**Bounded experiment (predeclared before any run):** on artist-held-out splits,
lower the engagement gate for mud/low-mid and noise objectives *within* their
existing safe processor ranges; measure objective gap-to-wet reduction on aligned
phrases + do-no-harm (peak/clip/SI-SDR preservation) on held-out artists. Reject
if do-no-harm breaches or the gap does not shrink. **Never tune on the tiny
private corpus directly** (overfitting/leakage) — use it only to size the effect.

## B-2 — Sub-floor sibilance detection  *(from F-1 + N-014)*

Real rap `sibilance_frame_p95 ≈ 0.095` sits below the DeEsser's 0.10 in-range
floor, so de-essing never engages — the same floor issue N-014 flagged. Brief:
a separately-validated lowering of the frame floor with its own do-no-harm proof,
and de-essing executed **inside** the −0.2 dBFS safety envelope (N-014 lesson).

## B-3 — Low-mid ("weak mic") control  *(from F-1 mud 6.6, F-3 Δlowmid<0)*

The dominant audible "weak-mic/boxy" defect is untreated low-mid buildup. Brief:
phrase-adaptive 250–700 Hz control sized by the measured mud ratio, bounded,
inside the safety envelope. Note: true mic/room *reconstruction* (dereverb,
resonance suppression) is a **missing module** (class (c)) → separate brief B-4 if
B-3 proves insufficient.

## B-4 — Missing modules (deferred)

Dereverberation, resonance suppression, and bounded harmonic enhancement are not
in the current processor registry. Only pursue after B-1/B-3 quantify how much the
gap is closable with existing processors (oracle residual, DT-55E). Building new
DSP before that risks solving the wrong problem.

## Priority order (from measured leverage, aligned to E-OWN-001)

1. **B-1** planner engagement (nothing else matters if the chain never runs)
2. **B-3** low-mid / weak-mic control (dominant audible defect)
3. **B-2** sibilance floor
4. E1 harshness dynamics · E7 cohesion (per orchestration plan)
5. **B-4** new modules — only if oracle residual proves them necessary
