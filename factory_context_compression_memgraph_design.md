# Memgraph-Based Context Compression with Anchor Points

## Executive summary

This document proposes a production-grade context compression system inspired by Factory's public description of "incremental compression with anchor points for near-perfect context" and adapts it to a local-first architecture built on top of `memgraph`.

The design treats context not as a flat prompt, but as a dynamic working subgraph assembled from:

- stable anchors,
- structural code entities,
- conversational and task artifacts,
- compressed multi-resolution summaries,
- selective rehydration paths.

The core idea is simple: **never compress everything equally**. Preserve structurally central, frequently reused, and semantically load-bearing entities as anchors. Compress the surrounding material incrementally into layered abstractions. Re-expand only the parts needed for a task.

The proposal includes:

- a problem statement,
- design goals and non-goals,
- a Memgraph schema,
- scoring and anchoring algorithms,
- a hierarchical compression pipeline,
- retrieval and rehydration logic,
- implementation modules,
- observability and failure handling,
- and a comprehensive evaluation harness to test effectiveness against naive truncation, naive summarization, and vector-only retrieval.

The intended audience is Codex or another implementation agent that will produce the first working version.

---

## 1. Problem statement

### 1.1 The actual problem

LLM systems fail on long-running software and knowledge tasks because the effective working context is fragile.

The standard failure modes are:

1. **Window overflow**
   - raw context no longer fits,
   - older but important details are dropped.

2. **Repeated summarization drift**
   - summaries summarize summaries,
   - technical precision degrades,
   - subtle constraints disappear,
   - wrong abstractions become sticky.

3. **Flat retrieval without structure**
   - vector search surfaces related chunks,
   - but loses topology, ownership, and dependency semantics,
   - especially harmful for code and multi-step agent work.

4. **No distinction between core and peripheral context**
   - all content competes equally,
   - implementation detail can displace load-bearing invariants,
   - recent but irrelevant text can crowd out stable facts.

5. **Inability to selectively rehydrate**
   - once compressed, detail is often gone,
   - or requires a fresh search over unstructured stores.

For software agents this becomes acute. Agents need to retain:

- system goals,
- architectural constraints,
- task plans,
- code structure,
- key decisions,
- unresolved questions,
- failures and lessons,
- interface contracts,
- source-of-truth file locations.

A robust system therefore needs **working memory**, **long-term memory**, **structural awareness**, and **incremental compression**.

### 1.2 Why a graph is a good fit

A graph is a natural substrate for context because most high-value context is relational.

Examples:

- a function belongs to a file,
- a file implements an interface,
- a task updates a module,
- a decision constrains a component,
- a summary compresses a set of chunks,
- a hypothesis was derived from evidence,
- an anchor is supported by multiple artifacts.

Graphs support:

- centrality estimation,
- dependency traversal,
- provenance,
- multi-resolution representations,
- selective rehydration,
- and task-local working subgraph assembly.

`memgraph` is a strong fit because it is fast, local-friendly, and queryable via Cypher, while remaining simple enough for an implementation-oriented prototype.

---

## 2. Goals and non-goals

### 2.1 Goals

The system must:

1. preserve high-value context across long-running sessions,
2. identify and maintain stable anchor points,
3. compress incrementally instead of periodically replacing all history,
4. support code-aware and document-aware structure,
5. create multi-resolution memory layers,
6. rehydrate detail on demand,
7. expose measurable effectiveness,
8. remain implementable in a staged way,
9. support local-first use with Memgraph as the primary state store,
10. make failure visible through metrics and traceability.

### 2.2 Non-goals for v1

The first implementation does not need:

- perfect semantic equivalence under all compression,
- full AST support for every language,
- a custom vector index inside Memgraph itself,
- multi-user tenancy,
- a GUI,
- or autonomous self-tuning of all scoring weights.

These can come later.

---

## 3. Conceptual model

### 3.1 Core concepts

#### Anchor
An anchor is a context entity that should remain stable and directly available in compressed memory because it is repeatedly useful or load-bearing.

Examples:

- active task goal,
- architecture decision,
- canonical interface contract,
- core domain entity,
- file or symbol with high dependency centrality,
- unresolved blocking issue,
- authoritative source path.

#### Context unit
A context unit is an atomic retrievable item.

Examples:

- conversation turn,
- file chunk,
- function,
- class,
- issue,
- decision note,
- plan step,
- command output,
- summary node.

#### Compression level
A layered representation of a context unit or group of units.

Suggested levels:

- **L0**: raw content or exact extract,
- **L1**: concise structured summary,
- **L2**: abstracted summary with key invariants only,
- **L3**: relationship-only or anchor-only representation.

#### Rehydration
Traversal from a compressed node back to raw source material or finer-grained summaries.

#### Working set
The subgraph chosen for a specific prompt or task.

### 3.2 Design principle

The main principle is:

> Preserve anchors, compress the periphery, and maintain explicit paths back to detail.

---

## 4. High-level architecture

```text
Ingestion -> Graph builder -> Anchor scorer -> Compression planner ->
Summarizer/compressor -> Multi-resolution graph store ->
Retriever/rehydrator -> Prompt assembly -> Evaluation and telemetry
```

