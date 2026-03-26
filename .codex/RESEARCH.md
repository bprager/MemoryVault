# Research

Last updated: 2026-03-25

## Primary Sources Reviewed

### Context Engineering: Sessions, Memory

- Source: `Context Engineering: Sessions, Memory`
- URL: `https://smallake.kr/wp-content/uploads/2025/12/Context-Engineering_-Sessions-Memory.pdf`
- Key takeaway: session history, working state, and long-term memory are different things, and memory generation should usually happen off the hot path with provenance and retrieval timing treated explicitly.
- Implication for MemoryVault: keep the session store, scratchpad or working state, durable memory, and raw-history backstop as separate layers.

### Generative Agents

- Source: `Generative Agents: Interactive Simulacra of Human Behavior`
- URL: `https://arxiv.org/abs/2304.03442`
- Key takeaway: believable long-running agent behavior depended on observation, planning, and reflection working together, with memory being stored, reflected on, and dynamically retrieved for planning.
- Implication for MemoryVault: memory cannot be separated from planning. The system must preserve plan state explicitly and support reflective updates.

### Reflexion

- Source: `Reflexion: Language Agents with Verbal Reinforcement Learning`
- URL: `https://arxiv.org/abs/2303.11366`
- Key takeaway: agents improve when they keep an episodic memory buffer of feedback and reflections from prior attempts.
- Implication for MemoryVault: success and failure should be stored as first-class memory with explicit reuse in later attempts.

### MemGPT

- Source: `MemGPT: Towards LLMs as Operating Systems`
- URL: `https://arxiv.org/abs/2310.08560`
- Key takeaway: tiered memory and explicit movement between memory levels help agents operate beyond the immediate context window.
- Implication for MemoryVault: the planned layered memory model is directionally sound, but task-state memory should remain in the most durable and accessible tier.

### MemoryBank

- Source: `MemoryBank: Enhancing Large Language Models with Long-Term Memory`
- URL: `https://arxiv.org/abs/2305.10250`
- Key takeaway: long-term memory improves sustained interaction, and selective reinforcement or forgetting can be useful.
- Implication for MemoryVault: use selective forgetting cautiously. It may fit low-value episodic detail, but should not apply to active goals, accepted plans, constraints, or failure history.

### HippoRAG

- Source: `HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models`
- URL: `https://arxiv.org/abs/2405.14831`
- Key takeaway: combining knowledge graphs with Personalized PageRank produced stronger and cheaper multi-hop retrieval than common RAG baselines.
- Implication for MemoryVault: graph retrieval should eventually include a neighborhood-ranking method such as Personalized PageRank rather than relying only on embeddings or simple traversal.

### GraphRAG

- Source: `From Local to Global: A Graph RAG Approach to Query-Focused Summarization`
- URL: `https://www.microsoft.com/en-us/research/publication/from-local-to-global-a-graph-rag-approach-to-query-focused-summarization/`
- Key takeaway: entity graphs plus community summaries improved global sensemaking over large private corpora.
- Implication for MemoryVault: graph-structured summaries are valuable, especially for high-level planning and corpus-wide questions, but should come after explicit task-state memory works.

### LLM Agent Survey

- Source: `A survey on large language model based autonomous agents`
- URL: `https://link.springer.com/article/10.1007/s11704-024-40231-1`
- Key takeaway: memory and planning are core parts of a unified agent framework rather than optional add-ons.
- Implication for MemoryVault: the architecture and benchmarks should treat memory, planning, and action continuity as one system.

### General Agentic Memory Via Deep Research

- Source: `General Agentic Memory Via Deep Research`
- URL: `https://arxiv.org/abs/2511.18423`
- Key takeaway: lightweight memory is most useful when paired with a complete searchable page-store and more deliberate search at retrieval time.
- Implication for MemoryVault: preserve a raw-history backstop and allow higher-effort retrieval paths for exact rehydration.

### A-MEM

