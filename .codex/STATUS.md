# Status

Last updated: 2026-04-01

## Project Snapshot

- Repository name: `MemoryVault`
- Stated purpose: local-first tool for learning effective memory strategies for long-running AI work
- Current maturity: `1.0.0` stable line / pre-Memgraph

## What Exists Today

- `main.py` now forwards to a working CLI for the local discovery prototype.
- `pyproject.toml` still defines a very small Python project with basic metadata and minimal declared dependencies, including `mypy` for local type checks.
- `README.md` now gives a brief repo overview instead of a placeholder.
- `Changelog.md` now exists in the repo root as the project changelog.
- `docs/PRD.md` now states the tool purpose, scope, and success criteria in plain language.
- `docs/strategy.md` now explains the tool-first development strategy and phased approach.
- `docs/integration_strategy.md` now defines the planned platform-neutral integration strategy for HTTP, MCP, multi-agent use, and caching.
- `docs/onboarding_strategy.md` now defines the planned onboarding, priming, and learning cycle for the next minor release.
- `docs/release_plan.md` now defines the concrete path from the current prototype line to `1.0.0`.
- `docs/release_plan.md` now also names a concrete `0.6.0` milestone: a thin local HTTP service with a first four-endpoint contract and end-to-end workflow test.
- `docs/release_plan.md` now also includes a first file-by-file implementation checklist for the `0.6.0` integration slice.
- The earlier standalone root design note has been retired after its useful content was folded into the repo-local planning documents in `.codex/`.
- The first batch of five external research documents has been assessed and folded into the repo-local planning documents.
- The second batch of five external research documents has been assessed and folded into the repo-local planning documents.
- The final batch of user-provided research documents has been assessed and folded into the repo-local planning documents.
- The `HyperAgents` paper has now been assessed and folded into the research and planning notes.
- The `Hindsight is 20/20` paper has now been assessed and folded into the research, design, and planning notes.
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
- The prototype now includes a first zero-touch onboarding flow over JSON traces and adapted Hugging Face dataset rows, with representative sampling, generated workspace profiles, YAML starter packs, learned label aliases, and a held-out benchmark gate.
- The onboarding flow now assigns a content-based version to each learned workspace profile.
- The repo now records strategy runs and short improvement notes for onboarding and transfer evaluations.
- The prototype now includes an offline transfer benchmark that tests whether a learned profile helps on a different task family.
- The strategy tracker now also summarizes recurring wins and gaps, task-family impact, basic cost patterns, profile summaries, and workspace lineages.
- The onboarding layer now includes a benchmark-gated refresh loop that uses prior successful strategy evidence to propose a next profile revision.
- The onboarding and refresh path now also learn free-form cue phrases, so unlabeled notes can still recover current focus, decisions, lessons, open questions, sources, constraints, and blockers.
- The tracker now measures cue-only deltas and can report which cue categories transferred across task families.
- The current Hugging Face onboarding adapters cover TaskBench, SWE-bench Verified, QASPER, and conversation-bench style rows.
- The CLI now includes a fixed `release-benchmark` command that runs an offline public release bundle over saved TaskBench, SWE-bench Verified, QASPER, and conversation-bench fixtures, plus one TaskBench-to-conversation transfer check.
- The repo now writes a stable `release_benchmark_report.json` artifact with fixed case ids, bundle version, project version, task-family coverage, and baseline versus cue-disabled versus adapted scores.
- Saved `workspace_profile.json`, `onboarding_benchmark.json`, and `transfer_benchmark.json` artifacts now carry explicit schema-version markers.
- The local workflow now includes a release-version sync check between `pyproject.toml` and the latest released section in `Changelog.md`.
- The repo now has a documented hybrid integration plan: HTTP core service, MCP adapter, and CloudEvents-style event plane.
- The repo now also includes a first implemented local HTTP service slice over a shared local service core.
- That local HTTP slice now also includes explicit `api_version: "v1"` HTTP envelopes, `service_task_state.v1` local task-state files, monotonic `task_version` counters, and clearer structured request errors.
- The local service path now also treats schema-less task-state files as legacy `v1` on load and returns clear compatibility errors for unknown task-state schemas.
- The local HTTP write path now also supports optimistic concurrency through `If-Match` using the current `task_version`, and stale writes now fail with a clear precondition error.
- The local HTTP write path now also supports optional `Idempotency-Key`, so the same retry returns the original result while key reuse for a different write fails clearly.
- The local HTTP write path now also rejects non-object JSON bodies and malformed nested event or expected-item payloads with clear client-facing errors before any task state changes.
- The onboarding and strategy layer now also validates saved workspace profiles, onboarding benchmarks, transfer benchmarks, strategy records, and release benchmark reports on load; schema-less early files are treated as legacy `v1`, while unknown schemas fail clearly.
- The repo now has a concrete release verification gate through `python3 -m memoryvault release-candidate-check`, covering product identity, supported surface, compatibility story, quality-gate presence, benchmark definition, and optional full benchmark execution.
- The repository has now cut `1.0.0` from the exercised `release/0.9.x` line after the release verification gate passed both with and without the full benchmark bundle.
- The released `1.0.0` line makes the current support promise explicit in the README, PRD, and release plan, including the supported local HTTP path, the supported verification commands, and the schema-bearing saved artifacts.
- The release verification gate now also fails if that support promise is not documented consistently or if experimental CLI commands are not marked clearly as non-contractual in CLI help.
- The repo now also has a documented onboarding plan: zero-touch bootstrap, generated starter packs, and evidence-driven refresh.
- Built-in and imported synthetic traces now cover several task shapes, including tool-use dependencies.
- Example imported traces now exist under `examples/interrupted_runs/`.
- `tests/test_pipeline.py` now verifies the local discovery loop and the Hugging Face benchmark registry.
- The CLI can now list built-in scenarios, run the demo loop, run imported trace files, suggest durable fields, run onboarding and transfer benchmarks, summarize strategy runs, print Hugging Face benchmark leads, and start the local HTTP service.
- A local quality gate now exists via `scripts/check_quality.sh` and a configured `.githooks/pre-commit` hook.
- The quality gate now requires passing `ruff`, `mypy`, the repo-local Markdown linter, the release-version sync check, the test suite, and at least 95% Python coverage.
- A live Memgraph service has been verified on host `odin`, exposed on Bolt port `7697`.
- The verified Memgraph target is a shared, already-populated instance rather than an empty database.
- The verified Memgraph target exposes graph algorithms and vector/text search capabilities.
- `.codex/` now exists as the persistent project memory layer for Codex sessions.

