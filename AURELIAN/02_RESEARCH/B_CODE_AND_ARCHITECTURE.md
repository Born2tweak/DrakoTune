# B — Code and Architecture Report

**As of:** 2026-07-21  
**Baseline:** `a3c51637a0c2ed18994a6950a45a72ccb753a93d`

## Executable flow

`scripts/run_alpha.py` preprocesses audio to 44.1 kHz, 16-bit mono; runs preflight and diagnostic analyzers; invokes the v2 decision planner by default; renders processors through the DSP executor; evaluates output; then writes report, manifest, trace, and exports. A `--legacy` branch remains explicit.

The architecture is modular at the package level—diagnostics, decision, DSP, evaluation—but evidence semantics cross those seams weakly. `EvaluationResult` and current manifests do not identify applicability, uncertainty, listener/item/source lineage, preregistration, or claim eligibility. Generic dictionaries permit silent drift.

## Preserve

- Deterministic champion path and ordered plan representation.
- Signal-safety checks, trace/report habit, fixture/golden infrastructure.
- Explicit legacy escape hatch during migration.
- Pure/testable modules where already present.

## Introduce

- Typed evidence and identity contracts before adding quality logic.
- DSP adapter boundary before distribution choice.
- Project/session service independent of CLI/web/desktop views.
- Applicability-aware metric registry and multiaxis verdict engine.
- Immutable experiment/result package with correction links.

## Avoid

A broad rewrite would erase working behavior and confound evidence rebuilding. Use characterization tests and strangler interfaces. Keep production champion behavior frozen until the new evaluation contract can compare old/new results.

## Evidence audit

| Source/symbol | Inspection result | Strength | Limitation/conflict | Architecture requirement | Recheck trigger |
|---|---|---|---|---|---|
| `scripts/run_alpha.py` | v2 is the default; legacy is explicit; stages and artifacts are traceable. | Strong repository fact | Script remains an orchestration-heavy entry point. | Characterize, then route through an application service. | CLI/orchestration change. |
| `src/orchestration.py` | Reusable core orchestration exists apart from the CLI. | Strong | Project lifecycle, atomic jobs, and UI-neutral recovery are not complete product services. | DT-52 seam then DT-69 project/application service. | Service migration. |
| `src/decision/planner.py` | Ordered deterministic plans are a strong inspectable champion. | Strong | Confidence/rationale ultimately depend on imperfect diagnostics. | Preserve behavior while adding typed intent/applicability. | Planner or threshold change. |
| `src/dsp_engine/` | Processors and executor are modular enough to wrap. | Strong | Backend capability, state, latency, streaming, and license identity are implicit. | Introduce `DspBackend`/capability contract before packaging or replacement. | Backend/dependency change. |
| Evaluation/reporting types | Existing outputs carry useful deltas and trace data. | Strong | Generic dictionaries omit applicability, uncertainty, independent units, rights, and claim eligibility. | DT-45–48 typed evidence migration. | Schema version change. |
| Preprocess/probe path | Working representation is always 44.1 kHz/16-bit mono and stereo is only warned about. | Strong | Historical product language can imply broader audio scope. | Make conversion an explicit versioned transform and scope boundary. | New channel/rate/context support. |
| Web job layer | Upload/job/download, retention, signed links, rate and concurrency controls exist in source. | Strong for code | Live configuration/availability was not verified; storage is in-memory. | Treat hosted deployment as a separate security/operations boundary. | Authorized deployment evidence. |
| Test/golden infrastructure | 360 pass, 2 skip; six audio goldens match. | Strong for audited build | Dependency/native build is not locked and goldens do not prove quality. | Preserve as T0/T1 regression, add build identity. | Any code/build/fixture change. |

## Coupling risk conclusion

The safest evolution is not a rewrite and not indefinite script growth. The project already has enough modularity for a strangler migration, but evidence semantics, project state, and DSP licensing must be separated before desktop work creates new coupling.
