# DrakoTune

Deterministic, explainable vocal-cleanup research software. Give DrakoTune a
raw vocal and it flags potential signal issues (such as harshness, sibilance,
mud, rumble, noise floor, uneven dynamics, mains hum, or low recording level),
applies bounded DSP moves when its current rules consider them applicable, and
produces a before/after plus a plain-language report. Detector findings are
measurements and hypotheses—not proof that a listener will hear a problem or
prefer the processed result.

**Hosted pilot URL:** [drakotune.fly.dev](https://drakotune.fly.dev). The
repository includes an experimental, public, unauthenticated pilot, but its
current deployment availability and configuration were not independently
verified in the 2026-07-21 audit. It is not a professional mix or mastering
engineer. See [docs/PILOT.md](docs/PILOT.md) before relying on it.

## What this is — and isn't

- **Is:** a deterministic signal-processing pipeline. Every diagnosis is a
  measured number (an `Observation`) with a named threshold; every processing
  action traces back to a specific diagnosis and a bounded parameter range.
  Nothing is applied on vibes.
- **Is not:** an AI model, a professional mastering engineer, or a magic
  "make it sound expensive" button. It will tell you what it *can't* fix
  (reverb, hum, an already-crushed master) and suggest rerecording instead of
  faking a fix.
- **Is not (yet):** validated by independent blinded human listening. Existing
  listening tooling is exploratory and its former sample/do-no-harm rules are
  not valid for confirmatory claims; the replacement protocol is specified in
  [AURELIAN](AURELIAN/README.md).

## Quickstart

```bash
git clone https://github.com/Born2tweak/DrakoTune.git
cd DrakoTune
pip install -e ".[dev,web]"
```

**CLI** — process one file:

```bash
python scripts/run_alpha.py path/to/vocal.wav --preset clean
# --preset polished adds gentle style compression + a de-esser guard (ADR 0005)
# writes output/<name>_before.wav, output/<name>_after.wav, output/<name>_report.md/.json
```

**Batch** — a whole folder:

```bash
python scripts/batch.py path/to/vocals/ --output-dir out/ --preset clean
```

**Web** — local server (same core, FastAPI front end):

```bash
python -m uvicorn src.webapp.app:app --port 8000
# open http://localhost:8000
```

**Tests:**

```bash
python -m pytest -q          # audited baseline: 360 passed, 2 skipped (362 collected)
python scripts/audio_regression.py   # golden-fixture audio regression
```

## How it works

```
FFmpeg preprocess (44.1kHz/16-bit/mono)
  -> preflight (rejects silent/too-short/corrupt input)
  -> diagnose (safety, loudness, spectral, advisory observations)
  -> decide (confidence-gated ProcessingPlan; safety before enhancement)
  -> execute (bounded Pedalboard chain + array processors, e.g. the de-esser)
  -> evaluate (before/after deltas, loudness-matched, self-audits its own output)
  -> report (plain-language findings/actions/limitations + JSON manifest)
```

Full architecture: [docs/03-architecture.md](docs/03-architecture.md).
Current milestone status and evidence trail:
[CURRENT_MILESTONE.md](CURRENT_MILESTONE.md).

## Documentation map

| Area | Start here |
|---|---|
| Product brief / PRD | [docs/01-product-brief.md](docs/01-product-brief.md), [docs/02-prd.md](docs/02-prd.md) |
| Architecture | [docs/03-architecture.md](docs/03-architecture.md) |
| Canonical post-M44 specifications & roadmap | [AURELIAN](AURELIAN/README.md) |
| Historical milestone record | [CURRENT_MILESTONE.md](CURRENT_MILESTONE.md) |
| Decisions (ADRs) | [docs/decisions/](docs/decisions/) |
| Validation plan & alpha evidence | [docs/validation/DRAKOTUNE_ALPHA_VALIDATION_PLAN.md](docs/validation/DRAKOTUNE_ALPHA_VALIDATION_PLAN.md) |
| Dataset governance & licensing | [docs/data/DATASET_GOVERNANCE.md](docs/data/DATASET_GOVERNANCE.md) |
| Research gaps (open questions) | [docs/research/RESEARCH_GAPS.md](docs/research/RESEARCH_GAPS.md) |
| Risk register | [docs/RISK_REGISTER.md](docs/RISK_REGISTER.md) |
| Security & privacy | [docs/security.md](docs/security.md), [docs/PRIVACY.md](docs/PRIVACY.md) |
| Pilot readiness | [docs/PILOT.md](docs/PILOT.md) |
| Deploying your own instance | [docs/DEPLOY_FLY.md](docs/DEPLOY_FLY.md) |

## Deployment

The web service needs FFmpeg + native DSP libraries and an in-memory job
store — it runs on a persistent container host, **not** serverless/edge
platforms (Vercel, Netlify, etc. — see the reasoning in
[docs/DEPLOY_FLY.md](docs/DEPLOY_FLY.md)). Ships as a `Dockerfile` +
`fly.toml` for [Fly.io](https://fly.io); the same image runs on any Docker
host. The deployment configuration includes rate limiting and a concurrency
cap (see the deploy doc) since it has no login gate; deployed behavior must be
verified separately from source-code inspection.

## Status

Deterministic core (diagnose → decide → execute → evaluate → report) is
built and regression-tested (audited baseline: 360 passed, 2 skipped; six
audio goldens). It has a synthetic-degradation corpus built from real-vocal
sources, style presets, a gated de-esser, hum removal, and an exploratory
in-browser listening runner. It is not yet supported by a statistically valid,
independent listening verdict, representative target-genre evidence, or a
desktop distribution decision. Canonical next work and exact claim boundaries:
[AURELIAN](AURELIAN/README.md). Historical build evidence:
[CURRENT_MILESTONE.md](CURRENT_MILESTONE.md).

## License

No license file is currently declared for this repository — treat it as
**all rights reserved** pending an explicit choice. Note: this project
depends on [Spotify's Pedalboard](https://github.com/spotify/pedalboard),
which is **GPL-3.0**; running it as a network service (as this deploy does)
does not trigger source-disclosure obligations (that's AGPL-specific), but
*distributing* a binary that links it would need review. See the GPL note
in [docs/DEPLOY_FLY.md](docs/DEPLOY_FLY.md).
