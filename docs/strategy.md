# MemoryVault strategy

Last updated: 2026-03-25

## What this project is now

MemoryVault is being developed as a tool, not as a domain-specific product.

The chosen `1.0` boundary is now explicit too: `MemoryVault 1.0` is a local-first memory-learning workbench, not yet a shared production memory service.

The tool starts with almost no domain knowledge. Its job is to observe long-running work, test what gets lost across interruptions, and learn which kinds of memory actually help. It should become more effective over time by comparing strategies, not by assuming the right memory model from the start.

The concrete release path from the current prototype state to `1.0.0` now lives in [docs/release_plan.md](release_plan.md).

## Core stance

- Start with zero domain knowledge.
- Treat every early schema as a hypothesis, not as truth.
- Use simulated tasks or public Hugging Face datasets when real data would otherwise be required.
- Measure what the tool forgets, what it carries forward correctly, and what changes improve outcomes.
- Promote durable memory fields only after repeated evidence across tasks.

## Development phases

### Phase 0: Tool framing

Define the non-negotiable rules of the tool:

- the final goal must always stay visible
- raw history must remain recoverable
- resume packets must be inspectable
- every memory field must justify its existence by improving resumed work

### Phase 1: Synthetic task harness

Build a fully local harness that can:

- generate or load interrupted task traces
- replay them through the same memory loop
- score what was forgotten on resume
- log repeated misses

This phase should use synthetic traces first because they are cheap to create, easy to inspect, and easy to label with expected outcomes.

### Phase 2: Public benchmark adapters

Add adapters for public Hugging Face datasets so the tool can be tested beyond hand-made examples.

Good early benchmark groups:

- long-memory conversations
- tool-use plans and execution traces
- code issue resolution and agent trajectories
- long-form document question answering with evidence

The point is not to specialize in those domains. The point is to see which memory behaviors survive across very different task shapes.

### Phase 2.5: Onboarding and priming

Before the durable schema hardens, add a zero-touch onboarding cycle that can:

- sample representative sources
- infer a first workspace profile
- generate an optional starter pack
- adapt extraction prompts
- run a cheap first-pass knowledge bootstrap
- test the result on held-out onboarding tasks

The detailed design now lives in [docs/onboarding_strategy.md](onboarding_strategy.md).

The first concrete implementation of this phase now exists too. The repo can build a generated workspace profile from representative JSON traces or adapted public dataset rows, emit an optional starter pack, and test that profile on held-out traces before trusting it.

That implemented slice now also records a version for each learned profile, stores short improvement notes, can test transfer from one task family to another, can summarize recurring wins, recurring gaps, cost patterns, profile history, and cue-transfer results across runs, and can run a benchmark-gated refresh loop that proposes a next profile from prior successful evidence, including learned cue phrases for free-form notes.

### Phase 3: Memory field discovery

Use repeated misses to propose candidate durable fields.

Examples:

- hidden assumptions
- recent failed attempts
- unresolved open questions
- decision rationale
- source confidence

Only fields that repeatedly matter should graduate into the core memory model.

### Phase 4: Strategy comparison

Once the tool can run the same tasks with different memory strategies, compare them.

Examples:

- no memory vs goal-only memory
- resume packet only vs resume packet plus evidence
- hand-written extraction rules vs learned extraction rules
- short memory budget vs larger memory budget

The tool should keep a record of which strategy works better, on which task types, and at what cost.

```plantuml
@startuml
title Strategy Comparison Loop

start
:Pick one interrupted task;
:Run baseline memory strategy;
:Run alternative memory strategy;
:Compare resume quality and cost;
if (repeat across tasks?) then (yes)
  :Aggregate results by task family;
else (no)
endif
:Promote or reject memory strategy;
stop
@enduml
```

The first concrete implementation of this phase now exists in two forms:

- the Memory Wind Tunnel in [docs/wind_tunnel.md](wind_tunnel.md), which removes one memory field at a time and measures the damage
- the new strategy tracker and transfer benchmark, which record learned profile runs and test whether a profile helps on another task family

### Phase 5: Durable storage and retrieval

After the tool has enough evidence about useful memory fields, move from the local artifact store to durable structured storage.

At that point, Memgraph can become the long-term store for:

- durable memory fields
- relationships among tasks, failures, decisions, and sources
- retrieval paths for resuming work

The graph should come after field discovery, not before it.

### Phase 6: Platform-neutral integration

Once the memory fields and retrieval bundles are clearer, expose the system through one shared integration shape:

- a versioned HTTP core service
- an MCP adapter for agents
- an asynchronous event plane for background work and cache invalidation

The detailed design now lives in [docs/integration_strategy.md](integration_strategy.md).

### Phase 7: Learning how to become effective

In the later phase, the tool should do more than remember. It should learn which memory policies make it better.

That now means:

- tracking which fields helped
- tracking which retrieval bundles were sufficient
- tracking which summaries caused harm
- tracking which strategies reduced repeated failure

The first thin implementation of that later phase is now in place:

- one strategy record per onboarding or transfer run
- one short set of improvement notes per run
- one offline transfer benchmark over saved synthetic or public-data-shaped fixtures
- one cross-run summary that rolls up category wins and gaps, task-family impact, basic cost signals, profile history, and workspace lineages
- one explicit refresh loop that turns those rollups into a candidate next profile and keeps it only when the held-out benchmark improves

The end state is a memory tool that improves by observing its own successes and misses.

### Cross-cutting requirement: observability

Every phase should stay observable.

That means:

- lifecycle logs for runs and wind tunnels
- per-run timing artifacts
- enough summary data to compare strategy cost and damage later

This is now started in [docs/observability.md](observability.md), but it should grow as the strategy-comparison layer grows.

## Data policy

At design time, do not assume access to real production traces.

Use two sources instead:

1. Synthetic traces created to expose known failure modes.
2. Public Hugging Face datasets that can be turned into interrupted-task evaluations.

This keeps the tool honest. It also avoids shaping the architecture around one narrow workflow too early.

## Immediate next phases

1. Implement one supported integration path in the `0.6.x` line.
2. Harden compatibility and release reporting in the `0.7.x` to `0.8.x` line.
3. Use `0.9.x` as a real release-candidate line rather than another normal minor release.
4. Keep expanding the learned cue set and measuring which gains transfer.
5. Compare whole memory strategies, not only single-field removals.
6. Promote only the next few high-value fields, not a large schema all at once.
