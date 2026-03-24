# Default Instructions

Last updated: 2026-03-24

## Operating Rules

1. Read this file at the start of every task.
2. Read `STATUS.md`, `PLAN.md`, and `TASKS.md` before making significant changes.
3. Read `DESIGN.md`, `CONSTRAINTS.md`, `DECISIONS.md`, `LESSONS_LEARNED.md`, `RESEARCH.md`, `RESEARCH_INTAKE.md`, `../docs/PRD.md`, and `../docs/research.md` whenever the task touches architecture, tradeoffs, tool definition, memory behavior, or unfamiliar areas.
4. Treat `.codex/` as the persistent memory layer for this repository and keep it current as part of the task, not as optional cleanup.
5. Keep a strict distinction between:
   - implemented behavior in the codebase,
   - intended behavior described in design documents,
   - speculative future ideas.
6. Do not claim a capability exists unless it is implemented and verified.
7. When adding or changing important behavior, update the relevant `.codex` files in the same change.
8. When discovering a recurring pitfall or a better way to work in this repo, capture it in `LESSONS_LEARNED.md`.
9. When making a durable choice, capture it in `DECISIONS.md` with a short reason.
10. Before reporting back, verify the work if practical and make sure `.codex` still matches reality.
11. In any memory-system design or implementation, treat preservation of the active objective, current plan, success criteria, constraints, and recorded failures as higher priority than generic semantic recall.
12. Summaries are never the source of truth for task state; they are derived views over explicit task, plan, and outcome records.
13. When assessing external research, record a concrete verdict in `RESEARCH_INTAKE.md`: core now, useful later, or reject. Do not let paper enthusiasm override the current first-principles plan.
14. Keep `../docs/research.md` as the durable human-readable synthesis of the accepted research, while keeping `.codex/RESEARCH.md` concise.
15. Keep `../Chaneglog.md` current when the repository has a notable user-visible, workflow, or architecture change worth recording.

## What Good Maintenance Looks Like

- `STATUS.md` tells the truth about the current repo state.
- `PLAN.md` makes the sequencing and priorities explicit before implementation begins.
- `TASKS.md` makes the next sensible steps obvious.
- `DESIGN.md` summarizes direction without pretending unfinished work is done.
- `CONSTRAINTS.md` lists real boundaries that should shape implementation.
- `DECISIONS.md` explains why the repo is the way it is.
- `LESSONS_LEARNED.md` contains practical guidance worth reusing.
- `Chaneglog.md` records notable project changes in chronological order.
- `docs/PRD.md` states the tool purpose, scope, and success criteria in plain language.
- `docs/research.md` gives future sessions a readable research summary with source links, short quotes, and project-level lessons.

## Current Expectation

This repository is still at a very early stage. Favor clarity, simple scaffolding, and verified progress over premature complexity.