### 4.1 Main services

1. **Ingestion service**
   - accepts code, markdown, notes, conversations, issue data, and tool output,
   - splits content into typed units,
   - computes metadata and embeddings.

2. **Graph builder**
   - writes entities and relations into Memgraph,
   - links chunks to files, files to repos, symbols to files, turns to tasks, summaries to source units.

3. **Anchor scoring service**
   - calculates a persistent `anchor_score`,
   - updates promotion or demotion state.

4. **Compression planner**
   - decides what can be compressed,
   - determines grouping boundaries,
   - preserves anchors and active neighborhoods.

5. **Compressor/summarizer**
   - creates L1 and L2 nodes,
   - stores provenance and summary coverage,
   - extracts invariants and unresolved issues.

6. **Retriever/rehydrator**
   - assembles task-specific subgraphs,
   - expands detail when required.

7. **Prompt assembler**
   - emits structured prompt packages or agent context payloads.

8. **Evaluation harness**
   - runs benchmark tasks,
   - compares strategies,
   - tracks factual retention, code precision, and task performance.

---

## 5. Memgraph data model

The graph should be explicit, typed, and provenance-heavy.

### 5.1 Node labels

#### Repository and code structure
- `Repo`
- `Branch`
- `File`
- `Chunk`
- `Symbol`
- `Function`
- `Class`
- `Interface`
- `Module`
- `Import`

#### Conversation and tasking
- `Session`
- `Turn`
- `Message`
- `Task`
- `Plan`
- `PlanStep`
- `Decision`
- `Issue`
- `Hypothesis`
- `Observation`
- `CommandOutput`

#### Compression and memory
- `Summary`
- `Invariant`
- `Anchor`
- `ContextGroup`
- `Embedding`
- `CompressionRun`
- `RetrievalRun`
- `EvaluationRun`
- `BenchmarkCase`
- `Metric`

#### External or document types
- `Document`
- `Section`
- `Requirement`
- `Spec`
- `TestCase`

### 5.2 Important relationships

- `(Repo)-[:HAS_FILE]->(File)`
- `(File)-[:HAS_CHUNK]->(Chunk)`
- `(File)-[:DECLARES]->(Symbol)`
- `(Symbol)-[:DEPENDS_ON]->(Symbol)`
- `(Symbol)-[:IMPLEMENTED_IN]->(File)`
- `(File)-[:IMPORTS]->(File)`
- `(Session)-[:HAS_TURN]->(Turn)`
- `(Turn)-[:HAS_MESSAGE]->(Message)`
- `(Task)-[:HAS_PLAN]->(Plan)`
- `(Plan)-[:HAS_STEP]->(PlanStep)`
- `(Task)-[:CONSTRAINED_BY]->(Decision)`
- `(Issue)-[:BLOCKS]->(Task)`
- `(Observation)-[:SUPPORTS]->(Hypothesis)`
- `(Summary)-[:SUMMARIZES]->(Chunk|Turn|File|Task|ContextGroup)`
- `(Summary)-[:DERIVED_FROM]->(Chunk|Turn|File|Task|ContextGroup)`
- `(Summary)-[:PRESERVES]->(Invariant)`
- `(Anchor)-[:ANCHORS]->(Symbol|Task|Decision|Invariant|File|Issue)`
- `(ContextGroup)-[:CONTAINS]->(Chunk|Turn|Summary|Symbol|Issue)`
- `(Summary)-[:REHYDRATES_TO]->(Chunk|File|Turn|Symbol|Issue)`
- `(Embedding)-[:EMBEDS]->(Chunk|Summary|Decision|Task)`
- `(CompressionRun)-[:CREATED]->(Summary|Invariant|ContextGroup)`
- `(RetrievalRun)-[:SELECTED]->(Chunk|Summary|Anchor|Decision|Task)`
- `(EvaluationRun)-[:MEASURED]->(Metric)`
- `(BenchmarkCase)-[:USES]->(Task|Repo|Document)`

### 5.3 Suggested node properties

#### Shared fields
Every high-value node should support:

- `id` (UUID)
- `source_id`
- `created_at`
- `updated_at`
- `modality` (`code`, `conversation`, `spec`, `tool_output`, `summary`)
- `scope` (`session`, `repo`, `task`, `global`)
- `importance`
- `salience`
- `confidence`
- `freshness`
- `anchor_score`
- `compression_level`
- `token_count`
- `hash`

#### File
- `path`
- `language`
- `repo_name`
- `branch_name`

#### Chunk
- `start_line`
- `end_line`
- `content`
- `content_type`
- `semantic_role`

#### Symbol
- `name`
- `symbol_type`
- `signature`
- `fully_qualified_name`

#### Turn / Message
- `role`
- `content`
- `turn_index`

#### Summary
- `summary_text`
- `summary_type` (`extractive`, `abstractive`, `hybrid`, `structural`)
- `preserved_items`
- `omitted_items`
- `coverage_score`
- `loss_risk_score`
- `level` (`L1`, `L2`, `L3`)

#### Invariant
- `text`
- `category` (`requirement`, `decision`, `constraint`, `contract`, `risk`, `todo`)
- `criticality`

