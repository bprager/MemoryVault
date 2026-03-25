# Plan

Last updated: 2026-03-24

## Planning Mode

Implementation has now started with a local discovery harness whose job is to reveal what the system forgets on resume. The durable memory schema should be shaped by those observed misses before the Memgraph-backed thin slice is finalized, and the overall tool should begin with near-zero domain knowledge.

The next architecture layer is now defined at the design level: a platform-neutral integration boundary that lets the same memory system serve local agents, remote agents, and multi-agent systems without binding the core logic to one host runtime.

## Goal From First Principles

The tool exists to help an agent stay effective across long-running work while also learning which memory structure actually helps.

That means the highest-priority memory is not "whatever is semantically similar." The highest-priority memory is:

- current objective,
- current plan and step status,
- success criteria,
- constraints and decisions,
- blockers and open questions,
- attempts, outcomes, failures, and lessons,
- authoritative source references.

If these are not preserved, the agent will drift even if it remembers lots of related material.

At design time, assume private real-world traces do not exist. The early learning loop should therefore use:

- synthetic interrupted traces,
- imported public traces and tasks from Hugging Face,
- and repeated-miss analysis over those runs.

## Verified Facts

- The large root design note has been ingested and reviewed.
- The target service on `odin:7697` is Memgraph, not Memcached.
- The Memgraph service is live and explicitly configured with `--bolt-port=7697`.
- The Memgraph instance is already populated with other data and indexes.
- The Memgraph instance exposes graph algorithms and vector/text search procedures.

## Critical Assumption Review

### Assumption: graph memory is the right foundation

- Verdict: mostly sound
- Reason: the problem is relational. Plans, constraints, provenance, failures, code structure, and summaries all depend on traversable relationships.
- Correction: the graph should not become the only storage layer. Large raw payloads may need external file or object storage with graph references.

### Assumption: anchor-based compression should be the first implementation target

- Verdict: too early as a first slice
- Reason: compression only helps after the system can already store and retrieve the right task state.
- Correction: first build explicit task-state persistence and deterministic retrieval, then add compression.

### Assumption: semantic retrieval is enough if it is good enough

- Verdict: false
- Reason: the agent must remember the plan, what succeeded, what failed, and what remains unresolved. This is control state, not just semantic similarity.
- Correction: retrieval must have a deterministic control-plane section before broader semantic expansion.

### Assumption: the target graph is blank or dedicated

- Verdict: false
- Reason: `odin:7697` is a shared Memgraph instance with existing labels and constraints.
- Correction: add strict workspace isolation from day one.

### Assumption: forgetting is broadly desirable

- Verdict: only for low-value periphery
- Reason: forgetting active objectives, accepted decisions, and past failed attempts makes the agent worse.
- Correction: protect objective, plan, constraint, and outcome memory from aggressive compression or decay.

### Assumption: repeated whole-context rewriting is a safe way to maintain memory

- Verdict: false
- Reason: research on context collapse shows that monolithic rewriting can erase useful detail, tactics, and failure patterns.
- Correction: prefer structured incremental updates, especially for procedural guidance and long-lived playbooks.

## Proposed Architecture Shape

### Session, memory, and raw-history split

The architecture should keep three distinct layers:

- `session store`: one conversation's events plus working state
- `memory manager`: extracted declarative and procedural memories
- `raw-history / page store`: exact source history and artifacts for rehydration and deep retrieval

This follows directly from the research intake: sessions are the workbench, long-term memory is the curated filing cabinet, and the raw store remains the backstop when summaries are not enough.

### Integration split

The system should expose three integration layers:

- `canonical service layer`: versioned HTTP and JSON API described with OpenAPI
- `agent adapter layer`: MCP server over the canonical service, using `stdio` locally and Streamable HTTP remotely
- `event layer`: broker-neutral CloudEvents for background work, subscriptions, and cache invalidation

This keeps the core platform-neutral while still making the tool easy for real agents to consume.

### Scratchpad layer

The architecture should also make transient reasoning state explicit:

- `scratchpad`: temporary task-scoped notes, intermediate calculations, draft hypotheses, and other ephemeral reasoning artifacts

Scratchpad artifacts can be promoted into durable memory or archived into raw history after validation, but they should not automatically become durable memory.

### Multi-agent coordination

For shared use, the system should support:

- `tenant_id` and `workspace_id` as hard isolation boundaries
- `agent_id`, `session_id`, and `run_id` as actor and execution boundaries
- optimistic concurrency for mutable task aggregates
- short-lived step leases with heartbeat renewal
- append-only event capture for chronology and auditing

### Caching direction

Caching should use:

- L1 process-local caching for hot read paths
- L2 shared caching for task snapshots and resume packets
- version-based invalidation plus event-driven fan-out
- ETag and `If-Match` style validation for safe re-use and lost-update protection

### Active task package

