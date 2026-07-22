# DrakoTune Autonomous Remediation Package

This package is the governing control plane for bringing DrakoTune from its current partially integrated, incompletely validated state to evidence-backed production readiness.

It is designed to be placed at the root of the DrakoTune repository and executed by a capable coding agent. Creating or reading these files is not completion. The agent must inspect the real repository, reconcile the templates with repository facts, implement the required controls, and continue through every dependency-ready milestone without waiting for phase-by-phase approval.

## Start here

Give the executing agent this instruction:

> Read `DRAKOTUNE_FULL_AUTONOMOUS_REMEDIATION_PROGRAM.md` and treat it as the governing execution contract. Reconcile it against the actual repository, replace every `RECONCILE_FROM_REPOSITORY` value with direct evidence, create any missing executable control-plane components, and run the full remediation program continuously. Do not stop after auditing, planning, research, writing documents, opening a pull request, or starting CI. Continue through every safely executable milestone, repair failures, expand the roadmap when gaps emerge, and ask me only for a consolidated irreducibly human decision.

## Package contents

- `DRAKOTUNE_FULL_AUTONOMOUS_REMEDIATION_PROGRAM.md`: governing execution contract.
- `control/execution-policy.yaml`: autonomy, retry, continuation, and stop rules.
- `control/milestone-registry.yaml`: initial dependency graph and graduation gates.
- `control/canonical-state.json`: durable restart and recovery state.
- `control/deficiency-register.yaml`: initial known deficiencies to verify and expand.
- `control/evidence-index.json`: requirement-to-evidence ledger.
- `control/human-gates.yaml`: narrow list of decisions requiring human authority.
- `control/scorecard.yaml`: non-averaging 10/10 graduation criteria.
- `control/research-registry.yaml`: targeted research streams and required decision outputs.

## Non-negotiable behavior

1. Repository evidence overrides the initial templates.
2. Unknown values must be reconciled; they must never be guessed.
3. A milestone cannot complete merely because code, tests, or documentation exist.
4. Every milestone must prove production reachability, acceptance criteria, regression safety, evidence capture, and state reconciliation.
5. Phase boundaries are dependency boundaries, not user-approval checkpoints.
6. CI waiting, test failures, missing research, and reversible ambiguity are continuation states—not stopping conditions.
7. An overall score cannot hide a weak category. Every scorecard category must pass independently.

## Initial installation outcome

The first execution must leave the repository with:

- a reconciled current-state record;
- an evidence-backed deficiency register;
- a machine-readable ready queue;
- verified production entry points;
- corrected milestone statuses;
- an active remediation milestone;
- a durable automatic continuation action;
- no unsupported public claim escaping the claim gate.