- Source: `A-MEM: Agentic Memory for LLM Agents`
- URL: `https://arxiv.org/abs/2502.12110`
- Key takeaway: dynamic linking, rich note attributes, and memory evolution can improve long-running knowledge organization.
- Implication for MemoryVault: use these ideas in the knowledge plane, but keep explicit task state more tightly controlled.

### HyperGraphRAG

- Source: `HyperGraphRAG: Retrieval-Augmented Generation with Hypergraph-Structured Knowledge Representation for Multi-Hop Reasoning`
- URL: `https://arxiv.org/abs/2503.21322`
- Key takeaway: some facts are too lossy when forced into simple pairwise edges.
- Implication for MemoryVault: reified fact nodes or hyperedge-style modeling may be needed later for richer knowledge representation.

### Mem0

- Source: `Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory`
- URL: `https://arxiv.org/abs/2504.19413`
- Key takeaway: practical durable memory can be built around incremental extraction plus explicit update operations such as add, update, delete or invalidate, and no-op; graph memory then extends this with structured relations.
- Implication for MemoryVault: use an explicit memory maintenance contract for declarative memory before introducing more open-ended rewriting.

### Agentic File System Abstraction

- Source: `Everything is Context: Agentic File System Abstraction for Context Engineering`
- URL: `https://arxiv.org/abs/2512.05470`
- Key takeaway: context engineering benefits from explicit infrastructure for history, memory, scratchpads, governance, and traceable state transitions.
- Implication for MemoryVault: keep the lifecycle of raw history, durable memory, and scratchpads explicit and auditable.

### Efficient Agents Survey

- Source: `Toward Efficient Agents: A Survey of Memory, Tool learning, and Planning`
- URL: `https://arxiv.org/abs/2601.14192`
- Key takeaway: agent quality must be evaluated together with token, latency, and step cost, and memory design needs a cost-aware lens across construction, management, access, and integration.
- Implication for MemoryVault: benchmark memory as a cost-quality trade-off rather than as retrieval quality alone.

### ALMA

- Source: `Learning to Continually Learn via Meta-learning Agentic Memory Designs`
- URL: `https://arxiv.org/abs/2602.07755`
- Key takeaway: memory design itself can be treated as a learnable, pluggable module with stable update and retrieve interfaces, and different domains may need different designs.
- Implication for MemoryVault: standardize the memory manager boundary now so future learned or searched memory designs can plug in later.

### Huxley-Godel Machine

- Source: `Huxley-Godel Machine`
- URL: `https://arxiv.org/abs/2510.21614`
- Key takeaway: immediate local scores can be a poor proxy for long-run usefulness.
- Implication for MemoryVault: evaluate memory by downstream task continuity and eventual success, not just local retrieval metrics.

### HyperAgents

- Source: `HyperAgents`
- URL: `https://arxiv.org/abs/2603.19461`
- Key takeaway: persistent memory and performance tracking emerged as transferable self-improvement mechanisms across several task families, but the paper is mainly about self-referential agent improvement rather than memory architecture.
- Implication for MemoryVault: keep performance tracking and synthesized improvement insights as first-class inputs to memory-policy learning, and test whether learned profiles transfer across task families instead of only improving one benchmark.

### Memory and the self

- Source: `Memory and the self`
- URL: `https://doi.org/10.1016/j.jml.2005.08.005`
- Key takeaway: active goals shape access to long-term memory, but healthy memory also depends on correspondence to experience.
- Implication for MemoryVault: retrieval should be goal-conditioned while durable memory stays grounded in evidence and provenance.

### ACE

- Source: `Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models`
- URL: `https://arxiv.org/abs/2510.04618`
- Key takeaway: evolving procedural context is useful, but monolithic rewriting can cause context collapse and destroy detail.
- Implication for MemoryVault: manage procedural memory as incrementally curated playbooks instead of whole-context rewrites.

### StateAct

- Source: `StateAct: Enhancing LLM Base Agents via Self-prompting and State-tracking`
- URL: `https://arxiv.org/abs/2410.02810`
- Key takeaway: agents adhere better over long interactions when they explicitly restate the goal and track current state.
- Implication for MemoryVault: runtime prompt assembly should always include an explicit goal reminder and structured current-state section.