#### Anchor
- `anchor_type`
- `stability_score`
- `promotion_reason`
- `demotion_reason`

#### Metric
- `name`
- `value`
- `unit`
- `strategy`
- `case_id`

### 5.4 Indexes and constraints

At minimum:

```cypher
CREATE CONSTRAINT ON (n:Repo) ASSERT n.id IS UNIQUE;
CREATE CONSTRAINT ON (n:File) ASSERT n.id IS UNIQUE;
CREATE CONSTRAINT ON (n:Chunk) ASSERT n.id IS UNIQUE;
CREATE CONSTRAINT ON (n:Symbol) ASSERT n.id IS UNIQUE;
CREATE CONSTRAINT ON (n:Task) ASSERT n.id IS UNIQUE;
CREATE CONSTRAINT ON (n:Summary) ASSERT n.id IS UNIQUE;
CREATE CONSTRAINT ON (n:Anchor) ASSERT n.id IS UNIQUE;
CREATE CONSTRAINT ON (n:Session) ASSERT n.id IS UNIQUE;
CREATE CONSTRAINT ON (n:BenchmarkCase) ASSERT n.id IS UNIQUE;
CREATE CONSTRAINT ON (n:EvaluationRun) ASSERT n.id IS UNIQUE;

CREATE INDEX ON :File(path);
CREATE INDEX ON :Symbol(fully_qualified_name);
CREATE INDEX ON :Chunk(hash);
CREATE INDEX ON :Task(scope);
CREATE INDEX ON :Summary(level);
CREATE INDEX ON :Anchor(anchor_type);
```

If Memgraph features or syntax differ by version, adapt accordingly.

---

## 6. Anchor selection and scoring

Anchor selection is the center of the design.

### 6.1 Anchor intuition

A node should become an anchor when it is:

- reused often,
- structurally central,
- semantically critical,
- cited repeatedly by tasks or summaries,
- hard to recover correctly if lost,
- or known to constrain future decisions.

### 6.2 Anchor score formula

The initial score can be a weighted sum:

```text
anchor_score =
  w1 * structural_centrality
+ w2 * task_relevance
+ w3 * recurrence
+ w4 * constraint_density
+ w5 * failure_cost
+ w6 * freshness_bonus
+ w7 * user_marked_importance
- w8 * volatility_penalty
```

#### Components

- `structural_centrality`
  - degree, weighted degree, PageRank-like importance in dependency graph.

- `task_relevance`
  - relevance to currently active tasks or plans.

- `recurrence`
  - how often referenced across turns, summaries, retrievals, or changes.

- `constraint_density`
  - whether the node carries contracts, invariants, or requirements.

- `failure_cost`
  - how damaging it is if forgotten or distorted.

- `freshness_bonus`
  - useful when recent changes are highly relevant.

- `user_marked_importance`
  - explicit pinning or high-priority tags.

- `volatility_penalty`
  - nodes changing constantly may not be good anchors unless also structurally critical.

### 6.3 Anchor classes

Not all anchors are equal.

#### A. Structural anchors
Examples:
- public interfaces,
- core services,
- entry points,
- schema definitions,
- high-fan-in symbols.

#### B. Task anchors
Examples:
- current mission goal,
- plan step in progress,
- blockers,
- acceptance criteria.

#### C. Decision anchors
Examples:
- architecture decisions,
- hard constraints,
- security boundaries,
- API contracts.

#### D. Episodic anchors
Examples:
- recent failure with an important lesson,
- a critical experiment result,
- a decision reversal.

### 6.4 Promotion and demotion

Anchoring must be dynamic but conservative.

#### Promote when
- score crosses threshold,
- repeatedly selected in retrieval,
- referenced by new summaries,
- linked to unresolved issues or active tasks,
- manually pinned.

#### Demote when
- stale for long periods,
- not structurally important,
- no longer linked to active goals,
- replaced by newer authoritative anchor.

Demotion should not delete raw material. It only changes retention priority.

### 6.5 Initial heuristic version

For v1 use transparent heuristics instead of complex learning:

```text
if node.type in {Decision, Invariant, Interface, Task} then base += 0.30
if dependency_degree > threshold then base += 0.20
if referenced_in_last_n_retrievals > threshold then base += 0.15
if linked_to_active_task then base += 0.20
if criticality == 'high' then base += 0.20
if volatility == 'high' then base -= 0.10
```

This is enough for a useful first system.

---

## 7. Incremental compression strategy

### 7.1 Why incremental matters

One-shot summarization is dangerous because it forces the system to re-express the entire context at once. Incremental compression instead compresses only stable peripheral regions while preserving critical neighborhoods and provenance.

### 7.2 Compression boundaries

Compression should happen within coherent groups, not arbitrary token windows.

Candidate groups:

- all turns belonging to a closed subtask,
- chunks from one file section,
- a finished plan phase,
- old log output under the same incident,
- related discussion attached to one decision.

Represent these as `ContextGroup` nodes.

### 7.3 Compression rules

#### Rule 1: never compress anchors away
Anchors should remain directly retrievable and should usually keep an L0 or L1 representation.

#### Rule 2: preserve invariants explicitly
Before summarizing a group, extract hard facts and create `Invariant` nodes.

