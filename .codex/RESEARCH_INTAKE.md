# Research Intake

Last updated: 2026-03-30

## Batch 1: User-Provided Documents

### 1. Context Engineering: Sessions, Memory

- File: `/Users/bernd/Downloads/Context Engineering_ Sessions & Memory.pdf`
- Verdict: accept, core
- Why it matters: it gives a practical architecture for separating sessions, memory, retrieval timing, provenance, and procedural memory.
- Adopt now:
  - keep session state separate from long-term memory
  - treat memory generation as an asynchronous background process when practical
  - track provenance and confidence for durable memories
  - distinguish declarative memory from procedural memory
  - evaluate memory quality, retrieval quality, and task success separately
- Do not over-apply:
  - it is product guidance, not a proof that one vendor’s architecture is the only correct implementation

### 2. General Agentic Memory Via Deep Research

- File: `/Users/bernd/Downloads/2511.18423v1.pdf`
- Verdict: accept, core with caution
- Why it matters: it argues for lightweight memory plus a complete searchable history, then uses planning, search, and reflection at retrieval time to assemble task-specific context.
- Adopt now:
  - preserve a searchable raw-history or page-store backstop
  - use lightweight durable memory as guidance rather than as the only truth source
  - allow retrieval to plan, search, and reflect instead of doing one-shot lookup
  - combine vector, keyword, and direct-source retrieval where useful
- Keep the caution:
  - MemoryVault still needs explicit control-plane memory for task, plan, and outcome state; that should not be replaced by a pure search-over-history design

### 3. A-Mem: Agentic Memory for LLM Agents

- File: `/Users/bernd/Downloads/2502.12110v11.pdf`
- Verdict: accept, useful now for the knowledge plane
- Why it matters: it shows a concrete pattern for note enrichment, dynamic linking, memory evolution, and top-k retrieval over long-running interactions.
- Adopt now:
  - enrich knowledge-plane memories with structured attributes and embeddings
  - allow dynamic linking among related notes
  - consider memory evolution for summaries or contextual descriptions when new evidence arrives
- Keep the caution:
  - explicit control-plane state should not be mutated with the same freedom as descriptive knowledge notes
  - MemoryVault still needs some predefined structure for task, plan, constraint, and outcome records

### 4. HyperGraphRAG

- File: `/Users/bernd/Downloads/2503.21322v3.pdf`
- Verdict: accept, future-state
- Why it matters: it shows that binary-only graph structure can lose important n-ary facts, and it offers a retrieval pattern that combines graph facts with chunk text.
- Adopt later:
  - represent complex facts with reified fact or hyperedge-style nodes when binary edges become too lossy
  - use hybrid retrieval that fuses structured facts with raw chunk context
  - consider separate retrieval over entities and fact nodes
- Why not now:
  - this is not phase-1 critical for MemoryVault’s first thin slice
  - the immediate problem is task-state persistence and retrieval, not high-end knowledge-graph expressiveness

### 5. Huxley-Godel Machine

- File: `/Users/bernd/Downloads/2510.21614v3.pdf`
- Verdict: accept, indirect but important
- Why it matters: it shows that immediate benchmark performance can be a poor proxy for long-run agent usefulness and that evaluation should consider longer-run descendants and outcomes.
- Adopt now:
  - judge MemoryVault by downstream task continuity, failure avoidance, and final success, not only by local retrieval scores
  - separate expansion from evaluation when exploring adaptive improvements
  - early-stop unpromising paths instead of spending equal effort everywhere
- Why it is indirect:
  - it is not a memory architecture paper
  - it affects how MemoryVault should evaluate and improve itself later, more than how phase 1 stores memory

## Batch 1 Summary

- Core now: `Context Engineering: Sessions, Memory`, `General Agentic Memory Via Deep Research`
- Useful now in a bounded way: `A-Mem: Agentic Memory for LLM Agents`
- Useful later: `HyperGraphRAG`, `Huxley-Godel Machine`
- Rejected as irrelevant: none

## Batch 2: User-Provided Documents

### 1. A-Mem: Agentic Memory for LLM Agents

- File: `/Users/bernd/Downloads/2502.12110v11.pdf`
- Verdict: duplicate, carry forward
- Why it matters: this paper was already assessed in Batch 1 and remains relevant for knowledge-plane note enrichment, linking, and bounded memory evolution.
- New action from this batch:
  - no change in verdict
  - keep it as a knowledge-plane idea, not a control-plane mechanism

### 2. Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory

- File: `/Users/bernd/Downloads/2504.19413v1.pdf`
- Verdict: accept, useful now
- Why it matters: it gives a practical update pipeline for durable declarative memory using candidate extraction, similarity-based comparison, and explicit operations such as add, update, delete or invalidate, and no-op.
- Adopt now:
  - use a bounded declarative-memory update contract
  - support asynchronous conversation summary generation as context for extraction
  - preserve conflict handling and invalidation semantics instead of naive append-only storage
