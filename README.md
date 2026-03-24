# MemoryVault

![Status](https://img.shields.io/badge/status-planning-2d6cdf)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-2ea44f)
![Store](https://img.shields.io/badge/store-Memgraph-0b7285)

MemoryVault is a local-first memory layer for long-running AI work.

It is being designed to keep hold of the parts agents lose most often: the goal, the plan, the constraints, prior attempts, and the source material behind them.

The project starts from a simple rule: keep task state stable first. Broader retrieval and compression come after that.

## What it keeps

- active tasks, plan steps, blockers, decisions, outcomes, and lessons
- code and document structure with links back to source
- raw history, durable memory, and scratch work as separate layers

## Status

MemoryVault is still in planning. The repo currently contains the product brief, research summary, and design notes. The implementation is still minimal.

## Read next

- [Product brief](docs/PRD.md)
- [Research summary](docs/research.md)
- [Design note](factory_context_compression_memgraph_design.md)