For each active task, MemoryVault should construct a deterministic control package before wider retrieval. It should contain:

- active objective
- current plan and active step
- success criteria
- blockers and open questions
- constraints and decisions
- recent outcomes and failures
- structured current working state

This package should be present even when broader semantic retrieval is unavailable or heavily budget-constrained.

### 1. Control-plane memory

This is the non-negotiable layer.

Core entities:

- `Workspace`
- `Task`
- `Plan`
- `PlanStep`
- `SuccessCriterion`
- `Decision`
- `Constraint`
- `Attempt`
- `Observation`
- `Outcome`
- `Failure`
- `Lesson`
- `OpenQuestion`
- `SourceRef`

Core rule:

- retrieval always includes the active objective, current step, constraints, open blockers, and latest relevant outcomes before anything else

### 2. Knowledge-plane memory

This is the broader context layer.

Core entities:

- `Repo`
- `File`
- `Chunk`
- `Symbol`
- `Document`
- `Section`
- `Summary`
- `Invariant`
- `Anchor`
- `ContextGroup`
- `Embedding`

Core rule:

- semantic retrieval and graph expansion support the task, but do not override control-plane memory

## New Guidance From Research Intake

### 1. Memory generation should usually be asynchronous

Long-term memory extraction and consolidation should run off the user-facing hot path whenever possible. The user should not wait for durable memory writes before receiving a response.

### 2. JIT retrieval needs a raw backstop

The GAM paper reinforces a useful rule: keep lightweight memory for guidance, but preserve complete raw history somewhere searchable so the system can recover exact detail when needed.

### 3. Provenance and confidence are first-class

Durable memories should retain:

- source type
- freshness
- confidence
- lineage to one or more exact sources

These signals should influence both consolidation and inference.

### 4. Declarative and procedural memories need different lifecycles

Facts about the world or the user are not the same as reusable playbooks. Procedural memory should eventually capture successful workflows and failure-avoidance strategies, but it should not be mixed into the same undifferentiated store as declarative memory.

### 5. Dynamic memory evolution belongs to the knowledge plane

The A-MEM paper suggests useful ideas for note enrichment, linking, and evolution. Those ideas fit the knowledge plane, where richer semantic structure is helpful. They should not silently rewrite explicit task state in the control plane.

### 6. N-ary facts are a future graph extension

Some knowledge cannot be represented cleanly with only binary edges. When that becomes important, MemoryVault should model complex facts through reified fact or hyperedge-style nodes inside the property graph.

### 7. Evaluation must optimize for long-run usefulness

The Huxley-Gödel Machine paper is not a memory architecture paper, but it does reinforce an important evaluation rule: immediate local scores can be a bad proxy for long-run agent effectiveness. MemoryVault should judge memory by downstream task continuity, plan adherence, failure avoidance, and final task success, not only by intrinsic memory metrics.

### 8. Durable declarative memory should use explicit update operations

The Mem0 paper provides a useful practical pattern: candidate memories are extracted incrementally, compared against similar existing memories, and then handled with explicit operations such as add, update, invalidate or delete, and no-op.

### 9. Memory architecture needs a stable interface

The ALMA paper suggests a good abstraction for future evolution: memory systems should present stable `update` and `retrieve` interfaces even if the internals differ. This allows pluggable memory modules now and learned memory design later.

### 10. Efficiency should be measured as a trade-off, not a single score

The efficient-agents survey argues for two complementary views: quality under a fixed cost budget, and cost at a comparable quality level. MemoryVault should adopt that lens in its benchmark harness.

### 11. Retrieval should be goal-conditioned but source-grounded

The self-memory literature adds a useful design test: active goals should shape access to long-term memory, but durable memory should remain linked to evidence and provenance so the agent does not drift into self-confirming continuity.

### 12. Long-horizon control needs explicit goal and state tracking

The StateAct paper reinforces that plan adherence is not just a storage problem. Runtime context should explicitly restate the active goal and current state instead of assuming the model will reliably infer them from a long prompt.

### 13. Procedural memory should grow as curated playbooks

The ACE paper shows the risk of context collapse from monolithic rewriting. MemoryVault should manage procedural memory as incrementally curated playbooks that retain detailed tactics, checks, and failure modes.

## Retrieval Strategy

Use a hybrid strategy:

1. deterministic fetch of control-plane memory
2. explicit goal reminder and current-state header
3. anchor and invariant fetch
4. graph expansion from task, files, symbols, decisions, and recent failures
5. semantic and text retrieval for supporting evidence
6. rehydration of exact raw content only where precision is required

Under token pressure, the last item to drop should be broad semantic detail, not task state or the goal-and-state header.

The main synchronous retrieval surface should be the HTTP API and its MCP adapter. Heavier updates, rebuilds, and cache refreshes should move onto the asynchronous event plane.

Retrieval ranking for durable memories should blend:

- semantic relevance
- recency
- importance
- confidence / provenance quality

