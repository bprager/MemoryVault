# Status

Last updated: 2026-03-24

## Project Snapshot

- Repository name: `MemoryVault`
- Stated purpose: local-first tool for learning effective memory strategies for long-running AI work
- Current maturity: discovery prototype / pre-Memgraph

## What Exists Today

- `main.py` now forwards to a working CLI for the local discovery prototype.
- `pyproject.toml` still defines a very small Python project with basic metadata and minimal declared dependencies, including `mypy` for local type checks.
- `README.md` now gives a brief repo overview instead of a placeholder.
- `Chaneglog.md` now exists in the repo root as the project changelog.
- `docs/PRD.md` now states the tool purpose, scope, and success criteria in plain language.
- `docs/strategy.md` now explains the tool-first development strategy and phased approach.
- `docs/integration_strategy.md` now defines the planned platform-neutral integration strategy for HTTP, MCP, multi-agent use, and caching.
- `docs/onboarding_strategy.md` now defines the planned onboarding, priming, and learning cycle for the next minor release.
- `factory_context_compression_memgraph_design.md` contains a detailed design proposal for a Memgraph-based context compression system with anchor points.
- The design proposal has now been ingested into the repo-local planning documents in `.codex/`.
- The first batch of five external research documents has been assessed and folded into the repo-local planning documents.
- The second batch of five external research documents has been assessed and folded into the repo-local planning documents.
- The final batch of user-provided research documents has been assessed and folded into the repo-local planning documents.
- `docs/research.md` now exists as the durable human-readable research summary for the combined paper review.
- `memoryvault/` now contains a local discovery prototype for interrupted-task evaluation.
- The prototype stores raw run artifacts locally, extracts candidate memory items heuristically, builds resume packets, and records missed-memory improvement actions.
- The prototype keeps the final goal explicit as a run-level goal guard in every resume packet.
- The prototype now accepts imported interrupted-task traces from JSON files in the same format as the built-in scenarios.
- The first repeated-miss promotion has happened: assumptions are now preserved in the resume packet.
- The prototype can now suggest future durable fields by aggregating repeated misses across stored runs.
- The prototype now includes a Memory Wind Tunnel that reruns the same task with fields removed and measures the damage.
- The prototype now includes Python `logging`-based lifecycle logs with CLI-controlled level and optional file output.
- The prototype now writes `observability.json` and `wind_tunnel_observability.json` artifacts with timings, counts, and summary metrics.
- The local workflow now includes a release-version sync check between `pyproject.toml` and the latest released section in `Chaneglog.md`.
- The repo now has a documented hybrid integration plan: HTTP core service, MCP adapter, and CloudEvents-style event plane.
- The repo now also has a documented onboarding plan: zero-touch bootstrap, generated starter packs, and evidence-driven refresh.
- Built-in and imported synthetic traces now cover several task shapes, including tool-use dependencies.
- Example imported traces now exist under `examples/interrupted_runs/`.
- `tests/test_pipeline.py` now verifies the local discovery loop and the Hugging Face benchmark registry.
- The CLI can now list built-in scenarios, run the demo loop, run imported trace files, suggest durable fields, and print Hugging Face benchmark leads.
- A local quality gate now exists via `scripts/check_quality.sh` and a configured `.githooks/pre-commit` hook.
- The quality gate requires passing `ruff`, `mypy`, the repo-local Markdown linter, the release-version sync check, the test suite, and at least 90% Python coverage.
- A live Memgraph service has been verified on host `odin`, exposed on Bolt port `7697`.
- The verified Memgraph target is a shared, already-populated instance rather than an empty database.
- The verified Memgraph target exposes graph algorithms and vector/text search capabilities.
- `.codex/` now exists as the persistent project memory layer for Codex sessions.

## What Does Not Exist Yet

- No project-specific Memgraph namespace or schema bootstrap.
- No Memgraph integration in this repository.
- No live session capture from real agent work.
- No adapter from Hugging Face datasets into the interrupted-task harness beyond example JSON traces.
- No anchor scoring or compression logic.
- No raw-history / durable-memory split beyond the local JSON artifact store.
- No provenance or confidence model beyond simple heuristic scores and source references.
- No explicit scratchpad lifecycle has been implemented yet.
- No declarative-memory promotion loop from observed misses into durable schema updates.
- No benchmark harness over public datasets yet.
- No whole-strategy comparison beyond single-field ablations in the wind tunnel.
- No centralized metrics dashboard or external tracing backend.
- No HTTP core service, MCP adapter, shared cache, or event-bus integration is implemented yet.
- No onboarding flow, generated starter pack, prompt adaptation step, or onboarding benchmark gate is implemented yet.

## Current Reality Check

The repository now contains a real local discovery loop, a first strategy-comparison mechanism through the Memory Wind Tunnel, and basic local observability. It can surface what gets forgotten on resume, which removed fields hurt, and how long each stage took, but it does not yet compare full strategies across public datasets or persist and retrieve work through the target Memgraph architecture.

The intended integration shape is now clearer than the implementation: one canonical HTTP service with MCP and event adapters, plus explicit multi-tenant caching and concurrency rules.

The intended onboarding shape is also now clearer than the implementation: automatic workspace bootstrap first, optional YAML starter packs second, and cheap graph bootstrapping only as a provisional knowledge-plane accelerator.

## Suggested Near-Term Focus

1. Expand the synthetic task library without baking in domain-specific memory rules.
2. Add Hugging Face adapters so the same interrupted-task loop and wind tunnel can run on public data.
3. Review repeated misses and promote the next stable patterns into the durable memory schema, with `recent_failures` the strongest current candidate.
4. Extend the wind tunnel from single-field removal to whole-strategy comparison.
5. Roll up per-run observability into cross-run summaries so strategy comparisons have time and cost context.
6. Define the HTTP service contract, MCP adapter surface, and event contract in code.
7. Define the onboarding flow, generated starter pack format, and held-out onboarding benchmark gate in code.
8. Define the project workspace boundary and bootstrap plan for the shared Memgraph instance on `odin:7697`.
9. Keep compression and richer retrieval work behind verified multi-benchmark resume wins.
