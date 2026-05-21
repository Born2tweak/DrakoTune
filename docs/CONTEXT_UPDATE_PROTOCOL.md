# CONTEXT UPDATE PROTOCOL
> Rules for maintaining `DRAKOTUNE_CONTEXT_EXPORT.md`

## Owner

The Orchestrator owns the context export. Sub-agents report changes; Orchestrator writes updates.

## Read Rule

Every agent MUST read the context export before starting work. No exceptions.

## When to Update

| Trigger | Update Sections |
|---|---|
| Milestone change | 1 (Snapshot), 6 (Milestone), 10 (Next Actions) |
| File created/edited | 7 (Repo State), 9 (Recent Changes) |
| Architecture change | 4 (Stack), 8 (Decisions) |
| Decision made | 8 (Decisions) |
| Bug found/fixed | 7 (Repo State) |
| Work completed | 9 (Recent Changes) |

## Sub-Agent Reports

At end of work, report to Orchestrator:
1. What changed (files)
2. What was decided
3. What was completed
4. What is broken
5. What should happen next

## Format

**Decisions (Section 8):** Add at TOP, reverse chronological.
```
- YYYY-MM-DD: [Decision]. Reason: [Why]. Files: [list]
```

**Changes (Section 9):** Add at TOP, reverse chronological.
```
- YYYY-MM-DD | [Agent] | [What changed]
```

## Milestone Gate

No milestone complete until: context export updated, all acceptance criteria checked, next actions point to next milestone.

## Compression

Keep sections 8-9 to last 10 entries. Archive older entries to `docs/archive/`. Never delete vision, architecture, or milestone content.

## Handoff Rule

When handing to another agent: "Read `docs/DRAKOTUNE_CONTEXT_EXPORT.md` first."

## Enforcement

Work without context update = incomplete. Next agent must flag stale context as blocker.