## What Does Not Exist Yet

- No project-specific Memgraph namespace or schema bootstrap.
- No Memgraph integration in this repository.
- No live session capture from real agent work.
- No live session capture from real Hugging Face downloads is wired into tests; public-data verification currently uses saved row snapshots plus an optional dataset-viewer fetch path.
- No anchor scoring or compression logic.
- No raw-history / durable-memory split beyond the local JSON artifact store.
- No provenance or confidence model beyond simple heuristic scores and source references.
- No explicit scratchpad lifecycle has been implemented yet.
- No declarative-memory promotion loop from observed misses into durable schema updates.
- No explicit durable memory-class markers yet for source evidence, derived views, and judgments.
- No dual time model yet beyond basic timestamps.
- No benchmark harness over public datasets yet.
- No whole-strategy comparison beyond single-field ablations in the wind tunnel.
- No centralized metrics dashboard or external tracing backend.
- No MCP adapter, shared cache, or event-bus integration is implemented yet.
- No prompt adaptation or provisional graph bootstrapping is implemented yet.

## Current Reality Check

The repository now contains a real local discovery loop, a first strategy-comparison mechanism through the Memory Wind Tunnel, basic local observability, and a broader onboarding loop. It can surface what gets forgotten on resume, which removed fields hurt, whether a learned workspace profile improves held-out traces, whether that learned profile transfers to another task family, and whether tracker-driven profile refresh actually improves the current held-out benchmark before being accepted. It still does not compare full strategies across large public datasets or persist and retrieve work through the target Memgraph architecture.

The intended integration shape is no longer only design work: the repo now has a first local HTTP slice and a shared service core for the narrowest supported resume workflow, plus explicit version markers on both the HTTP envelope and the saved task-state files. That slice now has both stale-write protection through `If-Match` against `task_version` and a first retry-safety story through `Idempotency-Key`. The broader integration model still remains ahead of the implementation: MCP, event handling, caching, and shared multi-agent concerns are still only planned.

The intended onboarding shape is also now clearer than the implementation: automatic workspace bootstrap first, optional YAML starter packs second, and cheap graph bootstrapping only as a provisional knowledge-plane accelerator.

The intended release shape is now also explicit in hindsight: `0.5.0` froze the first product boundary and release benchmark contract, `0.6.x` through `0.8.x` implemented and hardened one supported integration path, `0.9.x` acted as the release-candidate line, and `1.0.0` now ships that supported surface as stable. The chosen `1.0` boundary is a local-first memory-learning workbench, not yet a shared service. The stable line also draws a sharper boundary between the supported promise and still-experimental CLI workflows.

## Suggested Near-Term Focus

1. Keep the released `1.0.0` support promise honest as future work lands, especially around the supported HTTP path, verification commands, and saved-artifact compatibility rules.
2. Keep broadening cue learning and verify which cue categories transfer cleanly across more task families.
3. Extend the wind tunnel from single-field removal to whole-strategy comparison.
4. Define the project workspace boundary and bootstrap plan for the shared Memgraph instance on `odin:7697`.
5. Keep compression and richer retrieval work behind verified multi-benchmark resume wins.
6. Define durable memory-class markers and time semantics before the knowledge-plane schema hardens.
7. Keep preference-conditioned judgment layers out of the control plane unless a future benchmark clearly justifies them.
