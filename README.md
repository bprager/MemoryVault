# MemoryVault

![MemoryVault repository hero image showing a visual concept for long-running AI memory and continuity](.github/assets/memoryvault-repo-hero.jpg)

![Status](https://img.shields.io/badge/status-stable_1.0.0-2d6cdf)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-2ea44f)
![Store](https://img.shields.io/badge/store-Memgraph-0b7285)
![Coverage](https://img.shields.io/badge/coverage-95%25-2ea44f)

MemoryVault is a local-first memory-learning workbench for long-running AI work.

It starts with very little domain knowledge. The goal is to observe interrupted work, test what gets lost, and refine memory strategy over time.

The project starts from a simple rule: keep task state stable first, and let the memory model earn its shape from repeated evidence.

## What it does

- records interrupted tasks
- rebuilds a short resume package
- scores what the system forgot
- promotes stable memory fields only after repeated misses
- uses synthetic traces and public Hugging Face data until real traces exist

## Status

`MemoryVault 1.0` is now the released stable boundary for a local-first memory-learning workbench.

The `0.5.0` release made that boundary explicit. It focused on the local learning workflow, repeatable benchmark reporting, and saved artifact compatibility. It is not a shared memory service.

The released `1.0.0` line includes the supported local HTTP path for the core resume workflow.

The released `1.0.0` line also keeps one concrete release verification command:

- `python3 -m memoryvault release-candidate-check`

Today the workbench can:

- run interrupted-task scenarios
- run imported interrupted-task traces from JSON files
- store raw run history locally
- extract candidate memories without freezing a final schema up front
- build a resume packet with an explicit goal guard
- run a Memory Wind Tunnel that removes memory fields and measures the damage
- keep assumptions as a first promoted durable field after repeated misses
- log run lifecycle events through Python logging
- write per-run observability artifacts with timings and counts
- score what the system forgot and log improvement targets
- suggest new durable fields from repeated misses
- build a zero-touch workspace profile from representative traces
- generate an optional starter pack in YAML
- run an onboarding benchmark gate against held-out traces
- learn extra event-label patterns such as `Focus`, `Evidence`, and `Guardrail`
- learn free-form content cues such as `according to`, `stay within the`, and `waiting on the` so unlabeled notes still preserve sources and control state
- broaden those free-form cues to cover current focus, decisions, lessons, and open questions as well as sources, constraints, and blockers
- adapt saved Hugging Face dataset rows into the same onboarding gate
  Current adapters cover TaskBench, SWE-bench Verified, QASPER, and conversation-bench style rows.
- assign a stable version to each learned workspace profile
- record strategy runs with profile version, task-family, quality, and timing data
- store short dated improvement notes about what helped, what still fails, and what to try next
- run an offline transfer benchmark to see whether a learned profile helps on a different task family
- run a refresh loop that proposes a next profile from prior successful evidence, including learned content cues, and only keeps it if the held-out benchmark improves
- summarize recurring wins and gaps, task-family impact, cost patterns, and profile history from the CLI
- summarize which cue categories actually helped, how much they helped, and which task families they transferred to
- run a fixed offline release benchmark bundle and write one stable release report artifact
- run a first local HTTP service for task-state updates, event appends, resume-packet reads, and control-plane retrieval
- list Hugging Face benchmark leads for later evaluation
- verify that the project version and latest changelog release stay in sync

It does not yet connect to Memgraph or learn from live production traces.
It also does not yet implement the planned MCP adapter, shared deployment path, or event-driven integration layer.
The concrete path from the current `0.5.x` line to a stable `1.0.0` is documented in [docs/release_plan.md](docs/release_plan.md).

## What `1.0` means

For `1.0`, MemoryVault is for:

- learning which memory fields, cues, and retrieval bundles help an agent resume long-running work
- comparing those strategies across saved synthetic and public-data task families
- producing stable local artifacts and release benchmark reports that can be compared over time

For `1.0`, MemoryVault is not yet:

- a shared production memory service
- a shared HTTP or MCP platform surface for outside users to build against without change risk
- a live production-trace capture system
- a Memgraph-backed deployment

## Current `1.0` support promise

For the released `1.0.0` line, the repo treats these as the stable contractual surface:

- the local HTTP path with these four endpoints:
  - `POST /v1/events`
  - `PUT /v1/tasks/{task_id}/state`
  - `GET /v1/tasks/{task_id}/resume-packet`
  - `POST /v1/tasks/{task_id}/retrieve`
- the release verification commands:
  - `python3 -m memoryvault release-benchmark`
  - `python3 -m memoryvault release-candidate-check`
- the core saved artifacts:
  - `workspace_profile.json`
  - `onboarding_benchmark.json`
  - `transfer_benchmark.json`
  - `strategy_record.json`
  - `release_benchmark_report.json`
  - local task-state files using `service_task_state.v1`

Version upgrade expectations for that supported surface are:

- additive fields are allowed within a schema version
- breaking shape or meaning changes require a new schema version
- a new schema version also requires either a documented migration path or an explicit break notice in the release notes

## Experimental And Non-Contractual

The following commands are still allowed to change on the stable line and should not be treated as stable `1.0` contracts:

- built-in sample and demo commands such as `list-scenarios`, `run-scenario`, `demo`, and `wind-tunnel-scenario`
- public-data discovery commands such as `list-public-data` and `list-hf-adapters`
- Hugging Face adapter workflow commands such as `onboard-hf-file`, `refresh-hf-file`, `onboard-hf-first-rows`, and `transfer-hf-files`

Those commands remain useful for exercising the workbench, but the stable `1.0` promise is centered on the local HTTP path, the core saved artifacts, and the release-verification commands above.

## Try it

```bash
python3 -m memoryvault list-scenarios
python3 -m memoryvault demo
python3 -m memoryvault run-file examples/interrupted_runs/swe_bench_like_bugfix.json
python3 -m memoryvault run-file examples/interrupted_runs/taskbench_like_tool_chain.json
python3 -m memoryvault --log-level INFO --log-file /tmp/memoryvault.log run-file examples/interrupted_runs/taskbench_like_tool_chain.json
python3 -m memoryvault wind-tunnel-file examples/interrupted_runs/taskbench_like_tool_chain.json
python3 -m memoryvault onboard-directory examples/onboarding
python3 -m memoryvault refresh-directory examples/onboarding --workspace-id demo_workspace
python3 -m memoryvault list-hf-adapters
python3 -m memoryvault onboard-hf-file hf_taskbench examples/huggingface_rows/taskbench_first_rows.json
python3 -m memoryvault refresh-hf-file hf_taskbench examples/huggingface_rows/taskbench_first_rows.json --workspace-id demo_workspace
python3 -m memoryvault transfer-hf-files hf_taskbench examples/huggingface_rows/taskbench_first_rows.json hf_conversation_bench examples/huggingface_rows/conversation_bench_first_rows.json
python3 -m memoryvault summarize-strategies
python3 -m memoryvault release-benchmark
python3 -m memoryvault release-candidate-check --skip-benchmark
python3 -m memoryvault serve-http --host 127.0.0.1 --port 8765
python3 -m memoryvault suggest-fields --threshold 1
python3 -m memoryvault list-public-data
python3 scripts/check_version_sync.py
python3 scripts/check_release_candidate.py --skip-benchmark
./scripts/check_quality.sh
```

## Local HTTP path

The first local HTTP slice is intentionally small. It supports four endpoints:

- `POST /v1/events`
- `PUT /v1/tasks/{task_id}/state`
- `GET /v1/tasks/{task_id}/resume-packet`
- `POST /v1/tasks/{task_id}/retrieve`

The contract now includes explicit version markers:

- HTTP request and response envelopes use `api_version: "v1"`
- saved local task-state files use `artifact_schema_version: "service_task_state.v1"`

Each saved task also carries a `task_version` counter that increases whenever task state or task events change.

Run it locally:

```bash
python3 -m memoryvault serve-http --host 127.0.0.1 --port 8765
```

Set up a task:

```bash
curl -X PUT http://127.0.0.1:8765/v1/tasks/demo-task/state \
  -H 'Content-Type: application/json' \
  -d '{
    "api_version": "v1",
    "title": "Fix the checkout bug",
    "domain": "coding",
    "goal": "Ship the checkout fix without breaking coupon totals.",
    "interruption_point": "Paused after reproducing the failure."
  }'
```

Append events:

```bash
curl -X POST http://127.0.0.1:8765/v1/events \
  -H 'Content-Type: application/json' \
  -d '{
    "api_version": "v1",
    "task_id": "demo-task",
    "events": [
      {"sequence": 1, "actor": "assistant", "text": "Goal: Ship the checkout fix without breaking coupon totals."},
      {"sequence": 2, "actor": "assistant", "text": "Next step: Re-run the failing checkout test."},
      {"sequence": 3, "actor": "assistant", "text": "Constraint: Do not change the shipping calculator."}
    ]
  }'
```

Read the resume packet:

```bash
curl http://127.0.0.1:8765/v1/tasks/demo-task/resume-packet
```

Responses now return a stable envelope:

```json
{
  "ok": true,
  "api_version": "v1",
  "endpoint": "/v1/tasks/demo-task/resume-packet",
  "data": {
    "scenario_id": "demo-task",
    "final_goal_guard": "Ship the checkout fix without breaking coupon totals."
  }
}
```

## Release verification gate

The current stable line keeps one concrete repo-local verification gate:

- `python3 -m memoryvault release-candidate-check`

That check verifies:

- the README, PRD, and release plan all still describe the same `1.0` identity
- the supported local HTTP surface is still the documented public path
- the saved-artifact compatibility story is both documented and backed by loaders
- the normal quality gate still covers linting, typing, tests, markdown, version sync, and coverage
- the fixed release benchmark bundle is still defined correctly

Add `--skip-benchmark` if you only want the static gate checks without executing the full release benchmark bundle.

## Read next

- [Tool brief](docs/PRD.md)
- [Strategy](docs/strategy.md)
- [Onboarding, Priming, And Learning](docs/onboarding_strategy.md)
- [Release Plan](docs/release_plan.md)
- [Integration strategy](docs/integration_strategy.md)
- [Memory Wind Tunnel](docs/wind_tunnel.md)
- [Logging And Observability](docs/observability.md)
- [Research summary](docs/research.md)
- [Design note](factory_context_compression_memgraph_design.md)
