# Reproduce Runbook (DT-50)

How to reconstruct a test/render environment and audit the dependency/license
inventory. Records facts only — accepting a license obligation or a distribution
posture is a human-only gate (DT-51).

## Artifacts

| Artifact | Path | Meaning |
|---|---|---|
| SBOM | `AURELIAN/08_TOOLING/sbom.json` | full dependency closure with versions + licenses; runtime + FFmpeg fingerprint |
| Env fingerprint | `AURELIAN/08_TOOLING/env_fingerprint.json` | compact runtime + direct-dep pins + SBOM content hash |
| Lockfile | `AURELIAN/08_TOOLING/requirements.lock` | `pip freeze` pins for the resolved environment |

## Regenerate

```bash
PYTHONPATH=. python scripts/build_sbom.py
python -m pip freeze --exclude-editable > AURELIAN/08_TOOLING/requirements.lock
pytest -q tests/test_reproducibility.py
```

## Two-clean-environment parity

The acceptance criterion "two clean environments resolve identical artifacts and
pass baseline/goldens" is exercised by `.github/workflows/ci.yml`, which runs a
two-cell matrix (`clean_env: [a, b]`); each cell does a fresh `pip install -e
".[dev,web]"`, `pip check`, the full suite, the audio goldens, and SBOM
validation, then uploads its SBOM for diff.

**In-session status:** environment A (this machine) passed the full suite and
6/6 goldens. The second clean-environment parity is delegated to CI and is
recorded as *pending an actual CI run* — it is **not** claimed as locally proven.
See the DT-50 completion evidence for the exact unmet criterion.

## Captured license facts (not decisions)

- FFmpeg on the fingerprinting host is a **GPL-3.0-or-later** build
  (`--enable-gpl --enable-version3`). This is the D-010/D-015 signal: a bundled
  GPL FFmpeg would impose copyleft obligations on a desktop distribution. The
  fact is captured here; the distribution decision is DT-51 (owner + counsel).
- `pedalboard` is GPL-3.0; captured in the SBOM closure. Same downstream
  implication; same human-only decision.
