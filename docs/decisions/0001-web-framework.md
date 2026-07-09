# ADR 0001 — Web skeleton framework: FastAPI (Python)

- **Status:** accepted (2026-07-09)
- **Milestone:** M12 (Web App Skeleton)

## Context

The Technical Design Spec recommends "Next.js or comparable full-stack React
framework, TypeScript" for the eventual web application. The DrakoTune core,
however, is Python (diagnostics, decision engine, DSP execution, evaluation,
reports). The M12 acceptance criteria are modest: upload, job status, before/
after playback, report view, clear errors — enough for a local user to upload a
sample and view a result.

At decision time the environment had no Node/npm toolchain and no `package.json`.
A React/Next.js frontend would additionally need to call the Python core across a
process boundary.

## Decision

Build the M12 skeleton as a **FastAPI** backend with a minimal server-rendered
HTML UI, reusing the Python core directly. Endpoints follow the spec's API
concepts: `POST /api/audio/upload`, `GET /api/jobs/{id}`, `GET /api/audio/{id}/{which}`,
plus HTML `GET /` and `GET /jobs/{id}`.

## Consequences

- **Positive:** no cross-language boundary; the deterministic core is reused
  as-is; fully testable in-process via `fastapi.testclient`; runnable locally
  with `uvicorn`.
- **Cost:** adds `fastapi`, `uvicorn`, `python-multipart` (optional `web` extra);
  `httpx` (dev) for the test client.
- **Migration path:** the JSON API is frontend-agnostic. A future React/Next.js
  frontend (the spec's long-term direction) can consume these same endpoints
  without changing the core. If/when adopted, this ADR should be superseded.

## Alternatives considered

- **Stdlib `http.server`:** zero new deps, but hand-rolled routing/uploads and
  not representative of the product.
- **Next.js/React now:** matches the spec but requires a Node toolchain and a
  process bridge to Python; too heavy for a skeleton and not buildable in-session.
