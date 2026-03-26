# MemoryVault

![MemoryVault repository hero image showing a visual concept for long-running AI memory and continuity](.github/assets/memoryvault-repo-hero.jpg)

![Status](https://img.shields.io/badge/status-product_candidate-2d6cdf)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-2ea44f)
![Store](https://img.shields.io/badge/store-Memgraph-0b7285)
![Coverage](https://img.shields.io/badge/coverage-92%25-2ea44f)

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

`MemoryVault 1.0` is being defined as a local-first memory-learning workbench.

The `0.5.0` release makes that boundary explicit. It focuses on the local learning workflow, repeatable benchmark reporting, and saved artifact compatibility. It is not yet a shared memory service.

Today the workbench can:

Today it can:

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
- list Hugging Face benchmark leads for later evaluation
- verify that the project version and latest changelog release stay in sync

It does not yet connect to Memgraph or learn from live production traces.
It also does not yet implement the planned HTTP or MCP integration path for the later `0.6.x` line.
The concrete path from the current `0.5.x` line to a stable `1.0.0` is documented in [docs/release_plan.md](docs/release_plan.md).

## What `1.0` means

For `1.0`, MemoryVault is for:

- learning which memory fields, cues, and retrieval bundles help an agent resume long-running work
- comparing those strategies across saved synthetic and public-data task families
- producing stable local artifacts and release benchmark reports that can be compared over time

For `1.0`, MemoryVault is not yet:

- a shared production memory service
- a shipped HTTP or MCP integration surface
- a live production-trace capture system
- a Memgraph-backed deployment

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
python3 -m memoryvault suggest-fields --threshold 1
python3 -m memoryvault list-public-data
python3 scripts/check_version_sync.py
./scripts/check_quality.sh
```

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
