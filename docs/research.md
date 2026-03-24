# Research Summary

Last updated: 2026-03-24

## Purpose

This document is the long-form research summary for MemoryVault. It complements `.codex/RESEARCH.md` and `.codex/RESEARCH_INTAKE.md` with a human-readable record of the papers and whitepapers that most changed the architecture.

The practical question behind every source review has been the same:

- how does the agent keep the goal, plan, constraints, current state, and outcome history intact across long-running work?
- how does it remember more without drifting, collapsing detail, or repeating failures?
- how do we preserve usefulness without letting cost and latency explode?

The current design assumption is that the tool begins without private production traces. That means the research needs to inform not only the memory architecture, but also how to learn and test that architecture with synthetic and public data.

## Combined Lessons That Survived Review

- The highest-priority memory is the active objective, current plan, success criteria, constraints, blockers, and prior outcomes.
- Session history, scratchpads, curated long-term memory, and exact raw history should be separate layers with different lifecycles.
- Retrieval should be goal-conditioned, but durable memory must stay tied to evidence and provenance so the system does not drift into self-confirming stories.
- Long-horizon agents need an explicit goal reminder and a structured current-state header at runtime, not just a large pile of retrieved text.
- Durable declarative memory should use bounded maintenance actions such as add, update, invalidate, and no-op.
- Procedural memory should evolve as curated playbooks that accumulate tactics, checks, and failure-avoidance patterns.
- Monolithic whole-context rewriting is risky because it can collapse rich context into shallow summaries.
- Graph structure is valuable, but phase 1 should use it first for control state, provenance, and relationships, not for maximal knowledge-graph sophistication.
- Evaluation should optimize both usefulness and cost: task success, plan continuity, failure avoidance, token cost, latency, and extra steps.

## Quotes That Most Changed The Design