#### Rule 3: compress only closed or low-activity regions unless storage pressure is extreme
Do not compress a region heavily while an agent is actively editing it.

#### Rule 4: preserve provenance
Every summary must link to exactly what it summarizes.

#### Rule 5: support multiple levels
Do not overwrite L1 with L2. Store both.

### 7.4 Compression pipeline

For each candidate `ContextGroup`:

1. identify contained anchors,
2. extract invariant candidates,
3. create L1 summary,
4. optionally create L2 summary,
5. measure summary risk,
6. decide whether to mark raw nodes as cold,
7. update retrieval weights.

### 7.5 Types of compression

#### A. Structural compression for code
Preserve:
- file role,
- symbol names,
- public signatures,
- imports/dependencies,
- key behaviors,
- side effects,
- TODOs,
- contracts and exceptions.

Compress:
- local implementation detail,
- repetitive boilerplate,
- comments with low decision value.

#### B. Episodic compression for conversation
Preserve:
- goals,
- decisions,
- blockers,
- open questions,
- promised next steps,
- major evidence.

Compress:
- politeness chatter,
- repeated rephrasings,
- low-value back-and-forth.

#### C. Operational compression for logs and tool output
Preserve:
- command intent,
- failure signature,
- root cause clues,
- version and environment facts,
- successful fix.

Compress:
- repetitive log lines,
- verbose stack traces after extracting signatures.

---

## 8. Hierarchical memory model

### 8.1 Levels

#### L0, raw layer
Contains exact source content.

Use when:
- user asks for precise code change,
- contract detail matters,
- evaluation needs exactness.

#### L1, structured summary layer
Contains concise but faithful summaries with entity names, important relationships, invariants, and source links.

Use as default retrieval layer.

#### L2, abstracted summary layer
Contains high-level behavior, role, decision impact, and essential constraints only.

Use for global planning.

#### L3, anchor graph layer
Contains mainly anchors and relationships among them.

Use when the graph must fit a tiny prompt budget or bootstrap an agent with strategic context.

### 8.2 Memory transitions

```text
L0 -> L1 -> L2
  \      \-> invariants preserved independently
   \-> anchor promotion can happen at any stage
```

### 8.3 Rehydration policy

Rehydrate from:

- anchor neighborhood when anchor selected,
- source file if symbol edit requested,
- supporting evidence if confidence low,
- benchmark gold set when evaluating retrieval correctness.

---

## 9. Retrieval and prompt assembly

### 9.1 Retrieval stages

A good retrieval pipeline should combine graph structure and semantic relevance.

#### Stage 1: seed selection
Seeds can come from:
- user query embeddings,
- active task ID,
- file path or symbol mention,
- last selected anchors,
- unresolved issues.

#### Stage 2: graph expansion
Expand around seeds using relationship-aware traversal.

Suggested priority:
1. anchors,
2. invariants,
3. active task nodes,
4. decision nodes,
5. L1 summaries,
6. raw source for rehydration.

#### Stage 3: token budgeting
Build the context package under a token budget.

Suggested order under pressure:
- keep anchors,
- keep constraints,
- prefer L1 over L0,
- rehydrate only top-risk items.

### 9.2 Retrieval score

```text
retrieval_score =
  a1 * semantic_similarity
+ a2 * anchor_score
+ a3 * graph_distance_bonus
+ a4 * active_task_overlap
+ a5 * freshness
+ a6 * evidence_support
- a7 * redundancy_penalty
```

### 9.3 Prompt assembly format

The system should emit a structured prompt payload with sections such as:

1. active objective,
2. critical anchors,
3. preserved constraints,
4. relevant summaries,
5. rehydrated detail,
6. unresolved issues,
7. source references.

Example:

```yaml
objective:
  text: Refactor MCP adapter to support local Ollama models.
anchors:
  - openclaw gateway auth token mismatch is a recurring blocker
  - adapter package lives under services/adapter
constraints:
  - do not break existing provider config schema
  - keep local-first support
summaries:
  - file services/adapter/config.py handles provider schema validation
rehydrated:
  - exact signature for ProviderConfig.from_dict(...)
open_questions:
  - should gateway token be sourced from launchd env or config file
sources:
  - file path
  - turn ids
  - decision ids
```

This makes the system more inspectable and agent-friendly.

---

## 10. Summarization and invariant extraction

### 10.1 Summary schema

A generated summary should not just be free-form prose. It should be stored in a structured shape.

Recommended fields:

```json
{
  "title": "Config validation in adapter",
  "entity_type": "file_summary",
  "level": "L1",
  "key_points": [
    "Validates provider configs for OpenAI, local Ollama, and Gemini.",
    "Current implementation assumes one provider schema path."
  ],
  "invariants": [
    "Local-first provider support must remain available.",
    "Existing config file format should stay backward compatible."
  ],
  "open_questions": [
    "Should provider defaults be merged before validation?"
  ],
  "risks": [
    "Refactor may break gateway token handling."
  ],
  "source_refs": ["chunk-1", "chunk-2", "decision-7"]
}
```

### 10.2 Invariant extraction

Invariants are first-class and should survive every compression cycle.

Categories:
- requirements,
- contracts,
- constraints,
- assumptions,
- risks,
- TODOs,
- decisions.

