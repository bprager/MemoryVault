# Tasks

Last updated: 2026-03-24

## Active

- Maintain `.codex/` as the codebase evolves.
- Keep `Chaneglog.md` current when notable project changes are made.
- Keep `docs/PRD.md` current as the product definition changes.
- Maintain `docs/research.md` as research changes the intended architecture.
- Keep the project in planning mode until the phase-1 scope and schema are agreed.
- Keep the combined research synthesis aligned with the planning notes.

## Next

- Define the phase-1 thin slice around explicit task, plan, constraint, and success / failure memory.
- Define the deterministic prompt-assembly package for active work, including goal reminder and current-state header.
- Incorporate the new session / memory / page-store split into the written architecture.
- Define the scratchpad or working-state lifecycle explicitly.
- Define declarative memory update operations and conflict handling.
- Define how procedural playbooks should grow, refine, and retire without monolithic rewrites.
- Define how goal-conditioned retrieval is kept source-grounded to avoid self-confirming drift.
- Add cost-versus-quality evaluation criteria to the benchmark plan.
- Add benchmark cases for goal drift and context collapse.
- Decide how provenance and confidence should be represented in phase 1.
- Define workspace isolation for the shared Memgraph instance on `odin:7697`.
- Create an initial package structure instead of relying on a single root script.
- Define how local storage and Memgraph bootstrapping should be configured for development.
- Decide what raw content should stay in Memgraph versus external files or object storage.

## Completed Recently

- Established repo-local Codex memory and maintenance instructions.
- Ingested the large root design note into a repo-local planning pack.
- Verified that `odin:7697` is a live Memgraph endpoint and that it is a shared instance.
- Reviewed external research on agent memory, reflection, graph retrieval, and long-horizon planning.
- Assessed the first five user-provided research documents and recorded per-source verdicts.
- Assessed the second five user-provided research documents and recorded per-source verdicts.
- Assessed the final user-provided research batch and synced the resulting lessons into the plan.
- Created `docs/research.md` as the long-form research summary for future reference.
- Created `docs/PRD.md` and replaced the placeholder README and project metadata with concrete product descriptions.
- Created `Chaneglog.md` in the repo root and added standing instructions to maintain it.

## Likely First Milestones

1. Workspace namespace and schema bootstrap
2. Session store plus explicit task / plan / outcome graph
3. Provenance and confidence model for durable memories
4. Scratchpad and working-state lifecycle
5. Deterministic task package with explicit goal and current-state header
6. Basic ingestion of repository notes and docs
7. Deterministic retrieval of objective, plan, constraints, and recent outcomes
8. Hybrid retrieval with graph expansion and semantic support
9. Compression and summary layers
10. Test and benchmark harness