- [Context Engineering: Sessions, Memory](https://smallake.kr/wp-content/uploads/2025/12/Context-Engineering_-Sessions-Memory.pdf): "the session serves as the temporary workbench" and memory is the "organized filing cabinet."
  - Lesson: keep session state, scratch work, and durable memory separate.
- [Memory and the self](https://doi.org/10.1016/j.jml.2005.08.005): "the working self-modulates access to long-term knowledge."
  - Lesson: retrieval should be shaped by the active goal and current task identity.
- [General Agentic Memory Via Deep Research](https://arxiv.org/abs/2511.18423): "keeping only simple but useful memory" while preserving a "universal page-store."
  - Lesson: use lightweight durable memory plus a searchable raw-history backstop.
- [StateAct](https://arxiv.org/abs/2410.02810): the agent "reminds itself of the goal at every turn."
  - Lesson: active-task context should always restate the goal and structured state.
- [ACE: Agentic Context Engineering](https://arxiv.org/abs/2510.04618): "contexts as evolving playbooks."
  - Lesson: procedural guidance should grow incrementally instead of being repeatedly rewritten from scratch.
- [Mem0](https://arxiv.org/abs/2504.19413): "dynamically extracting, consolidating, and retrieving salient information."
  - Lesson: durable memory needs an explicit maintenance loop.
- [Everything is Context](https://arxiv.org/abs/2512.05470): "persistent, governed infrastructure."
  - Lesson: lineage, access control, and traceability belong in the design from the start.
- [Toward Efficient Agents](https://arxiv.org/abs/2601.14192): "Pareto frontier between effectiveness and cost."
  - Lesson: memory must be judged as a quality-versus-cost trade-off, not only by retrieval quality.

## Source Assessments

### Core Now

- [Context Engineering: Sessions, Memory](https://smallake.kr/wp-content/uploads/2025/12/Context-Engineering_-Sessions-Memory.pdf)
  - Why it matters: best practical framing for splitting session state, memory generation, retrieval timing, provenance, and procedural memory.
  - Carry into MemoryVault: session store plus scratchpad plus durable memory plus raw-history backstop.

- [General Agentic Memory Via Deep Research](https://arxiv.org/abs/2511.18423)
  - Why it matters: strong argument for a complete searchable history behind a lighter memory layer.
  - Carry into MemoryVault: preserve a page-store or raw-history layer; let retrieval plan and search when exact detail matters.
  - Caution: this cannot replace explicit task, plan, and outcome memory.

- [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory](https://arxiv.org/abs/2504.19413)
  - Why it matters: practical memory maintenance pattern with explicit updates instead of naive append-only growth.
  - Carry into MemoryVault: declarative memory should use add, update, invalidate, and no-op style actions.

- [Memory and the self](https://doi.org/10.1016/j.jml.2005.08.005)
  - Why it matters: useful first-principles frame for why active goals should shape memory access.
  - Carry into MemoryVault: retrieval should be goal-conditioned, but still checked against source correspondence and evidence.

### Useful Now

- [StateAct: Enhancing LLM Base Agents via Self-prompting and State-tracking](https://arxiv.org/abs/2410.02810)
  - Why it matters: directly addresses goal drift and long-context failure.
  - Carry into MemoryVault: every active-task prompt package should include an explicit goal reminder and a structured current-state section.

- [ACE: Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models](https://arxiv.org/abs/2510.04618)
  - Why it matters: shows the danger of "context collapse" and the value of structured, incremental updates.
  - Carry into MemoryVault: procedural memory should be curated as evolving playbooks; avoid monolithic whole-context rewrites.
  - Caution: richer context is useful only if retrieval, governance, and control-state prioritization stay intact.

- [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/abs/2502.12110)
  - Why it matters: good pattern for note enrichment, structured attributes, and dynamic linking.
  - Carry into MemoryVault: use for the knowledge plane, especially document and repo memory.
  - Caution: do not let the same free-form evolution rewrite explicit control-plane state.

- [Everything is Context: Agentic File System Abstraction for Context Engineering](https://arxiv.org/abs/2512.05470)
  - Why it matters: reinforces governance, lineage, and explicit handling of memory, tools, and human input.
  - Carry into MemoryVault: keep state transitions auditable and make access control and retention explicit.
  - Caution: we do not need to commit to a literal file-system abstraction in phase 1.

- [Toward Efficient Agents: A Survey of Memory, Tool Learning, and Planning](https://arxiv.org/abs/2601.14192)
  - Why it matters: provides the right evaluation lens for cost-aware agent design.
  - Carry into MemoryVault: benchmark both quality and cost, and prefer hybrid memory management over always invoking heavy reasoning.

- [Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442)
  - Why it matters: observation, planning, and reflection work together; memory is not a stand-alone component.
  - Carry into MemoryVault: connect memory design tightly to planning and reflection instead of treating retrieval as enough.

- [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366)
  - Why it matters: failed attempts become useful only when the agent can reuse them.
  - Carry into MemoryVault: store outcomes, reflections, and failure-avoidance lessons as first-class records.

- [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560)
  - Why it matters: tiered memory is useful when context windows are not enough.
  - Carry into MemoryVault: keep layered memory, but protect active task state in the most accessible durable tier.

- [HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models](https://arxiv.org/abs/2405.14831)
  - Why it matters: graph retrieval and graph ranking can outperform flat retrieval for multi-hop questions.
  - Carry into MemoryVault: add graph-native ranking such as Personalized PageRank after the first deterministic baseline works.

- [From Local to Global: A Graph RAG Approach to Query-Focused Summarization](https://www.microsoft.com/en-us/research/publication/from-local-to-global-a-graph-rag-approach-to-query-focused-summarization/)
  - Why it matters: graph communities and summaries help with large-corpus sensemaking.
  - Carry into MemoryVault: useful for later corpus-level summaries and high-level planning views.

- [A survey on large language model based autonomous agents](https://link.springer.com/article/10.1007/s11704-024-40231-1)
  - Why it matters: confirms that memory and planning are part of one agent loop, not optional add-ons.
  - Carry into MemoryVault: keep memory, planning, and action continuity in one architecture.

### Useful Later Or Indirect

- [HyperGraphRAG: Retrieval-Augmented Generation with Hypergraph-Structured Knowledge Representation for Multi-Hop Reasoning](https://arxiv.org/abs/2503.21322)
  - Why it matters: binary edges can be too weak for complex facts.
  - Carry later: reified fact nodes or hyperedge-style modeling when simple property-graph relations become lossy.

- [Learning to Continually Learn via Meta-learning Agentic Memory Designs](https://arxiv.org/abs/2602.07755)
  - Why it matters: memory design itself may later become learnable.
  - Carry later: keep a stable `update` and `retrieve` boundary so the internals can evolve.

- [Huxley-Godel Machine](https://arxiv.org/abs/2510.21614)
  - Why it matters: local scores can hide worse long-run behavior.
  - Carry later: evaluate MemoryVault by downstream task continuity and long-run task completion, not only local memory scores.

- [MemoryBank: Enhancing Large Language Models with Long-Term Memory](https://arxiv.org/abs/2305.10250)
  - Why it matters: long-term memory and selective forgetting can help sustained interaction.
  - Carry later: selective forgetting may fit low-value episodic detail, but it should not touch active goals, plans, constraints, or failures.

## Architecture Implications For MemoryVault

- Control-plane memory comes first: objective, plan, active step, success criteria, blockers, constraints, decisions, attempts, outcomes, failures, lessons, and source references.
- The tool should begin with near-zero domain assumptions and let repeated misses shape the durable schema over time.
- Session state stays separate from durable memory, and both stay separate from exact raw history.
- Scratchpads and working state are explicit and auditable; they do not become durable memory automatically.
- Prompt assembly should always start with a deterministic task package that includes the goal and current state.
- Declarative memory should use explicit maintenance actions with provenance and confidence.
- Procedural memory should be maintained as evolving playbooks, with structured growth and review instead of whole-playbook rewrites.
- Graph structure should first serve control-state retrieval, provenance, and evidence linkage before more ambitious knowledge modeling.
- Benchmarking should include plan adherence, failure avoidance, task completion, token cost, latency, and extra tool or retrieval steps.
- Until real traces exist, benchmark input should come from synthetic traces and public Hugging Face datasets that can be converted into interrupted-task evaluations.

## Current Bottom Line

The research does not support starting with compression. It supports starting with reliable control-state memory, goal-aware retrieval, explicit state tracking, source-grounded durable memory, and carefully curated procedural playbooks. Compression and richer graph reasoning remain important, but only after the system can already remember what it is trying to do, what has happened so far, and what should happen next.

## Public Benchmark Leads

These public Hugging Face datasets look like strong fits for MemoryVault's evaluation loop because they can be turned into interrupted-task tests instead of only one-shot scores:

- [princeton-nlp/SWE-bench_Verified](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified): public software tasks with clear goals and test-based outcomes.
- [nebius/SWE-agent-trajectories](https://huggingface.co/datasets/nebius/SWE-agent-trajectories): full agent runs with failures, logs, and patches for interrupted-trace replay.
- [microsoft/Taskbench](https://huggingface.co/datasets/microsoft/Taskbench): tool-use planning and dependency graphs across several domains, good for a domain-agnostic tool.
- [xiaowu0162/longmemeval-cleaned](https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned): public long-memory conversational benchmark; the older `longmemeval` dataset is marked deprecated on Hugging Face.
- [arcada-labs/conversation-bench](https://huggingface.co/datasets/arcada-labs/conversation-bench): long-range dialogue, tool use, and memory stress cases.
- [allenai/qasper](https://huggingface.co/datasets/allenai/qasper): source-grounded long-document tasks with evidence.
- [bigbio/multi_xscience](https://huggingface.co/datasets/bigbio/multi_xscience): multi-document synthesis with source relationships.
- [hotpotqa/hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa): multi-hop evidence retrieval with supporting facts.