### Model Context Protocol Architecture

- Source: `Model Context Protocol Architecture Overview`
- URL: `https://modelcontextprotocol.io/docs/learn/architecture`
- Key takeaway: MCP separates host, client, and server, supports tools, resources, and prompts, and remote Streamable HTTP servers are designed to serve multiple clients.
- Implication for MemoryVault: MCP is a strong agent-facing adapter for both local and remote use, but it should sit over a stable service core.

### MCP Transports

- Source: `Model Context Protocol Transports`
- URL: `https://modelcontextprotocol.io/specification/2024-11-05/basic/transports`
- Key takeaway: MCP standardizes local `stdio` and remote HTTP-based transports for the same JSON-RPC protocol.
- Implication for MemoryVault: one MCP adapter can cover both local sidecar and shared-service deployment modes.

### OpenAPI

- Source: `OpenAPI Specification v3.1.1`
- URL: `https://spec.openapis.org/oas/v3.1.1.html`
- Key takeaway: OpenAPI defines a language-agnostic way to describe HTTP APIs so humans and machines can understand them with minimal implementation logic.
- Implication for MemoryVault: the canonical service contract should be a versioned HTTP and JSON API described with OpenAPI.

### CloudEvents

- Source: `CloudEvents`
- URL: `https://cloudevents.io/`
- Key takeaway: CloudEvents standardizes event metadata and payload description across systems and languages.
- Implication for MemoryVault: asynchronous update, invalidation, and observability events should use a portable event envelope.

### NATS JetStream

- Source: `NATS JetStream`
- URL: `https://docs.nats.io/nats-concepts/jetstream`
- Key takeaway: JetStream provides durable streams and related storage primitives suitable for asynchronous infrastructure work.
- Implication for MemoryVault: JetStream is a strong first implementation target for the event plane and cache backplane.

### NATS JetStream Key-Value

- Source: `NATS JetStream Key-Value Store`
- URL: `https://docs.nats.io/using-nats/developer/develop_jetstream/kv`
- Key takeaway: the KV layer supports watchable keys and CAS-style updates.
- Implication for MemoryVault: it is a practical candidate for shared cache metadata, lightweight coordination, and invalidation state.

### OpenTelemetry

- Source: `OpenTelemetry Concepts`
- URL: `https://opentelemetry.io/docs/concepts/signals/`
- Key takeaway: traces, metrics, and logs should share one observability model with propagated context across service boundaries.
- Implication for MemoryVault: service, adapter, worker, and broker integrations should share one tracing and metrics vocabulary from the start.

### HTTP Semantics

- Source: `RFC 9110`
- URL: `https://www.rfc-editor.org/rfc/rfc9110`
- Key takeaway: conditional requests with validators are the standard way to revalidate cached responses and protect against lost updates.
- Implication for MemoryVault: the shared-service design should use ETag, `If-None-Match`, and `If-Match` for read validation and concurrent write safety.

### GraphRAG Auto Prompt Tuning

- Source: `GraphRAG Auto Prompt Tuning`
- URL: `https://microsoft.github.io/graphrag/prompt_tuning/auto_prompt_tuning/`
- Key takeaway: domain-adapted prompt generation from representative input is highly encouraged, and automatic entity-type discovery is recommended for broad or highly varied data.
- Implication for MemoryVault: onboarding should prefer automatic prompt adaptation over manual ontology preparation.

### GraphRAG Prompt Tuning Overview

- Source: `GraphRAG Prompt Tuning Overview`
- URL: `https://microsoft.github.io/graphrag/prompt_tuning/overview/`
- Key takeaway: default prompts work out of the box, auto tuning is encouraged, and manual tuning is an advanced path.
- Implication for MemoryVault: zero-touch onboarding should be the default path, with manual starter-pack editing kept optional.

### GraphRAG Methods

- Source: `GraphRAG Methods`
- URL: `https://microsoft.github.io/graphrag/index/methods/`
- Key takeaway: the fast indexing method is cheaper and faster but noisier than the standard method.
- Implication for MemoryVault: a fast first-pass graph build is useful for onboarding acceleration, but it should remain provisional.