For higher-cost retrieval paths, the system should have a clear threshold for when extra reranking, tool use, or graph expansion is justified.

## Algorithm Direction

- memory manager interface: expose `update()` and `retrieve()` at the module boundary
- declarative memory management: prefer explicit add / update / invalidate / noop operations
- task-state retrieval: deterministic graph queries keyed by active task and plan state
- anchor importance: transparent heuristics first, not learned weights
- graph expansion: bounded traversal with task-aware edge priorities
- graph ranking: combine anchor score, task overlap, freshness, evidence support, and graph distance
- graph-native retrieval boost: use Personalized PageRank or similar neighborhood scoring once the baseline works
- summaries: start extractive or hybrid for high-risk memory, not purely abstractive
- failure learning: store explicit reflective outcomes from attempts rather than only free-form summaries
- scratchpad handling: keep transient reasoning artifacts separate from durable memory and promote only validated outcomes
- prompt assembly: always include an explicit goal reminder and structured current-state section for the active task
- procedural playbooks: use structured grow / refine / retire flows instead of repeated whole-playbook rewrites

## Workspace Isolation Strategy

The shared Memgraph target requires:

- a top-level `Workspace` node for MemoryVault
- a `workspace_id` on all MemoryVault-managed nodes
- UUID-based IDs for all records
- queries that always filter by workspace
- no assumption that global labels or indexes belong only to MemoryVault

## Recommended Phase Order

### Phase 0: interrupted-task discovery loop

- record interrupted tasks locally with raw history intact
- accept imported interrupted-task traces through a simple JSON format
- prefer synthetic traces and public Hugging Face tasks until real traces exist
- extract candidate memories without assuming a final schema
- build a deterministic resume packet with an explicit final-goal guard
- score missed memories and log improvement actions
- compare repeated misses across scenarios and domains
- use the observed misses to shape the first durable memory model
- promote fields only after repeated misses justify them
- run a wind tunnel that removes one field at a time and measures the resulting damage
- record lifecycle logs and per-run observability artifacts from the start

### Phase 1: schema and workspace review

- summarize what the tool has learned across synthetic and public benchmark runs
- summarize which wind-tunnel ablations caused the largest damage
- finalize the control-plane schema
- finalize workspace isolation strategy
- finalize scratchpad and session-working-state semantics
- finalize the declarative memory update contract
- finalize the active-task goal-and-state package
- finalize the procedural playbook update pattern
- define success metrics and benchmark cases

### Phase 2: explicit task-state memory

- connect to `odin:7697`
- bootstrap workspace namespace
- define session store semantics for events and working state
- define scratchpad persistence and audit semantics
- persist tasks, plans, plan steps, constraints, attempts, outcomes, failures, and source references
- persist provenance and confidence fields for durable control-plane items
- retrieve the active task package deterministically
- assemble prompts around the deterministic goal-and-state package before wider retrieval

### Phase 3: repo and document ingestion

- ingest docs, code structure, and sections
- preserve raw-history references or page-store references for exact rehydration
- implement declarative memory update operations for extracted durable memories
- link them to tasks, plans, and decisions
- add provenance and exact source references
- start procedural playbook capture for validated tactics and failure-avoidance patterns

### Phase 4: anchors and hybrid retrieval

- compute initial anchor scores
- add graph expansion and semantic support
- preserve exact source rehydration paths

### Phase 5: summaries and incremental compression

- add L1 summaries and invariant extraction
- protect control-plane memory from over-compression
- add loss-risk tracking and drift checks

### Phase 6: benchmark and inspection

- benchmark against sliding window, naive summary, vector-only, and graph-without-compression baselines
- score plan retention, failure recall, constraint preservation, and task continuity
- report quality under fixed budgets and cost at comparable quality levels
- compare memory strategies across synthetic traces and Hugging Face task families before claiming one general solution
- include runtime and stage-cost summaries from the observability layer, not only quality scores

## Non-Negotiable Acceptance Criteria For Phase 1

- The system can run interrupted tasks and keep the final goal explicit in every resume packet.
- The system can accept imported interrupted-task traces without requiring a hard-coded built-in scenario.
- The system can record what the resume packet missed and turn that into concrete improvement actions.
- Repeated misses can be compared across tasks instead of being buried in one-off logs.
- The first durable schema is derived from repeated misses, not only from upfront design guesses.
- The design preserves a clean path from local discovery artifacts to later graph-backed storage.
- Synthetic traces and public Hugging Face datasets can both be adapted into the same interrupted-task evaluation format.
- The wind tunnel can remove individual fields and report which removals cause the largest damage.
- The deterministic resume packet continues to return objective, current plan, constraints, and latest relevant outcomes once the graph-backed store exists.
- The design is isolated safely inside the shared Memgraph instance once storage moves to Memgraph.
- The system can point back to exact supporting sources for any high-value memory item.
