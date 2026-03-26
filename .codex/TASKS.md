# Tasks

Last updated: 2026-03-25

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
- Keep the onboarding benchmark gate evidence-based; generated starter packs should not be trusted without held-out checks.
- Keep the pre-1.0 release path honest; do not cut `1.0.0` while the supported surface is still ambiguous.

## Next

- Implement one supported integration path in the `0.6.x` line.
- Add compatibility and migration checks for workspace profiles and strategy artifacts before `0.9.x`.
- Define the final `1.0` release gate and run it on a `0.9.x` release-candidate line.
- Expand the synthetic interrupted-task library across several generic task shapes.
- Add more Hugging Face dataset adapters beyond the current TaskBench, SWE-bench Verified, QASPER, and conversation-bench set.
- Add a review loop that summarizes repeated misses and wind-tunnel damage across runs and task families.
- Decide which repeated misses graduate into the next durable memory fields after `assumptions`.
- Expand onboarding cue learning beyond the current free-form focus, decision, lesson, question, source, constraint, and blocker patterns.
- Define the deterministic resume packet for general long-running work, including goal reminder and current-state header.
- Define workspace isolation for the shared Memgraph instance on `odin:7697`.
- Broaden the generated starter pack beyond learned failure markers and event-label aliases.
- Expand the Hugging Face onboarding path beyond saved row snapshots and the first three adapters.
- Expand the onboarding refresh loop beyond the first carried-forward cue phrases and test which ones generalize across task families.
- Define the HTTP API contract that the MCP adapter and SDKs will share.
- Define the CloudEvents event contract for invalidation, rebuilds, and async memory work.
- Define the cache-key strategy, invalidation rules, and lease model for multi-agent use.
- Extend strategy comparison from single-field ablations to whole memory-policy comparisons.
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
- Implemented a first onboarding flow with representative sampling, generated workspace profiles, YAML starter packs, and a held-out benchmark gate over bundled synthetic traces.
- Broadened the onboarding flow so it now learns event-label aliases and can run on adapted Hugging Face TaskBench, SWE-bench Verified, QASPER, and conversation-bench style rows.
- Added profile versions, strategy records, and improvement notes for onboarding and transfer runs.
- Added an offline transfer benchmark and CLI summaries for strategy runs.
- Added deeper strategy-tracker rollups for category wins and gaps, task-family impact, cost patterns, profile summaries, and workspace lineages.
- Added a benchmark-gated onboarding refresh loop that turns prior successful strategy evidence into a candidate next profile revision.
- Added learned cue phrases for free-form notes and taught the refresh loop to carry those cues forward when they improve held-out traces.
- Added cue-only benchmark measurements and tracker summaries so the project can see which cue categories actually transfer across task families.
- Added a fixed offline `release-benchmark` command and `release_benchmark_report.json` artifact for the first public release bundle.
- Added schema-version markers to saved workspace profiles and benchmark artifacts as the first narrow compatibility promise.
- Released `0.5.0` with one explicit `1.0` identity: a local-first memory-learning workbench.

## Likely First Milestones

1. More Hugging Face adapters and larger public-data samples
2. Next durable field promotions after `assumptions`
3. Whole-strategy comparison across task families
4. Richer cross-run strategy summaries
5. Broaden onboarding adaptation beyond the current learned cue phrases and keep verifying transfer
6. Onboarding refresh loop and profile maintenance
7. Canonical HTTP service contract and MCP adapter
8. Cache and lease model for shared multi-agent use
9. Workspace namespace and schema bootstrap
10. Session store plus explicit task / plan / outcome graph
