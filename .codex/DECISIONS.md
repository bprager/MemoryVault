# Decisions

Last updated: 2026-03-24

## Active Decisions

### 2026-03-24: Add a repo-local `.codex` workspace

- Status: active
- Decision: store persistent agent-facing project memory in `.codex/`.
- Why: it creates a durable place for status, decisions, lessons, and operating instructions across Codex sessions.

### 2026-03-24: Use `AGENTS.md` to enforce `.codex` usage

- Status: active
- Decision: add a root `AGENTS.md` that instructs future Codex sessions to read and maintain `.codex/`.
- Why: creating the files alone is not enough; the repo needs a stable entry point that makes the workflow repeatable.

### 2026-03-24: Treat the large root design note as a design reference, not implementation evidence

- Status: active
- Decision: use `factory_context_compression_memgraph_design.md` as the current architecture reference while keeping repo status documents honest about the implementation gap.
- Why: the repo already contains substantial design thinking, but the shipped code is still only a bootstrap.

### 2026-03-24: Stay in planning mode before implementation

- Status: active
- Decision: do planning review, external research, and assumption checks before starting major implementation.
- Why: the architecture is ambitious and the target graph environment is shared, so bad early assumptions would be expensive.

### 2026-03-24: Use the verified Memgraph service on `odin:7697`

- Status: active
- Decision: plan around the live Memgraph service on host `odin` using Bolt port `7697`.
- Why: the endpoint has been verified directly from the running infrastructure instead of assumed from defaults.

### 2026-03-24: Treat `odin:7697` as a shared graph substrate

- Status: active
- Decision: design MemoryVault around strict workspace isolation rather than assuming a dedicated empty database.
- Why: the live Memgraph instance already contains other labels, indexes, constraints, and data.

### 2026-03-24: Make task, plan, and outcome memory the highest-priority memory class

- Status: active
- Decision: preserve active objective, plan, success criteria, blockers, and success / failure history ahead of generic semantic recall.
- Why: an agent that forgets its plan or repeats failed actions is not effective even if it remembers semantically related facts.

### 2026-03-24: Separate session state from long-term memory and raw history

- Status: active
- Decision: treat the session store, long-term memory manager, and raw-history or page-store as distinct layers.
- Why: the research intake consistently reinforced that raw conversation, extracted memories, and exact rehydration sources serve different purposes and should not be collapsed into one store.

### 2026-03-24: Require provenance and confidence for durable memories

- Status: active
- Decision: durable memories should carry source lineage and confidence information.
- Why: later consolidation, pruning, and inference all depend on knowing where a memory came from and how trustworthy it is.

### 2026-03-24: Keep declarative and procedural memory on separate lifecycles

- Status: active
- Decision: facts and preferences should not share the same extraction and consolidation loop as playbooks and workflow knowledge.
- Why: procedural memory is a reasoning-augmentation problem, not just a factual retrieval problem.

### 2026-03-24: Add explicit scratchpad handling to the architecture

- Status: active
- Decision: represent temporary reasoning artifacts as a distinct scratchpad or working-state layer instead of treating them as durable memory by default.
- Why: intermediate reasoning needs to stay inspectable and auditable without polluting the durable memory base.

### 2026-03-24: Use explicit update operations for declarative durable memory

- Status: active
- Decision: manage durable declarative memory with bounded operations such as add, update, invalidate or delete, and no-op.
- Why: this is a pragmatic and auditable foundation for memory maintenance before more adaptive methods are introduced.

### 2026-03-24: Design memory modules around update and retrieve interfaces

- Status: active
- Decision: keep the memory manager boundary simple and stable with high-level `update` and `retrieve` interfaces.
- Why: it supports pluggable internals now and leaves room for learned memory designs later.

### 2026-03-24: Evaluate memory with cost-quality trade-offs

- Status: active
- Decision: measure MemoryVault by both quality under fixed budget and cost at comparable quality.
- Why: a memory system that improves quality only by exploding token, latency, or tool cost is not production-ready.

### 2026-03-24: Keep a durable human-readable research summary in `docs/research.md`

- Status: active
- Decision: maintain `docs/research.md` as the long-form research synthesis while keeping `.codex/RESEARCH.md` concise.
- Why: the design now depends on a growing set of papers, and future sessions need one readable place that preserves links, quotes, and project-level lessons.