Extraction can begin as a hybrid system:

- regex or rule-based candidate extraction,
- LLM-based normalization and deduplication,
- graph merge into canonical invariants.

### 10.3 Deduplication

Summaries and invariants will duplicate over time unless merged.

Use:
- hash-based dedupe for exact text,
- semantic similarity threshold for near duplicates,
- graph merge rules when one new invariant overlaps an existing canonical invariant.

---

## 11. Implementation plan

This section is written for Codex to implement directly.

### 11.1 Suggested repository structure

```text
context-compression/
  README.md
  pyproject.toml
  src/
    cc/
      __init__.py
      config.py
      types.py
      memgraph/
        client.py
        schema.py
        queries.py
      ingest/
        chunker.py
        code_parser.py
        conversation_parser.py
        document_parser.py
      embeddings/
        provider.py
      graph/
        builder.py
        anchor_scoring.py
        grouping.py
      compression/
        planner.py
        summarizer.py
        invariants.py
        dedupe.py
      retrieval/
        seeds.py
        traversal.py
        ranking.py
        rehydration.py
        assembler.py
      eval/
        datasets.py
        harness.py
        metrics.py
        baselines.py
        reports.py
      telemetry/
        logger.py
        tracing.py
      cli/
        main.py
  tests/
    unit/
    integration/
    benchmark/
  data/
    benchmark_cases/
  scripts/
    init_memgraph.py
    run_benchmarks.py
```

### 11.2 Core implementation phases

#### Phase 1, graph foundation
Implement:
- Memgraph schema bootstrap,
- ingestion for markdown, conversation, and code files,
- base graph builder,
- simple anchor scoring,
- raw retrieval.

#### Phase 2, first compression layer
Implement:
- `ContextGroup` generation,
- L1 summary creation,
- invariant extraction,
- provenance links,
- retrieval with anchors and summaries.

#### Phase 3, hierarchical memory
Implement:
- L2 summaries,
- cold raw node handling,
- rehydration triggers,
- token-budget-aware assembly.

#### Phase 4, benchmark harness
Implement:
- benchmark dataset format,
- baseline strategies,
- automated scoring,
- report generation.

#### Phase 5, tuning and analysis
Implement:
- retrieval metrics dashboard,
- anchor stability reports,
- failure case inspection.

---

## 12. Detailed component design

### 12.1 Ingestion

Inputs:
- repository tree,
- commit diff,
- conversation transcript,
- markdown docs,
- logs or command output.

Responsibilities:
- normalize source records,
- compute hashes,
- split into chunks,
- identify modality and semantic role,
- optionally parse code symbols.

For code parsing, begin with:
- Tree-sitter where available,
- fallback regex extraction for signatures.

### 12.2 Grouping

Compression must operate on coherent groups.

Grouping heuristics:
- by file section,
- by conversation topic segment,
- by plan phase,
- by incident or issue thread,
- by time window with semantic cohesion.

Outputs:
- `ContextGroup` node,
- `CONTAINS` edges,
- group metadata such as modality mix, token count, and activity status.

### 12.3 Anchor scoring service

Responsibilities:
- compute or update `anchor_score`,
- decide anchor promotion,
- store reasoning metadata.

Run:
- after ingestion,
- after retrieval,
- after compression,
- periodically as maintenance.

### 12.4 Compression planner

Responsibilities:
- identify candidate groups,
- exclude hot or active regions,
- estimate compression value and risk,
- choose summary level.

Suggested planner output:

```json
{
  "group_id": "cg-123",
  "eligible": true,
  "reason": "closed task discussion older than threshold",
  "contains_anchor": true,
  "proposed_action": "create_L1_only",
  "risk_score": 0.32
}
```

### 12.5 Summarizer

Responsibilities:
- generate summary text or JSON summary,
- extract invariants,
- identify omissions,
- estimate coverage.

Important: the summarizer should receive the anchor and invariant context for the group so it does not flatten away what matters.

### 12.6 Retriever and rehydrator

Responsibilities:
- choose seeds,
- expand graph,
- rank nodes,
- decide what to keep compressed,
- rehydrate where exactness is needed.

Rehydration triggers:
- direct request for code modification,
- low confidence due to only abstract summaries,
- user asks "where exactly?",
- benchmark judge expects exact fact retrieval.

---

## 13. Comprehensive evaluation harness

This is critical. Without a serious harness the project will drift into anecdote.

### 13.1 What the harness should prove

The harness should test whether the proposed system outperforms simpler baselines on:

1. factual retention,
2. constraint preservation,
3. code-edit accuracy,
4. long-horizon task continuity,
5. retrieval efficiency under token limits,
6. resistance to summarization drift.

### 13.2 Baselines

Implement at least four strategies:

#### Baseline A, sliding window
Use most recent raw chunks until token budget exhausted.

#### Baseline B, naive rolling summary
Summarize old context into one summary blob, append recent raw context.

#### Baseline C, vector-only RAG
Retrieve top-k chunks by embedding similarity, no graph or anchor logic.

#### Baseline D, graph retrieval without compression
Retrieve via graph structure, but no multi-level summaries.

