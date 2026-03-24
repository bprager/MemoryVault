# Codex Workspace

This directory is the repo-local memory layer for Codex sessions working in `MemoryVault`.

## Purpose

- preserve project context across sessions,
- reduce repeated rediscovery,
- keep intended design separate from implemented reality,
- make next steps and constraints explicit.

## Read Order

1. `DEFAULT_INSTRUCTIONS.md`
2. `STATUS.md`
3. `PLAN.md`
4. `TASKS.md`
5. `DESIGN.md`, `CONSTRAINTS.md`, `DECISIONS.md`, `LESSONS_LEARNED.md`, `RESEARCH.md`, and `RESEARCH_INTAKE.md` as needed

## File Map

- `DEFAULT_INSTRUCTIONS.md`: baseline operating rules for Codex in this repo
- `STATUS.md`: current snapshot of what exists and what does not
- `PLAN.md`: current implementation plan and planning review
- `TASKS.md`: active and next work items
- `DESIGN.md`: concise architectural summary and source-of-truth pointers
- `CONSTRAINTS.md`: hard limits and guardrails
- `DECISIONS.md`: durable choices and why they were made
- `LESSONS_LEARNED.md`: mistakes avoided, patterns worth repeating
- `RESEARCH.md`: external research and the design implications that matter here
- `RESEARCH_INTAKE.md`: source-by-source research verdicts and what to adopt, defer, or reject

## Maintenance Rules

- Update only the files touched by the task.
- Prefer replacing stale summaries over piling on noisy history.
- Keep durable facts here; keep transient chatter out.
- If a task changes behavior, architecture, or priorities, update the relevant docs before finishing.
