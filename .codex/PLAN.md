# Plan

Last updated: 2026-04-01

## Planning Mode

Implementation has now started with a local discovery harness whose job is to reveal what the system forgets on resume. The durable memory schema should be shaped by those observed misses before the Memgraph-backed thin slice is finalized, and the overall tool should begin with near-zero domain knowledge.

The next architecture layer is now defined at the design level: a platform-neutral integration boundary that lets the same memory system serve local agents, remote agents, and multi-agent systems without binding the core logic to one host runtime.

The next product-learning layer is also now defined at the design level: a zero-touch onboarding cycle that gets a new workspace to a first useful state quickly and then keeps improving it through evidence.

That onboarding layer now has a first implemented slice: representative JSON traces or adapted Hugging Face rows can be sampled automatically, turned into a generated workspace profile and starter pack, and tested on held-out traces before the profile is trusted.

Another research-driven addition now matters for the next stage: the tool should learn reusable memory behavior, not only per-dataset tricks. That means explicit performance tracking over strategy variants and transfer checks where a profile learned on one task family is tested on another.

That strategy-learning addition now also has a first implemented slice: learned profiles now get content-based versions, onboarding and transfer runs now write strategy records plus short improvement notes, the CLI can test one task family against another using saved public-data fixtures, the tracker can now roll those runs up into category, cost, lineage, and cue-transfer summaries, and a refresh loop can now turn that evidence into a benchmark-gated candidate next profile with carried-forward cue phrases for free-form notes.

The release path is now explicit too:

- `0.5.x`: freeze the `1.0` product identity and the release benchmark contract
- `0.6.x` to `0.8.x`: implement and harden one supported integration path plus artifact compatibility
- `0.9.x`: operate as a release-candidate line
- `1.0.0`: ship only when docs, benchmark, integration path, and compatibility promises all agree

The first implemented slice of that `0.5.x` release work now exists too:

- one fixed offline public benchmark bundle
- one stable `release_benchmark_report.json` artifact
- one narrow compatibility rule based on explicit artifact schema markers plus content-based profile versions
- one explicit `1.0` product identity: a local-first memory-learning workbench

That `0.6.0` milestone now also has a first implemented slice:

- one thin local HTTP service as the first supported integration path
- one intentionally narrow first contract:
  - append events
  - update task state
  - get a deterministic resume packet
  - retrieve the control-plane memory view
- one shared service-layer core so the CLI and HTTP path do not fork behavior

The next hardening work should therefore focus on maintaining the stable support promise, remaining benchmark confidence, and schema decisions rather than on inventing a different first integration surface. The repo has now cut `1.0.0` from the exercised `release/0.9.x` line, and the first compatibility floor is in place for local task state plus the saved profile, benchmark, strategy, and release-report artifacts. MCP, CloudEvents, Memgraph wiring, and shared multi-agent concerns remain later work.

The latest release-management rule remains explicit after the stable cut: the repo must state which surfaces are part of the `1.0` support promise and which remain experimental. That support promise centers on the four-endpoint local HTTP path, the release verification commands, and the schema-bearing saved artifacts. Sample, demo, and public-data helper commands remain useful, but they are not part of the stable `1.0` contract and should stay marked as experimental until the project deliberately promotes them.

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

### Onboarding split

The onboarding layer should also be explicit:

- `automatic bootstrap`: sample representative sources, infer domain hints, and generate a first workspace profile
- `optional starter pack`: YAML hints for source priority, candidate types, retrieval policy, and benchmark profiles
- `provisional knowledge bootstrap`: cheap graph extraction and prompt adaptation for the knowledge plane
- `benchmark gate`: held-out onboarding checks before promoted defaults are trusted
- `refresh loop`: revise the workspace profile from misses, drift, and changed source material

This keeps manual setup optional while preserving a place for user hints when they help.

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

### Onboarding direction

The fastest path to usefulness is not a mandatory ontology.

The preferred path is:

- fixed control-plane structure
- generated starter packs as soft hints
- representative-sample adaptation
- cheap first-pass graph bootstrapping
- measured promotion from onboarding benchmarks and later task misses