- Adopt later:
  - graph-backed memory for richer relational retrieval if phase-1 memory proves too flat

### 3. Everything is Context: Agentic File System Abstraction for Context Engineering

- File: `/Users/bernd/Downloads/2512.05470v1.pdf`
- Verdict: accept, useful now with caution
- Why it matters: it reinforces explicit history, memory, and scratchpad lifecycles, along with governance, access control, and lineage.
- Adopt now:
  - make scratchpad handling explicit
  - keep state transitions auditable
  - treat access control, lineage, and retention as architecture, not cleanup
- Keep the caution:
  - the specific file-system abstraction is interesting, but MemoryVault does not need to commit to “everything is a file” in phase 1

### 4. Toward Efficient Agents: A Survey of Memory, Tool learning, and Planning

- File: `/Users/bernd/Downloads/2601.14192v1.pdf`
- Verdict: accept, useful now
- Why it matters: it frames memory as a quality-versus-cost trade-off and surveys practical patterns for working memory, external memory, hybrid management, and memory access.
- Adopt now:
  - evaluate MemoryVault on both quality and cost
  - prefer hybrid management where cheap rules handle obvious cases and LLM reasoning is invoked selectively
  - keep working memory compact and durable memory targeted
- Do not over-apply:
  - this is a survey, so it is more useful for evaluation discipline and design vocabulary than for a single concrete algorithm

### 5. Learning to Continually Learn via Meta-learning Agentic Memory Designs

- File: `/Users/bernd/Downloads/2602.07755v1.pdf`
- Verdict: accept, future-state
- Why it matters: it treats memory design itself as something that can be learned, and it argues for stable `update` and `retrieve` interfaces for memory modules.
- Adopt now:
  - standardize the memory manager boundary around update and retrieve
- Adopt later:
  - explore searched or learned memory designs after a stable hand-designed baseline exists
- Why not now:
  - phase 1 still needs a manually understandable baseline before automated memory-design search makes sense

## Batch 2 Summary

- Core now: none beyond already-established first-principles priorities
- Useful now: `Mem0`, `Everything is Context`, `Toward Efficient Agents`
- Carry-forward duplicate: `A-Mem`
- Useful later: `Learning to Continually Learn via Meta-learning Agentic Memory Designs`
- Rejected as irrelevant: none

## Batch 3: Final User-Provided Documents

### 1. Toward Efficient Agents: A Survey of Memory, Tool learning, and Planning

- File: `/Users/bernd/Downloads/2601.14192v1.pdf`
- Verdict: duplicate, carry forward
- Why it matters: this paper was already assessed in Batch 2 and still stands as the main source for a cost-versus-quality evaluation lens.
- New action from this batch:
  - no change in verdict
  - keep using it to shape benchmarking and selective use of heavier memory reasoning

### 2. Memory and the self

- File: `/Users/bernd/Downloads/1-s2.0-S0749596X05000987-main.pdf`
- Verdict: accept, useful now as a first-principles lens
- Why it matters: it frames memory access as being shaped by active goals and introduces the tension between coherence and correspondence.
- Adopt now:
  - make retrieval explicitly goal-conditioned
  - preserve evidence correspondence so the system does not drift into self-justifying but weakly grounded memory
  - treat working state and long-term memory as reciprocal rather than independent
- Keep the caution:
  - this is a cognitive theory paper, not an implementation recipe
  - its value is architectural framing, not a literal software blueprint

### 3. Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models

- File: `/Users/bernd/Downloads/2510.04618v2.pdf`
- Verdict: accept, useful now with caution
- Why it matters: it shows that monolithic context rewriting can cause context collapse, and that richer procedural context can be maintained through structured, incremental updates.
- Adopt now:
  - treat procedural memory as evolving playbooks
  - prefer structured grow / refine / curate flows over rewriting a whole context blob
  - preserve detailed tactics, checks, and failure modes when they remain useful
- Keep the caution:
  - more context is not automatically better
  - detailed playbooks still need retrieval discipline, governance, and protection of the control plane

### 4. StateAct: Enhancing LLM Base Agents via Self-prompting and State-tracking

- File: `/Users/bernd/Downloads/2410.02810v3.pdf`
- Verdict: accept, useful now
- Why it matters: it directly addresses long-horizon goal drift and weak state tracking.
- Adopt now:
  - include an explicit goal reminder in the active-task package
  - include a structured current-state header in prompt assembly
  - keep the next-step context focused on what the agent is trying to do and what the environment currently looks like
- Keep the caution:
  - this is guidance for runtime context construction, not a substitute for durable memory

## Batch 3 Summary

- Useful now: `Memory and the self`, `Agentic Context Engineering`, `StateAct`
- Carry-forward duplicate: `Toward Efficient Agents`
- Rejected as irrelevant: none