#### Proposed strategy E
Anchor-based incremental compression with hierarchical rehydration.

### 13.3 Benchmark case types

Create a diverse benchmark suite.

#### Type 1, long conversation retention
Example tasks:
- later ask about an early constraint,
- ask for earlier decision rationale,
- ask what blocker remained unresolved.

#### Type 2, codebase reasoning
Example tasks:
- identify where an interface is implemented,
- modify a function without breaking a contract,
- explain a dependency chain,
- answer which file handles a behavior introduced much earlier.

#### Type 3, multi-step task continuity
Example tasks:
- plan created early,
- follow-up edits later,
- final prompt checks if acceptance criteria remain aligned.

#### Type 4, incident debugging memory
Example tasks:
- log snippets ingested over time,
- root cause hypothesis updated,
- later ask for likely cause and prior attempted fixes.

#### Type 5, spec-to-code alignment
Example tasks:
- requirement introduced in a spec,
- code references later,
- ask whether implementation matches the requirement.

### 13.4 Benchmark dataset format

Use a machine-readable JSONL or YAML format.

Example JSON case:

```json
{
  "id": "case-code-001",
  "domain": "code",
  "description": "Refactor task with early constraint and later implementation detail",
  "sources": [
    {"type": "file", "path": "src/service/config.py", "content": "..."},
    {"type": "conversation", "turns": ["..."]},
    {"type": "spec", "content": "..."}
  ],
  "timeline": [
    {"step": 1, "ingest": ["source_a"]},
    {"step": 2, "query": "What are the compatibility constraints?"},
    {"step": 3, "ingest": ["source_b"]},
    {"step": 4, "query": "Now modify the adapter while preserving the constraints."}
  ],
  "gold": {
    "facts": [
      "The config file format must remain backward compatible.",
      "Local Ollama support must not break."
    ],
    "required_entities": [
      "ProviderConfig.from_dict",
      "services/adapter/config.py"
    ],
    "forbidden_errors": [
      "claiming GraphQL is required"
    ]
  }
}
```

### 13.5 Metrics

Use both automatic and judge-assisted metrics.

#### Retrieval metrics
- Recall@k of gold facts,
- Recall@k of gold entities,
- anchor hit rate,
- mean graph distance from gold evidence,
- redundancy ratio,
- average token cost.

#### Answer quality metrics
- factual precision,
- factual recall,
- constraint preservation score,
- hallucination count,
- code entity exactness,
- source attribution correctness.

#### Task completion metrics
- success/failure on benchmark objective,
- acceptance criteria coverage,
- number of corrective follow-ups needed.

#### Compression metrics
- compression ratio,
- invariant preservation rate,
- anchor stability over time,
- summary drift score.

#### Operational metrics
- ingestion latency,
- retrieval latency,
- compression latency,
- Memgraph query latency.

### 13.6 Summary drift test

This deserves its own benchmark.

Procedure:
1. ingest a sequence of detailed technical interactions,
2. repeatedly compress as more data arrives,
3. later query exact constraints and rationale,
4. compare retrieved facts with the original source.

Measure:
- fact deletion,
- fact mutation,
- over-generalization,
- contradiction creation.

### 13.7 Rehydration effectiveness test

Procedure:
1. force small prompt budget,
2. retrieve using compressed context,
3. detect cases where exact code detail is needed,
4. trigger rehydration,
5. compare performance before and after.

Measure:
- improvement in code exactness,
- reduction in incorrect edits,
- extra token and latency cost.

### 13.8 Judge model usage

For some metrics use an LLM judge, but do not rely on it exclusively.

Good uses:
- rubric-based answer grading,
- semantic equivalence of extracted invariants,
- identifying whether a response violated a hard constraint.

But also include deterministic checks:
- exact entity string matches,
- file path matches,
- presence or absence of known facts,
- diff-based validation for code edits.

### 13.9 Report generation

Each benchmark run should emit:

- per-case detailed JSON,
- aggregate CSV,
- Markdown report with comparisons,
- and optional plots.

Suggested report sections:
- overall ranking by strategy,
- top wins and failures,
- anchor utilization stats,
- summary drift analysis,
- failure exemplars.

---

## 14. Example evaluation scenario

### 14.1 Scenario

A repo contains:
- adapter config code,
- docs explaining local-first model support,
- conversation history about backward compatibility,
- later task to add a new provider.

The benchmark asks:
- what constraints must be preserved,
- where the validation logic lives,
- and how to implement the extension safely.

### 14.2 Expected failure of weaker baselines

- sliding window forgets earlier constraints,
- naive summary may remember "support multiple providers" but drop "do not break local Ollama",
- vector-only retrieval may surface provider config chunks but miss the decision note that backward compatibility is non-negotiable.

### 14.3 Expected strength of proposed design

- decision and invariant anchors remain live,
- relevant code summary is retrieved,
- rehydration fetches the exact function signature,
- answer preserves both strategic and exact detail.

---

## 15. Suggested concrete algorithms

### 15.1 Anchor update pseudocode