The current implemented version of that direction is intentionally narrow:

- onboarding derives a workspace profile from representative traces
- the generated starter pack is written as YAML
- the held-out benchmark currently tests two learned adaptations:
  - failure-marker expansion for `recent_failures`
  - event-label alias learning for non-default markers such as `Focus`, `Evidence`, and `Guardrail`

This is enough to validate the onboarding loop itself without pretending the full adaptation plan is already built.

### Strategy-learning direction

The next evaluation layer should make memory learning cumulative and comparable:

- `strategy tracker`: record quality, cost, task family, profile version, and run lineage over time
- `improvement insight store`: keep timestamped summaries of what likely helped, what regressed, and what should be tried next
- `transfer gate`: test whether a learned workspace profile or memory policy helps on a different task family
- `variant archive`: keep comparable strategy variants instead of mutating only the latest profile in place

This is the useful part of the `HyperAgents` paper for MemoryVault: not self-modifying agents, but evidence that persistent memory plus performance tracking can become reusable improvement machinery across domains.

The currently implemented slice of that direction is still intentionally simple:

- one strategy record per onboarding or transfer run
- one small set of timestamped improvement notes per run
- one transfer gate that compares baseline and adapted scoring on a different task family
- one CLI summary that rolls up recurring wins and gaps, task-family impact, cost patterns, profile summaries, and workspace lineages
- one refresh loop that carries forward prior successful aliases, failure markers, cue phrases, source priorities, and starter-pack hints, but only accepts the candidate profile when the current held-out benchmark improves

This is enough to start measuring reuse without pretending that the repo already has a full policy archive, evolutionary search loop, or large-scale cross-benchmark strategy harness.

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
- durable knowledge-plane items should declare whether they are source evidence, derived views, or judgment-like records so retrieval can keep those roles distinct

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

### 14. Onboarding should prefer auto adaptation over manual tuning

The current GraphRAG documentation is useful here: auto prompt tuning is encouraged, manual tuning is advanced, and fast indexing is a cheaper but noisier option.

That suggests a practical onboarding rule for MemoryVault:

- automatic adaptation first
- optional soft hints second
- manual ontology work only when the workspace truly needs it

### 15. Evidence, derived views, and judgments need separate lanes

The Hindsight paper reinforces a design rule that fits MemoryVault well: source evidence, synthesized summaries, and any subjective judgments should not be stored as if they were the same kind of memory. Derived views are useful, but they should not silently replace what the system actually observed.

### 16. Time needs occurrence and record semantics

When possible, durable memory should track both when something happened and when MemoryVault recorded or updated it. That distinction matters for historical retrieval, freshness, and conflict review.

### 17. The knowledge plane should grow toward fused retrieval

For the knowledge plane, the future retrieval target should blend lexical, semantic, graph, and temporal signals, then spend reranking cost only when the task justifies it.

## Retrieval Strategy

Use a hybrid strategy:

1. deterministic fetch of control-plane memory
2. explicit goal reminder and current-state header
3. anchor and invariant fetch
4. graph expansion from task, files, symbols, decisions, and recent failures
5. semantic, text, and temporal retrieval for supporting evidence
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
- memory classes: mark durable knowledge-plane items as evidence, derived view, or judgment and keep their update rules separate
- task-state retrieval: deterministic graph queries keyed by active task and plan state
- anchor importance: transparent heuristics first, not learned weights
- graph expansion: bounded traversal with task-aware edge priorities
- time semantics: carry occurrence and recorded or updated time where the source allows it
- graph ranking: combine anchor score, task overlap, freshness, evidence support, and graph distance
- graph-native retrieval boost: use Personalized PageRank or similar neighborhood scoring once the baseline works
- future retrieval fusion: combine lexical, semantic, graph, and temporal candidates before optional reranking on the knowledge plane
- summaries: start extractive or hybrid for high-risk memory, not purely abstractive
- derived views: regenerate summaries or profiles asynchronously from evidence changes instead of hand-editing them as primary truth
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
