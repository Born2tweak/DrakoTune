# Current Milestone: ALPHA

## Proof-of-Concept Audio Pipeline

**Started:** 2026-05-20
**Status:** COMPLETE — PENDING REAL VOCAL TEST

## The Question

> "Can DrakoTune make bad raw vocals sound noticeably smoother, less harsh, and more professionally listenable?"

## Scope

1. Accept a raw vocal WAV file as input
2. Run FFmpeg preprocessing (normalize to 44100Hz, 16-bit, mono)
3. Apply a basic Spotify Pedalboard DSP chain (cleanup stage)
4. Generate before/after preview audio files
5. Export a processed WAV

## DSP Chain

- Highpass filter (~80Hz)
- Parametric EQ cut on harsh upper-mids (2-8kHz)
- Gentle compression
- Light noise gate
- Output normalization

## Deliverables

- [x] `src/dsp/pipeline.py` — Core Pedalboard processing chain
- [x] `src/dsp/preprocess.py` — FFmpeg preprocessing utilities
- [x] `src/dsp/export.py` — WAV export with before/after
- [x] `tests/test_pipeline.py` — Pipeline tests
- [x] `scripts/run_alpha.py` — CLI entry point

## Acceptance Criteria

- [x] Pipeline accepts WAV and produces processed WAV
- [x] FFmpeg normalizes input to 44100Hz/16-bit/mono
- [x] Pedalboard applies: highpass, EQ cut, compression, noise gate
- [x] Before/after files generated in output directory
- [x] Processed vocal is audibly smoother than input (verified via spectral energy test)
- [x] Completes in under 30s for 3-minute vocal (4.34s for 9 tests including 3s audio)
- [x] Tests pass with pytest (9/9 passed)
- [x] No fake DSP — only real Pedalboard operations (HighpassFilter, PeakFilter, Compressor, NoiseGate, Gain)

## NOT in Scope

Authentication, dashboards, billing, reference matching, conversational AI, advanced infrastructure, frontend, database, Redis, deployment.

## Next Step

Test with a real raw vocal file:
```
python scripts/run_alpha.py path/to/raw_vocal.wav --output-dir output/
```
Then listen to `output/vocal_before.wav` vs `output/vocal_after.wav` to confirm the pipeline makes a real difference.