```python
def update_anchor_score(node, graph_ctx):
    score = 0.0
    score += 0.30 * structural_centrality(node, graph_ctx)
    score += 0.20 * task_relevance(node, graph_ctx)
    score += 0.15 * recurrence(node, graph_ctx)
    score += 0.15 * constraint_density(node)
    score += 0.10 * failure_cost(node)
    score += 0.05 * freshness(node)
    score += 0.10 * user_importance(node)
    score -= 0.10 * volatility(node)
    return max(0.0, min(1.0, score))
```

### 15.2 Compression planner pseudocode

```python
def plan_compression(context_group):
    if context_group.is_active:
        return Skip("active group")
    if context_group.contains_only_recent_nodes:
        return Skip("too recent")

    anchor_ratio = compute_anchor_ratio(context_group)
    risk = estimate_loss_risk(context_group)

    if risk > 0.75:
        return Action("L1_only")
    if anchor_ratio > 0.25:
        return Action("L1_with_invariants")
    return Action("L1_and_L2")
```

### 15.3 Retrieval pseudocode

```python
def retrieve(query, active_task_id, budget_tokens):
    seeds = select_seeds(query, active_task_id)
    candidates = expand_graph(seeds, max_depth=3)
    ranked = rank_candidates(query, candidates)

    package = []
    remaining = budget_tokens

    for item in ranked:
        best_repr = choose_representation(item, remaining)
        package.append(best_repr)
        remaining -= best_repr.token_count
        if remaining <= 0:
            break

    package = maybe_rehydrate(package, query, remaining)
    return assemble_prompt(package)
```

### 15.4 Summary drift metric pseudocode

```python
def summary_drift_score(gold_facts, retrieved_facts):
    missing = count_missing(gold_facts, retrieved_facts)
    mutated = count_mutated(gold_facts, retrieved_facts)
    contradictions = count_contradictions(gold_facts, retrieved_facts)
    return (missing * 1.0) + (mutated * 1.5) + (contradictions * 2.0)
```

---

## 16. Memgraph query patterns

### 16.1 Retrieve top anchors for active task

```cypher
MATCH (t:Task {id: $task_id})
OPTIONAL MATCH (t)-[:CONSTRAINED_BY|HAS_PLAN|BLOCKED_BY*1..2]-(n)
WITH collect(DISTINCT n) AS direct_nodes
UNWIND direct_nodes AS n
OPTIONAL MATCH (a:Anchor)-[:ANCHORS]->(n)
RETURN n, a
ORDER BY coalesce(a.stability_score, 0.0) DESC, coalesce(n.anchor_score, 0.0) DESC
LIMIT 25;
```

### 16.2 Get summaries plus provenance for a file

```cypher
MATCH (f:File {path: $path})
OPTIONAL MATCH (s:Summary)-[:SUMMARIZES]->(f)
OPTIONAL MATCH (s)-[:PRESERVES]->(i:Invariant)
OPTIONAL MATCH (s)-[:REHYDRATES_TO]->(r)
RETURN f, s, collect(DISTINCT i) AS invariants, collect(DISTINCT r) AS rehydrate_targets
ORDER BY s.level ASC;
```

### 16.3 Expand anchor neighborhood

```cypher
MATCH (a:Anchor {id: $anchor_id})-[:ANCHORS]->(n)
MATCH p=(n)-[*1..2]-(m)
RETURN p;
```

### 16.4 Find groups eligible for compression

```cypher
MATCH (cg:ContextGroup)
WHERE cg.is_active = false
  AND cg.last_accessed_at < $cutoff
  AND coalesce(cg.compressed, false) = false
RETURN cg
ORDER BY cg.token_count DESC
LIMIT 100;
```

---

## 17. Testing strategy beyond benchmarks

### 17.1 Unit tests

Cover:
- score calculation,
- grouping logic,
- invariant extraction normalization,
- deduplication,
- token budget packing,
- rehydration trigger logic.

### 17.2 Integration tests

Cover:
- ingestion into Memgraph,
- summary creation and relation wiring,
- retrieval across levels,
- anchor promotion after repeated access.

### 17.3 Regression tests

Curate failure cases where:
- a key decision vanished,
- a file path was forgotten,
- an invariant was mutated,
- code exactness was lost after compression.

These should remain in the harness permanently.

### 17.4 Property-style tests

Useful assertions:
- every summary has at least one `DERIVED_FROM` source,
- every invariant preserved by a summary can be traced to at least one raw source,
- no compressed group with anchors loses all direct access to its anchors,
- retrieval under a larger budget should not perform worse than under a smaller budget on deterministic metrics.

---

## 18. Observability and debugging

This system will be hard to trust without visibility.

### 18.1 Telemetry to emit

Per retrieval run:
- selected seeds,
- selected anchors,
- chosen representation levels,
- rehydration decisions,
- final token allocation.

Per compression run:
- group selected,
- risk score,
- anchor ratio,
- summary level produced,
- invariant count,
- coverage estimate.

### 18.2 Debug artifacts

Store:
- prompt packages,
- summary JSON,
- benchmark judge outputs,
- source-to-summary provenance maps,
- before and after retrieval snapshots.

### 18.3 Failure inspection view

Codex should generate a Markdown failure report for benchmark cases with:
- question,
- expected facts,
- retrieved nodes,
- answer produced,
- missed anchors,
- root-cause hypothesis.