### 2026-03-24: Keep a human-readable tool brief in `docs/PRD.md`

- Status: active
- Decision: maintain `docs/PRD.md` as the plain-language statement of MemoryVault's purpose, scope, and success criteria.
- Why: the repository needs one short, durable reference for what the tool is for before implementation details spread further.

### 2026-03-24: Keep a root changelog in `Chaneglog.md`

- Status: active
- Decision: maintain a root `Chaneglog.md` file for notable project changes using the Keep a Changelog structure.
- Why: the repo now needs one obvious chronological record of meaningful changes outside the more task-oriented `.codex` notes.

### 2026-03-24: Balance goal coherence with source correspondence

- Status: active
- Decision: let the active goal shape retrieval, but require durable memory to stay linked to evidence, provenance, and exact sources.
- Why: a goal-driven memory system is useful, but without correspondence guardrails it can drift into self-confirming narratives.

### 2026-03-24: Include an explicit goal-and-state header in active task context

- Status: active
- Decision: the runtime task package should always restate the active objective and include a structured current-state section before broader semantic context.
- Why: long-horizon agents drift when the goal and state are left implicit inside a large context.

### 2026-03-24: Maintain procedural guidance as evolving playbooks

- Status: active
- Decision: reusable strategies, checks, and failure-avoidance patterns should be curated incrementally as playbooks rather than rewritten wholesale each cycle.
- Why: structured growth is more stable than monolithic context rewriting and better preserves useful detail over time.

### 2026-03-24: Derive the first durable memory model from interrupted-task misses

- Status: active
- Decision: start implementation with a local interrupted-task discovery loop instead of freezing the durable memory schema upfront.
- Why: the project does not yet know the exact minimum memory bundle, and repeated misses on resume are a better guide than abstract schema guesses.

### 2026-03-24: Keep the final goal explicit in every resume packet

- Status: active
- Decision: every resume packet should carry a run-level goal guard that restates the final goal even before the rest of the memory model is mature.
- Why: losing the final goal is a catastrophic failure mode for long-running work, so goal visibility should not depend on later retrieval quality.

### 2026-03-24: Start the first implementation with a local artifact store

- Status: active
- Decision: begin with inspectable local JSON artifacts for interrupted-task runs before moving the discovery loop to Memgraph.
- Why: it reduces startup complexity, keeps failures easy to inspect, and lets the durable schema emerge before graph persistence hardens the shape too early.

### 2026-03-24: Use a simple JSON trace format for early real-task intake

- Status: active
- Decision: accept interrupted-task traces through a plain JSON file format that matches the built-in scenario shape.
- Why: it lets real and simulated tasks flow through the same harness immediately, without waiting for a live session-capture system.

### 2026-03-24: Promote assumptions into the first durable resume fields

- Status: active
- Decision: add `assumptions` to the resume packet after repeated misses showed that hidden assumptions were consistently lost.
- Why: the first promotion should come from observed failures, and assumptions were the clearest repeated gap in the initial runs.

### 2026-03-24: Treat MemoryVault as a tool-first project, not a domain-specific product

- Status: active
- Decision: frame MemoryVault as a tool for learning effective memory strategies rather than as a product optimized around one domain from the start.
- Why: the project should discover which memory fields and strategies generalize, not bake in narrow assumptions before enough evidence exists.

### 2026-03-24: Assume no private real data at design time

- Status: active
- Decision: use synthetic traces and public Hugging Face datasets as the primary early data sources.
- Why: the tool must make progress before live production traces exist, and the architecture should not depend on private data availability.

### 2026-03-24: Add a Memory Wind Tunnel before hardening the schema

- Status: active
- Decision: compare baseline resume packets against ablated variants that remove one field at a time.
- Why: this creates a causal test for which memory fields actually matter instead of relying on intuition or only on presence in successful runs.

### 2026-03-24: Enforce local quality gates before commit

- Status: active
- Decision: require passing Python linting, Markdown linting, tests, and at least 90% coverage through a repo-local quality script and pre-commit hook.
- Why: the project is still small enough that strict local gates are cheap, and they prevent fast-moving design work from silently lowering implementation quality.
