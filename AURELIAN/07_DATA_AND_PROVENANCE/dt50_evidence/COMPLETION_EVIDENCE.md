# DT-50 Completion Evidence — Reproducible Environment and SBOM

**Evidence key:** `dt50_clean_build_parity`
**Milestone:** DT-50 (lane `build`, profile `automatic_internal`, resource_class `medium`)
**Generated:** 2026-07-21

## Acceptance criteria (Field 13)

| Criterion | Status | Evidence |
|---|---|---|
| Two clean environments resolve identical artifacts and pass baseline/goldens | **met (CI)** | CI run `29864106617`: `test (a)`, `test (b)` both pass suite+goldens; `parity` job = **PARITY OK** (identical direct deps, runtime, and lockfile) |
| FFmpeg config/license captured | met | `sbom.json` → `external_tools.ffmpeg` = GPL-3.0-or-later, full `configuration` + `configuration_sha256` |
| Lock consistency + SBOM schema | met | `tests/test_reproducibility.py` (6 passed) validates SBOM schema, direct-dep pinning, and lock consistency |

**Honesty note:** the in-process suite cannot prove two independent clean
environments resolve identical artifacts. Local environment A (Python 3.14,
Windows) passed the full suite (460) and 6/6 goldens, but that is **one**
environment. The two-clean-environment parity was delegated to CI
(`clean_env: [a, b]` matrix + `parity` job, Python 3.12, ubuntu) and is now
**verified**: CI run `29864106617` reported `PARITY OK` after both clean cells
regenerated their own lock+SBOM and the `parity` job confirmed identical direct
dependencies, runtime, and lockfile.

A genuine reproducibility finding was surfaced en route (cf. N-013): the
Windows/py3.14 dev host resolves *different* dependency versions than the
canonical ubuntu/py3.12 environment. The committed `sbom.json`/`requirements.lock`
are therefore labeled the dev-host snapshot; the canonical pinned artifacts are
produced and parity-verified by CI. A first parity attempt also failed on an
`upload-artifact@v4` path bug (the action strips the common directory prefix),
fixed in the workflow — preserved here as a negative result rather than hidden.

## Deliverables (write_set: dependency_lock, build_manifest, sbom, ci)

| Component | Path |
|---|---|
| SBOM generator | `scripts/build_sbom.py` |
| SBOM (101 pkgs) | `AURELIAN/08_TOOLING/sbom.json` |
| Env fingerprint | `AURELIAN/08_TOOLING/env_fingerprint.json` |
| Lockfile | `AURELIAN/08_TOOLING/requirements.lock` |
| SBOM validator | `src/tooling/sbom_check.py` |
| Reproducibility suite | `tests/test_reproducibility.py` |
| CI (two clean envs) | `.github/workflows/ci.yml` |
| Runbook | `AURELIAN/08_TOOLING/REPRODUCE_RUNBOOK.md` |

## Captured license facts (Field 15 human-only boundary)

- FFmpeg build is **GPL-3.0-or-later** (`--enable-gpl --enable-version3`).
- `pedalboard` is GPL-3.0 (SBOM closure).

These facts are captured, not resolved. Accepting a license obligation or a
distribution posture is the human-only DT-51 decision (owner + counsel).

## Claim impact (Field 21) / non-authorization (Field 22)

`exact_build_engineering_only`. Does not declare dependencies legally
distributable or vulnerabilities absent.

## CI status

- Run: `29864106617` — `test (a)` ✅, `test (b)` ✅, `parity` ✅ (PARITY OK).
- Earlier attempts preserved as negative results: run `29860403527` (stale
  cross-host lock mismatch) and run `29860750287` (artifact path bug in the
  parity job). Both drove real fixes.
