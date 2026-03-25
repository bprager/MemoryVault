# MemoryVault

![Status](https://img.shields.io/badge/status-discovery_prototype-2d6cdf)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-2ea44f)
![Store](https://img.shields.io/badge/store-Memgraph-0b7285)

MemoryVault is a local-first tool for learning how an AI system should remember long-running work.

It starts with very little domain knowledge. The goal is to observe interrupted work, test what gets lost, and refine memory strategy over time.

The project starts from a simple rule: keep task state stable first, and let the memory model earn its shape from repeated evidence.

## What it does

- records interrupted tasks
- rebuilds a short resume package
- scores what the system forgot
- promotes stable memory fields only after repeated misses
- uses synthetic traces and public Hugging Face data until real traces exist

## Status

MemoryVault now has an early local discovery prototype.

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
- list Hugging Face benchmark leads for later evaluation
- verify that the project version and latest changelog release stay in sync

It does not yet connect to Memgraph or learn from live production traces.
It also does not yet implement the planned shared-service or MCP integration design.

## Try it

```bash
python3 -m memoryvault list-scenarios
python3 -m memoryvault demo
python3 -m memoryvault run-file examples/interrupted_runs/swe_bench_like_bugfix.json
python3 -m memoryvault run-file examples/interrupted_runs/taskbench_like_tool_chain.json
python3 -m memoryvault --log-level INFO --log-file /tmp/memoryvault.log run-file examples/interrupted_runs/taskbench_like_tool_chain.json
python3 -m memoryvault wind-tunnel-file examples/interrupted_runs/taskbench_like_tool_chain.json
python3 -m memoryvault suggest-fields --threshold 1
python3 -m memoryvault list-public-data
python3 scripts/check_version_sync.py
./scripts/check_quality.sh
```

## Read next

- [Tool brief](docs/PRD.md)
- [Strategy](docs/strategy.md)
- [Integration strategy](docs/integration_strategy.md)
- [Memory Wind Tunnel](docs/wind_tunnel.md)
- [Logging And Observability](docs/observability.md)
- [Research summary](docs/research.md)
- [Design note](factory_context_compression_memgraph_design.md)
