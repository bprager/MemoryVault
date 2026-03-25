# Design

Last updated: 2026-03-24

## Intended System

`MemoryVault` is intended to become a local-first tool for discovering and refining AI memory strategies over long-running work by combining:

- explicit task-state memory,
- goal-conditioned prompt assembly,
- graph-structured memory,
- anchor-based context preservation,
- evolving procedural playbooks,
- layered summaries,
- selective rehydration of detail.

## Current Implemented Slice

The repository now includes a small local discovery harness that:

- records interrupted-task runs as raw local artifacts,
- accepts imported interrupted-task traces from a simple JSON format,
- extracts candidate memory items heuristically from those runs,
- builds a deterministic resume packet,
- keeps the final goal explicit as a goal guard,
- scores what the resume packet missed,
- records improvement actions for the next iteration,
- aggregates repeated misses into candidate durable fields,
- runs a Memory Wind Tunnel that removes fields and measures the damage.
- emits lifecycle logs and writes local observability artifacts with stage timings and summary counts.

This harness is intentionally narrower than the final architecture. Its purpose is to help derive the durable memory model from observed failures before wiring the full graph-backed system.

It should be treated as a tool for memory-strategy learning, not as a finished domain-specific memory product.

## Primary Design Source

The detailed design proposal currently lives in:

- `factory_context_compression_memgraph_design.md`

That document is the main source for the intended architecture until the implementation grows enough to require more detailed repo-local architecture notes.

## Core Concepts From The Existing Design

- Treat task goals, plans, constraints, and outcomes as first-class memory, not as incidental text.
- Preserve high-value "anchor" entities rather than compressing everything equally.
- Represent code, tasks, summaries, and relationships as a graph.
- Compress context incrementally into multiple levels.
- Rehydrate detail on demand for the active task.
- Measure quality with a benchmark harness instead of relying on intuition.

## Planning Direction After Review

The current planning direction is to split memory into two tightly linked planes:

- `control-plane memory`: objective, plan, plan step status, success criteria, blockers, decisions, attempts, failures, and verified outcomes
- `knowledge-plane memory`: code, documents, chunks, summaries, anchors, embeddings, and provenance links

The control plane is the highest-priority memory layer. Retrieval should always preserve it before spending budget on broader semantic context.

The tool should not assume that one domain teaches the right memory model. The early architecture therefore needs to support repeated comparison across synthetic and public task families.

The wind tunnel is the first concrete mechanism for that comparison. It currently performs single-field ablations over the resume packet. Later it should grow into whole-strategy comparison.

The observability layer is intentionally basic for now: standard Python logging plus per-run JSON artifacts. That is enough to support later strategy comparison without requiring external infrastructure yet.

## Goal-Conditioned Retrieval

The design should follow a simple rule from first principles:

- the active goal and current working state should shape what memory is retrieved
- durable memory should remain tied to evidence, provenance, and exact sources

This balances two needs:

- `coherence`: the agent should keep acting like it knows what task it is doing
- `correspondence`: the agent should not invent continuity that is weakly grounded in evidence

## Session And Memory Separation

Research intake reinforced a three-part split:

- `session store`: the hot-path workbench for one conversation, including chronological events and working state
- `memory manager`: the long-term store for extracted and curated memories
- `raw history / page store`: the exact source material used for rehydration and deep retrieval

This split matters because long-term memory should not be treated as the raw session log, and lossy memories need a path back to exact source data.

## Scratchpads And Working State

The architecture should also make temporary reasoning state explicit:

- `scratchpad`: transient, task-scoped intermediate notes, hypotheses, and calculations
- `working state`: the current session-local structured state that drives the next step

Scratchpads may later produce durable memories, but they are not durable memories by default.

## Active Task Package

At runtime, the first context assembled for an active task should be deterministic and explicit. It should contain:

- active objective
- explicit final-goal guard
- current plan and active step
- success criteria
- blockers and open questions
- relevant constraints and decisions
- recent outcomes and failures
- structured current state from the session or environment