## Batch 4: Official Integration Standards

### 1. Model Context Protocol Architecture Overview

- Source: `https://modelcontextprotocol.io/docs/learn/architecture`
- Verdict: accept, useful now
- Why it matters: it makes the host, client, and server split explicit, shows that MCP covers tools, resources, and prompts, and states that remote Streamable HTTP servers commonly serve many clients.
- Adopt now:
  - treat MCP as the primary agent-facing adapter
  - support both local and remote agent integration modes
  - keep the adapter thin over one shared business-logic core

### 2. Model Context Protocol Transports

- Source: `https://modelcontextprotocol.io/specification/2024-11-05/basic/transports`
- Verdict: accept, useful now
- Why it matters: it standardizes the local `stdio` transport and a remote HTTP-based transport for the same JSON-RPC protocol.
- Adopt now:
  - use `stdio` for local sidecar mode
  - use remote HTTP transport for shared service mode
  - avoid separate logic paths for local and remote agent integration

### 3. OpenAPI Specification v3.1.1

- Source: `https://spec.openapis.org/oas/v3.1.1.html`
- Verdict: accept, core now
- Why it matters: it provides a language-agnostic contract format for a stable HTTP API.
- Adopt now:
  - make the canonical MemoryVault service boundary a versioned HTTP and JSON API
  - generate SDKs and tests from the OpenAPI contract where useful

### 4. CloudEvents

- Source: `https://cloudevents.io/`
- Verdict: accept, useful now
- Why it matters: it gives a portable event envelope across services, brokers, and programming languages.
- Adopt now:
  - define asynchronous update and invalidation events in a CloudEvents-style contract
  - keep the event contract broker-neutral

## Batch 5: Public Dataset Access And Shapes

### 1. Hugging Face Dataset Viewer First Rows

- Source: `https://huggingface.co/docs/dataset-viewer/en/first_rows`
- Verdict: accept, useful now
- Why it matters: it documents a stable JSON shape for dataset features and example rows.
- Adopt now:
  - use `first-rows` style payloads as the canonical adapter input shape
  - keep saved row snapshots in the repo for offline tests
  - optionally fetch the same payload shape live when network access is available

### 2. Hugging Face Dataset Cards: TaskBench, SWE-bench Verified, QASPER, ConversationBench

- Sources:
  - `https://huggingface.co/datasets/microsoft/Taskbench`
  - `https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified`
  - `https://huggingface.co/datasets/allenai/qasper`
  - `https://huggingface.co/datasets/arcada-labs/conversation-bench`
- Verdict: accept, useful now
- Why it matters: they expose the real public row fields that MemoryVault needs to turn into interrupted-task onboarding scenarios.
- Adopt now:
  - start with adapters for TaskBench, SWE-bench Verified, and QASPER-style rows
  - keep conversation-style datasets as the next likely expansion path

### 5. NATS JetStream and Key-Value Store

- Sources:
  - `https://docs.nats.io/nats-concepts/jetstream`
  - `https://docs.nats.io/using-nats/developer/develop_jetstream/kv`
- Verdict: accept, useful now
- Why it matters: it is a practical first implementation target for durable async processing, shared cache state, watches, and CAS-style updates.
- Adopt now:
  - treat JetStream as the first likely broker and cache-backplane candidate
  - use its KV semantics as a reference for shared-cache invalidation and coordination
- Keep the caution:
  - the MemoryVault event contract should not depend on JetStream-specific message shapes

### 6. OpenTelemetry Concepts

- Sources:
  - `https://opentelemetry.io/docs/concepts/signals/`
  - `https://opentelemetry.io/docs/concepts/context-propagation/`
- Verdict: accept, useful now
- Why it matters: it gives a common model for traces, metrics, logs, and propagated context across distributed components.
- Adopt now:
  - propagate tenant, workspace, task, session, and run identity through service calls and workers
  - define one observability vocabulary across the service, adapter, and event plane

### 7. RFC 9110

- Source: `https://www.rfc-editor.org/rfc/rfc9110`
- Verdict: accept, useful now
- Why it matters: it defines conditional requests and validators for safe cache revalidation and write protection.
- Adopt now:
  - use ETag on read models such as resume packets
  - use `If-None-Match` for efficient cache validation
  - use `If-Match` to prevent lost updates on mutable task state

## Batch 4 Summary

- Core now: `OpenAPI`
- Useful now: `MCP architecture`, `MCP transports`, `CloudEvents`, `NATS JetStream`, `OpenTelemetry`, `RFC 9110`
- Rejected as irrelevant: none

## Batch 5: Onboarding, Priming, And Graph Bootstrapping

### 1. GraphRAG Auto Prompt Tuning

