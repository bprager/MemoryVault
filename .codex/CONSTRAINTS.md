# Constraints

Last updated: 2026-03-24

## Technical Constraints

- Python version target is `>=3.10`.
- The current project has no declared runtime dependencies.
- The codebase is at a very early stage, so added complexity should be justified by immediate value.
- The target graph service is Memgraph on `odin:7697`, not a fresh localhost database.

## Product And Architecture Constraints

- The intended product direction is local-first.
- The existing large design document should be treated as an active design input, not as proof that features exist.
- Future work should preserve a clean separation between repository memory, raw artifacts, and derived summaries.
- The verified Memgraph target is a shared instance with pre-existing labels, indexes, constraints, and data.
- Any MemoryVault graph design must include workspace isolation and globally unique IDs.
- Goal state, plan state, constraints, and recorded success / failure history must never become optional memory.
- High-value task-state memory should not be aggressively compressed away.
- Session state and long-term memory should remain distinct subsystems.
- Scratchpad state should remain distinct from durable memory.
- Retrieval should be guided by the active goal, but durable memory must remain grounded in provenance and exact source correspondence.
- Active-task context should include an explicit goal reminder and structured current-state header.
- Durable memories should retain provenance and confidence information.
- Declarative memories and procedural memories should not be forced through one identical lifecycle.
- Procedural guidance should grow incrementally as curated playbooks rather than through repeated whole-context rewrites.
- The architecture should avoid context-collapse patterns that destroy detail in the name of brevity.
- Long-term memory generation should stay off the user-facing hot path whenever practical.
- The design should optimize for both task quality and resource cost, not one in isolation.
- Durable declarative memory updates should be explicit and auditable rather than opaque whole-store rewrites.
- Evaluation should include goal drift, repeated failure, and context-collapse cases rather than only retrieval accuracy.

## Workflow Constraints

- `.codex/` should stay concise and useful; it is not a dumping ground for session chatter.
- Durable repo knowledge should be written down here rather than left implicit.
- If the repository state changes in a meaningful way, the relevant `.codex` files should be updated in the same task.
- User-authored or pre-existing files should not be overwritten casually, especially the large design note in the repo root.
- Planning should be revised critically before implementation instead of treating the first design as settled.