Broader semantic retrieval should support this package, not replace it.

## Declarative And Procedural Memory

The design should treat two memory classes differently:

- `declarative memory`: facts, preferences, events, constraints, and summaries about what is true
- `procedural memory`: reusable playbooks about how to perform a task or avoid a failure pattern

Procedural memory is important for self-improvement, but it should not share the same extraction and consolidation logic as declarative memory.

## Procedural Playbooks

The current preferred design for procedural memory is:

- store reusable strategies, checks, templates, and failure-avoidance patterns as playbooks
- grow and refine these playbooks incrementally
- avoid repeated whole-playbook rewrites that can cause context collapse

This keeps useful tactical detail alive without turning procedural guidance into an unstable summary blob.

## Trust And Provenance

Durable memories should carry provenance and confidence signals so the system can:

- resolve conflicts during consolidation
- adjust trust during retrieval and inference
- prune stale or weak memories without losing source lineage

## Knowledge-Plane Evolution

The knowledge plane can eventually support:

- dynamic linking among related memories
- memory evolution as new evidence reshapes older summaries
- n-ary fact representation through reified fact or hyperedge nodes when binary edges are not expressive enough

These are useful future capabilities, but they should not weaken the stability of the control-plane memory.

## Memory Manager Interface

The memory manager should expose a stable high-level interface even if the internals evolve later:

- `update`: ingest new interaction evidence and decide how durable memory changes
- `retrieve`: return the most useful durable memory for the current task

This keeps the current design compatible with future pluggable or learned memory strategies without forcing them into phase 1.

## Declarative Memory Update Pattern

For durable declarative memory, the current preferred pattern is incremental update with explicit operations such as:

- add new memory
- update existing memory with richer or fresher information
- invalidate or delete contradicted memory
- no-op when no durable change is justified

This is a better starting point than unrestricted free-form rewriting of the whole memory base.

## Target Infrastructure

- Primary graph target: Memgraph on host `odin`
- Verified Bolt port: `7697`
- Verified reality: shared, already-populated instance with graph algorithms plus vector and text search support

Because the target is shared, the design must use strict workspace isolation from day one.

## Expected Major Components

- task / plan / outcome state model
- ingestion of code, documents, and task activity
- Memgraph-backed storage and relationships
- anchor scoring and promotion / demotion
- summarization and invariant extraction
- retrieval and prompt assembly
- evaluation and observability

## Current Implementation Gap

The local discovery harness exists, but the graph-backed memory system still does not. The design direction remains ahead of the codebase, though the repo now has a real prototype for interrupted-task evaluation and schema discovery.

## Design Guardrails

- Optimize first for goal retention, plan continuity, and success / failure tracking.
- Start with near-zero domain assumptions and let repeated misses shape the durable schema.
- Keep task state explicit and structured; do not rely on summaries to reconstruct it.
- Keep session state, long-term memory, and raw history as distinct layers with clear roles.
- Keep scratchpad state explicit, transient, and auditable.
- Generate or consolidate long-term memories off the user-facing hot path whenever practical.
- Treat declarative and procedural memory as related but separate subsystems.
- Require provenance and confidence for durable memories that can influence later decisions.
- Prefer bounded, explicit update operations for declarative memory over unrestricted whole-store rewriting.
- Evaluate architectural changes against both task quality and cost, not quality alone.
- Avoid monolithic whole-context rewriting where structured incremental curation is possible.
- Keep runtime context explicit about goal and current state to reduce long-horizon drift.
- Let the active goal shape retrieval, but keep durable memory anchored to evidence and provenance.
- Treat the shared Memgraph instance as a namespace-isolated substrate, not a blank slate.
- Keep the distinction between "planned" and "implemented" explicit.
- Build in thin vertical slices instead of trying to realize the whole design at once.
- Prefer local-first workflows and inspectable state.
- Use synthetic traces and Hugging Face public datasets until real traces exist.
- Use ablation-style evaluation before hardening durable fields that sound important but may not matter in practice.