- Source: `https://microsoft.github.io/graphrag/prompt_tuning/auto_prompt_tuning/`
- Verdict: accept, useful now
- Why it matters: it recommends automatic domain-adapted prompt generation and includes automatic entity-type discovery for broad or varied input.
- Adopt now:
  - use representative-source sampling during onboarding
  - adapt extraction prompts automatically before assuming a hand-authored schema
  - keep entity-type discovery automatic by default for mixed workspaces

### 2. GraphRAG Prompt Tuning Overview

- Source: `https://microsoft.github.io/graphrag/prompt_tuning/overview/`
- Verdict: accept, useful now
- Why it matters: it states that default prompts are the easiest starting point, auto tuning is encouraged, and manual tuning is advanced.
- Adopt now:
  - keep zero-touch onboarding as the primary path
  - treat manual starter-pack edits as optional advanced behavior

### 3. GraphRAG Methods

- Source: `https://microsoft.github.io/graphrag/index/methods/`
- Verdict: accept, useful now with caution
- Why it matters: it explains the trade-off between richer but expensive standard graph extraction and cheaper but noisier fast extraction.
- Adopt now:
  - use a cheap first-pass graph build for onboarding acceleration
  - keep that graph provisional and benchmarked
- Keep the caution:
  - do not let cheap graph extraction define durable control-plane truth

### 4. GraphRAG Bring Your Own Graph

- Source: `https://microsoft.github.io/graphrag/index/byog/`
- Verdict: accept, useful now
- Why it matters: it shows that existing graphs can be integrated without making them mandatory.
- Adopt now:
  - support starter ontologies or custom graphs as optional onboarding hints
  - do not require users to provide them

### 5. Few-NERD

- Source: `https://huggingface.co/datasets/DFKI-SLT/few-nerd`
- Verdict: accept, useful now
- Why it matters: it provides coarse and fine-grained entity labels for evaluating candidate type discovery.
- Adopt now:
  - use it to test onboarding-time type discovery and starter-pack quality

### 6. DocRED

- Source: `https://huggingface.co/datasets/thunlp/docred`
- Verdict: accept, useful now
- Why it matters: it is a practical public benchmark for cross-sentence relation extraction.
- Adopt now:
  - use it to evaluate whether onboarding-time relation induction is useful or too noisy

## Batch 5 Summary

- Useful now: `GraphRAG auto prompt tuning`, `GraphRAG prompt tuning overview`, `GraphRAG methods`, `GraphRAG bring your own graph`, `Few-NERD`, `DocRED`
- Rejected as irrelevant: none

## Batch 6: User-Provided Paper Review

### 1. HyperAgents

- File: `/Users/bernd/Downloads/2603.19461v1.pdf`
- Verdict: accept, useful later and indirectly useful now
- Why it matters: this is not a memory-system design paper, but it does show that persistent memory and performance tracking emerged as reusable self-improvement mechanisms and transferred across task families instead of helping only one benchmark.
- Adopt now:
  - treat performance tracking as part of the memory-learning loop rather than as separate reporting only
  - evaluate whether learned workspace profiles or memory policies transfer across task families
  - keep synthesized improvement insights, not just raw scores, as first-class artifacts in future strategy-learning work
- Adopt later:
  - consider an archive of memory-policy or workspace-profile variants once the current baseline is stable enough to compare them meaningfully
- Do not over-apply:
  - do not pivot MemoryVault into a self-modifying or open-ended evolutionary agent project
  - do not treat this paper as guidance for durable schema design, retrieval design, caching, or multi-agent infrastructure

## Batch 6 Summary

- Useful now in a bounded way: `HyperAgents`
- Rejected as irrelevant: none

## Batch 7: Hindsight Technical Report

### 1. Hindsight is 20/20: Building Agent Memory that Retains, Recalls, and Reflects

- File: `/Users/bernd/Desktop/2512.12818v1.pdf`
- Verdict: accept, useful now with caution
- Why it matters: it gives a concrete pattern for separating source facts, agent experience, derived summaries, and subjective judgments, and it reinforces temporal metadata plus multi-channel retrieval instead of one retrieval path.
- Adopt now:
  - keep source evidence, derived views, and subjective judgments distinct in durable memory
  - treat summaries or entity and task profiles as derived views regenerated from underlying evidence, not as the truth source
  - record both when something happened and when it was recorded when that distinction affects retrieval or auditability
- Adopt later:
  - add multi-channel retrieval that can blend semantic, lexical, graph, and temporal signals for the knowledge plane
- Keep the caution:
  - the experimental write-up still has rough edges, including unresolved `<add>` placeholders and some baseline reuse from outside reports
  - preference-conditioned opinion modeling is not a phase-1 need for MemoryVault; the control plane should stay objective

## Batch 7 Summary

- Useful now with caution: `Hindsight is 20/20`
- Rejected as irrelevant: none
