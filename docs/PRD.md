# MemoryVault product requirements

Last updated: 2026-03-24

## Summary

MemoryVault is a local-first memory layer for long-running AI work.

Its job is simple: help an agent stay on the same task until the work is done.

The system is meant to preserve the parts that agents tend to lose first:

- the active goal
- the current plan and step status
- constraints, decisions, blockers, and open questions
- attempts, outcomes, failures, and lessons
- links back to the code, documents, notes, and raw history those records came from

MemoryVault is not being built as a generic note store. It is being built to keep work on track.

## Problem

Large language models are good at local reasoning and weak at long-running continuity.

In real work this shows up in a few predictable ways:

- the prompt fills up and older but important context falls out
- repeated summaries wash out technical detail
- similarity search finds related text but misses structure, authority, and sequence
- the agent forgets what has already been tried
- the agent loses the current plan, or drifts away from it
- decisions and constraints stop shaping later steps

This hurts software and research work more than casual chat. One missed constraint, one forgotten failed attempt, or one lost source reference can waste hours.

## Product goal

Give an agent a stable working memory that survives across sessions and helps it answer the same six questions every time:

1. What am I trying to finish?
2. What is the current plan?
3. What step am I on right now?
4. What constraints and decisions still apply?
5. What already happened, including failures?
6. Where did this information come from?

If MemoryVault does that reliably, it is doing its job.

## Who this is for

### Primary user

An AI agent doing long-running technical work, especially coding, research, and multi-step problem solving.

### Secondary user

A developer or operator who needs to inspect the agent's state, verify where a memory came from, and correct bad drift before it turns into wasted work.

## Product principles

- Task state comes before broad recall.
- Source links matter. Memory without traceability is not enough.
- Short-term work, durable memory, and raw history should stay separate.
- A good memory system should help the agent avoid repeating failed work.
- Compression is useful, but it should not come before reliable task-state retrieval.
- The system should stay local-first and inspectable.

## What the product must do

### 1. Preserve task state

MemoryVault must store and retrieve:

- the active task
- the plan and active step
- success criteria
- blockers and open questions
- constraints and decisions
- recent attempts, outcomes, failures, and lessons

This is the minimum working memory for long-running agent work.

### 2. Keep different kinds of memory separate

The product needs distinct layers for:

- session state: the live workbench for one conversation or run
- scratchpad: temporary notes and intermediate reasoning
- durable memory: curated records worth keeping
- raw history: the exact source material for re-checking or rehydration

These layers should be linked, but they should not be collapsed into one blob.

### 3. Keep source and trust information

High-value memory items must keep:

- source references
- provenance
- confidence or trust signals
- time or freshness metadata where it matters

The system should be able to point back to the source of a memory instead of asking the model to "just remember."

### 4. Understand relationships

The product should keep relationships between:

- tasks and plan steps
- files and symbols
- documents and sections
- decisions and the components they affect
- attempts and outcomes
- summaries and the source material they compress

This is why a graph-backed design is part of the current direction.

### 5. Support exact recovery

When a compressed or summarized memory is not enough, the system must be able to recover the underlying detail from raw history or source material.

### 6. Stay useful under cost limits

MemoryVault should improve continuity without creating runaway cost.

Success is not only better recall. Success is better recall at a reasonable token, latency, and retrieval cost.

## What the product should not do in v1

- It should not try to solve every memory problem at once.
- It should not start with aggressive compression as the first implementation target.
- It should not depend on a blank database. The current Memgraph target is shared.
- It should not turn every piece of temporary reasoning into durable memory.
- It should not hide important state inside free-form summaries.
- It should not optimize for benchmark scores that look good but break long-run continuity.

## Phase 1 scope

Phase 1 should prove that the basic memory loop works.

That means:

- one active task can be stored and resumed
- the plan and step status can be retrieved reliably
- constraints, decisions, failures, and lessons persist across sessions
- the system can link those records back to real sources
- the runtime context always includes the goal and current state before wider retrieval
- the design stays safely isolated inside the shared Memgraph instance on `odin:7697`

If phase 1 cannot do those things, later compression work is premature.

## Success measures

MemoryVault is succeeding when:

- the agent keeps the same goal and plan across long-running work
- the agent stops repeating failures that are already in memory
- important constraints survive long enough to affect later steps
- high-value memories can be traced back to the source that supports them
- the system beats naive prompt history and naive summaries on continuity
- the memory layer adds bounded cost instead of uncontrolled overhead

## Current scope boundaries

The repo is still in planning.

Today the project already has:

- a detailed design note
- a research summary
- a reviewed architecture direction
- a verified Memgraph target

Today the project does not yet have:

- a production memory pipeline
- a working Memgraph integration in the codebase
- a benchmark harness
- a real user-facing workflow beyond the placeholder script

## Open product questions

- What belongs in Memgraph and what should stay in files or object storage?
- How should procedural playbooks be reviewed, updated, and retired?
- How much human curation should be required before durable memory changes?
- What is the right default boundary between fast retrieval and deeper rehydration?
- How should importance, freshness, and confidence be combined for ranking?

## Short version

MemoryVault exists to stop long-running AI work from falling apart when the prompt gets long.

It should help an agent remember the goal, keep the plan, respect constraints, learn from failure, and show where its memory came from.