---

## 19. Risks and mitigations

### Risk 1, bad anchor scoring
A poor scoring formula can lock in the wrong things.

Mitigation:
- transparent weights,
- benchmark tuning,
- inspectable promotion reasons,
- manual pin support.

### Risk 2, summary hallucination
Abstractive summaries can fabricate or over-generalize.

Mitigation:
- require provenance,
- preserve invariants separately,
- use extractive or hybrid summaries for high-risk domains,
- evaluate drift explicitly.

### Risk 3, graph bloat
The graph may grow too quickly.

Mitigation:
- deduplication,
- cold storage markers,
- periodic pruning of low-value transient nodes,
- external object storage for large raw payloads if needed.

### Risk 4, slow retrieval
Graph traversal plus rehydration can become expensive.

Mitigation:
- indexes,
- bounded traversal,
- cached neighborhoods,
- precomputed anchor neighborhoods.

### Risk 5, code parser fragility
Parsing every language perfectly is hard.

Mitigation:
- start with Python, TypeScript, Go,
- fallback to chunk-level structure,
- isolate parser adapters.

---

## 20. Recommended initial technical stack

Suggested implementation stack:

- Python 3.12+
- `gqlalchemy` or Memgraph-compatible driver
- `pydantic` for typed models
- Tree-sitter for code parsing where possible
- a pluggable embedding provider
- pytest for tests
- pandas and matplotlib for benchmark reports
- uv for environment management

Optional later:
- FastAPI service wrapper
- OpenTelemetry traces
- lightweight web dashboard

---

## 21. Concrete deliverables for Codex

Codex should implement the following in order.

### Deliverable 1
A repository with:
- Memgraph schema bootstrap,
- typed models,
- ingestion for code, markdown, and conversation transcripts.

### Deliverable 2
Anchor scoring with:
- a configurable weight file,
- promotion and demotion logic,
- explainable score output.

### Deliverable 3
Compression pipeline with:
- context grouping,
- L1 summaries,
- invariant extraction,
- provenance graph wiring.

### Deliverable 4
Retrieval and prompt assembly with:
- graph traversal,
- ranking,
- token-budget packing,
- rehydration.

### Deliverable 5
A benchmark harness with:
- baseline strategies,
- benchmark case format,
- automated metrics,
- Markdown report generation.

### Deliverable 6
A reproducible demo script that:
- ingests a sample repo and conversation timeline,
- runs all strategies,
- prints comparison tables,
- writes reports to disk.

---

## 22. Acceptance criteria

The first production-worthy prototype should satisfy these criteria:

1. can ingest mixed context into Memgraph,
2. promotes anchors with transparent scores,
3. stores at least L0 and L1 memory representations,
4. retrieves anchors and summaries under a fixed token budget,
5. rehydrates raw detail when exactness is needed,
6. runs a benchmark suite comparing at least five strategies,
7. emits a Markdown benchmark report,
8. shows measurable gains over at least sliding window and naive rolling summary on retention and constraint preservation.

Suggested target for early success:
- at least 20 percent better constraint preservation than naive rolling summary,
- at least 15 percent better fact recall than sliding window in long-horizon tasks,
- equal or lower hallucination rate than vector-only RAG,
- acceptable latency for local experimentation.

---

## 23. Roadmap after v1

After the first version works, the next valuable steps are:

1. learn scoring weights from benchmark outcomes,
2. add better language-specific structure extraction,
3. support temporal decay and episodic memory classes,
4. build a graph-aware MCP server for retrieval,
5. add visual inspection of anchors, summaries, and provenance,
6. support write-back from agents after task completion,
7. integrate with your memgraph-based personal knowledge systems.

---

## 24. Final recommendation

Do not build this as "just summarization with a graph on the side". That will fail.

Build it as a **graph-native memory system** where:
- anchors are first-class,
- summaries are layered,
- invariants are explicit,
- provenance is non-optional,
- and evaluation is built in from day one.

That is the difference between a toy memory feature and a durable context substrate for serious agents.

---

## Appendix A, minimal benchmark directory example

```text
data/benchmark_cases/
  long_conversation/
    case_001.json
    case_002.json
  code_reasoning/
    case_101.json
    case_102.json
  task_continuity/
    case_201.json
  incident_debugging/
    case_301.json
```

---

## Appendix B, minimal CLI commands

```bash
uv run python -m cc.cli.main init-schema
uv run python -m cc.cli.main ingest --repo ./sample_repo --session ./sample_session.json
uv run python -m cc.cli.main compress --scope session:demo
uv run python -m cc.cli.main retrieve --query "What constraints must be preserved?"
uv run python -m cc.cli.main benchmark --suite all --report ./reports/benchmark.md
```

---

## Appendix C, implementation guidance to Codex

When implementing:

- prefer clarity over premature optimization,
- keep all scoring weights configurable,
- make every summary traceable to raw source,
- store intermediate artifacts for debugging,
- treat benchmark infrastructure as a core product feature, not an afterthought,
- and keep the interfaces modular so the summarizer, embedding provider, and retriever can be swapped later.

The benchmark harness is not optional. It is the only reliable way to know whether the system actually preserves context rather than merely producing plausible summaries.
