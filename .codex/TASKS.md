# Tasks

Last updated: 2026-03-24

## Active

- Maintain `.codex/` as the codebase evolves.
- Keep `Changelog.md` current when notable project changes are made.
- Keep `docs/PRD.md` current as the tool definition changes.
- Maintain `docs/research.md` as research changes the intended architecture.
- Keep the combined research synthesis aligned with the implementation direction.
- Preserve the goal guard in every resume path as the discovery loop evolves.
- Review repeated resume misses and turn stable patterns into candidate core memory fields.
- Keep the imported trace format simple enough that real task runs can be added without tooling friction.
- Keep the tool domain-agnostic until repeated evidence justifies specialization.
- Use synthetic traces or Hugging Face datasets whenever test inputs are needed.
- Keep the 90% coverage and lint gates green as the tool grows.
- Keep lifecycle logs and observability artifacts useful and lightweight.
- Keep `pyproject.toml` and the latest released section in `Changelog.md` in sync.
- Keep the integration design platform-neutral and centered on one canonical service boundary.
- Keep onboarding zero-touch by default and manual preparation optional.

## Next

- Expand the synthetic interrupted-task library across several generic task shapes.
- Add Hugging Face dataset adapters for code, tool-use, long-memory conversation, and evidence-grounded document tasks.
- Add a review loop that summarizes repeated misses and wind-tunnel damage across runs and task families.
- Decide which repeated misses graduate into the next durable memory fields after `assumptions`.
- Improve `recent_failures` extraction so weak or wrong attempts are retained even when they do not use the word `failed`.
- Define the deterministic resume packet for general long-running work, including goal reminder and current-state header.
- Define workspace isolation for the shared Memgraph instance on `odin:7697`.
- Define the onboarding flow for the next release.
- Define the generated starter pack schema and regeneration rules.
- Define the onboarding benchmark gate and refresh loop.
- Define the HTTP API contract that the MCP adapter and SDKs will share.
- Define the CloudEvents event contract for invalidation, rebuilds, and async memory work.
- Define the cache-key strategy, invalidation rules, and lease model for multi-agent use.
- Extend strategy comparison from single-field ablations to whole memory-policy comparisons.
- Add cross-run observability summaries so strategy comparisons include time and stage cost.
- Define the scratchpad or working-state lifecycle explicitly.
- Define declarative memory update operations and conflict handling.
- Define how procedural playbooks should grow, refine, and retire without monolithic rewrites.
- Define how goal-conditioned retrieval is kept source-grounded to avoid self-confirming drift.
- Decide how provenance and confidence should be represented once the durable schema starts hardening.
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
- Created `docs/PRD.md` and replaced the placeholder README and project metadata with a concrete plain-language project brief.
- Created `Changelog.md` in the repo root and added standing instructions to maintain it.
- Implemented a first local discovery prototype with built-in interrupted-task scenarios, local artifacts, resume packets, and improvement logging.
- Added a registry of Hugging Face benchmark leads for coding, tool-use, long-memory, and grounded document evaluation.
- Added a JSON intake path for imported interrupted-task traces and example imported trace files.
- Promoted `assumptions` into the resume packet as the first evidence-based durable field.
- Added a durable-field suggestion step based on repeated misses across runs.
- Added a tool-first strategy note and a zero-domain-knowledge data policy.
- Added a Memory Wind Tunnel that removes memory fields and measures the damage.
- Added a local quality gate and pre-commit hook with 90% coverage plus Python and Markdown linting.
- Added Python logging and basic observability artifacts for scenario and wind tunnel runs.
- Added a release-version sync check so future releases use the same version in `pyproject.toml` and `Changelog.md`.
- Added a documented hybrid integration strategy for HTTP, MCP, multi-agent coordination, and caching.
- Added a documented onboarding, priming, and learning strategy for the next minor release.

## Likely First Milestones

1. Synthetic and Hugging Face benchmark adapters
2. Next durable field promotions after `assumptions`
3. Whole-strategy comparison across task families
4. Cross-run observability summaries
5. Onboarding flow, starter pack, and benchmark gate
6. Canonical HTTP service contract and MCP adapter
7. Cache and lease model for shared multi-agent use
8. Workspace namespace and schema bootstrap
9. Session store plus explicit task / plan / outcome graph
10. Provenance and confidence model for durable memories