### GraphRAG Bring Your Own Graph

- Source: `GraphRAG Bring Your Own Graph`
- URL: `https://microsoft.github.io/graphrag/index/byog/`
- Key takeaway: existing graphs can be brought into the workflow, but they are optional inputs rather than a required starting point.
- Implication for MemoryVault: starter ontologies or custom graphs are useful optional hints, not prerequisites.

### Few-NERD

- Source: `Few-NERD dataset card`
- URL: `https://huggingface.co/datasets/DFKI-SLT/few-nerd`
- Key takeaway: the dataset provides coarse and fine-grained entity types suitable for evaluating type discovery and starter-pack quality.
- Implication for MemoryVault: use it to benchmark onboarding-time candidate type discovery without relying on private corpora.

### DocRED

- Source: `DocRED dataset card`
- URL: `https://huggingface.co/datasets/thunlp/docred`
- Key takeaway: document-level relation extraction requires cross-sentence synthesis and is a useful stress test for relation discovery.
- Implication for MemoryVault: use it to evaluate whether onboarding-time relation hints and provisional graphs are useful or too noisy.

### Hugging Face Dataset Viewer First Rows

- Source: `Hugging Face dataset viewer first-rows guide`
- URL: `https://huggingface.co/docs/dataset-viewer/en/first_rows`
- Key takeaway: the dataset viewer exposes a stable JSON response with dataset features and example rows, which is enough to inspect public dataset shape before full ingestion.
- Implication for MemoryVault: public-data adapters can target saved `first-rows` style payloads for offline tests and later use the same response shape for live fetches.

## Working Conclusions

1. The strongest memory systems do more than retrieve text. They preserve agent state across attempts.
2. Graph structure is most valuable when it encodes relationships among task state, provenance, and evidence, not just entities from documents.
3. Reflection and outcome tracking matter because they stop the agent from repeating failed actions.
4. Tiered memory is useful, but only if the most important task-state records are protected from loss.
5. Compression should be delayed until deterministic retrieval of task-state memory already works.
6. Sessions, long-term memory, and raw history should be treated as separate layers with different lifecycles.
7. Provenance and confidence should influence both consolidation and inference, not just storage.
8. Declarative memory and procedural memory should be designed as separate subsystems.
9. Dynamic linking and memory evolution are promising for the knowledge plane but should not destabilize the control plane.
10. Complex n-ary facts may eventually require reified fact or hyperedge-style nodes in the graph.
11. Memory evaluation should optimize for downstream task success and long-run usefulness, not only local retrieval quality.
12. Scratchpad or working-state artifacts should be explicit and auditable rather than hidden inside durable memory.
13. Explicit add / update / invalidate / noop operations are a strong starting point for declarative memory maintenance.
14. Memory should be benchmarked on a Pareto frontier of quality versus cost.
15. A stable `update` / `retrieve` interface makes the memory layer easier to evolve later.
16. Active goals should shape retrieval, but durable memory must keep correspondence with evidence.
17. Long-horizon reliability improves when the runtime context explicitly restates the goal and current state.
18. Procedural memory should grow through structured incremental playbooks rather than monolithic rewriting.
19. A tool-first memory project should begin with synthetic traces and public datasets if private production traces do not yet exist.
20. Early benchmark coverage should span several task families so the tool does not mistake one domain's memory needs for a general rule.
21. The best integration model is a hybrid: canonical HTTP service, MCP agent adapter, and async event plane.
22. Public-data adapters should follow the real Hugging Face row shape so offline fixtures and optional live fetches use one compatible format.
22. Multi-agent memory systems need explicit tenancy, concurrency, and cache-coherence design.
23. Zero-touch onboarding should be the default, with manual structure treated as optional hints.
24. Fast graph bootstrapping is useful for onboarding speed, but only as provisional knowledge-plane support.

## Intake Note

Detailed source-by-source verdicts for the user-provided documents live in `RESEARCH_INTAKE.md`. The longer human-readable synthesis with links and short quotes lives in `../docs/research.md`.
