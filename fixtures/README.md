# Audio Fixture Library (M02)

Deterministic, synthetic regression material for DrakoTune's diagnostics, DSP,
evaluation, and report layers.

## Policy

1. **Synthetic only.** Fixtures are generated from code, never recorded from real
   users. This avoids copyright and privacy issues (Bible: user audio is private
   creative material).
2. **Deterministic.** Every fixture is built from a fixed seed. The committed WAV
   bytes are reproducible; `tests/test_fixtures.py` fails if a regeneration would
   change them, so drift is caught in CI.
3. **Small and mono.** 1 second, 44100 Hz, mono, PCM_16 — enough to exercise the
   spectral/temporal analyzers without bloating the repo.
4. **Metadata is declared, not asserted (yet).** Each fixture ships a manifest in
   `expected/`. The `expected_diagnoses` field is **informational in M02** —
   diagnostic thresholds are not calibrated, so tests must not assert specific
   severities until M04–M06 pin them.

## Layout

```
fixtures/
  generate.py            deterministic generator (python fixtures/generate.py)
  loader.py              list_fixtures / load_fixture / load_metadata
  audio/<name>.wav       committed synthetic audio
  expected/<name>.json   declared metadata + informational expectations
```

## Current fixtures

| name | category | intent |
|------|----------|--------|
| `clean_tone` | clean | harmonic vocal-like tone; minimal issues |
| `harsh` | harsh | narrow 3.5kHz / 6.5kHz energy |
| `muddy` | muddy | dominant 300Hz low-mid buildup |
| `noisy` | noisy | quiet tone over elevated noise floor |
| `clipped` | clipped | hard-clipped full-scale plateaus |
| `silence` | silence | near-digital-silence edge case |

## Regenerating

```bash
python fixtures/generate.py
```

Only change fixtures deliberately. If a regeneration changes the committed bytes,
that is a behavior change to review — not something to silently overwrite.

## Loading (in tests)

```python
from fixtures import load_fixture, list_fixtures

fx = load_fixture("harsh")
fx.audio          # np.ndarray float32
fx.sample_rate    # 44100
fx.metadata       # declared manifest dict
```
