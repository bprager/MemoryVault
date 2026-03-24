# Lessons Learned

Last updated: 2026-03-24

## Current Lessons

### Keep planned and implemented states separate

The repo already contains a detailed system design, but the executable code is still minimal. Mixing those two states would quickly create confusion.

### Persistent memory only works if it is wired into the workflow

Creating context files is not enough. A repo-local instruction file must point future Codex sessions at `.codex/` and require maintenance.

### Hidden files may be swallowed by global Git ignore rules

`AGENTS.md` and `.codex/` can disappear from normal Git status output if they are ignored globally. Add explicit unignore rules in the repo's `.gitignore` so the project memory stays visible and trackable.

### Shared graph infrastructure changes the design immediately

If the target graph is already populated, namespace isolation is not cleanup work for later. It is part of the first design decision.

### Semantic memory without task state is not enough

An agent can retrieve relevant facts and still fail if it loses the objective, current plan, blockers, or evidence from previous failures. Those need first-class storage.

### Sessions, durable memory, and raw history solve different problems

The workbench for one live conversation is not the same thing as long-term memory, and neither is the same thing as an exact raw history store for rehydration. Keeping them separate makes the design clearer.

### Scratchpads should not silently become memory

Temporary reasoning artifacts are valuable for audit and debugging, but they should only be promoted to durable memory after validation.

### Dynamic memory evolution is useful, but not everywhere

Allowing knowledge-plane notes to gain links or improved summaries is promising. Letting the same mechanism silently rewrite explicit task state would be risky.

### Immediate scores can hide long-run failure

A local metric may reward something that looks good now but causes worse downstream behavior later. Evaluation needs to track long-run task success, failure avoidance, and plan continuity.

### Forgetting is not uniformly good

Selective forgetting may help with low-value episodic detail, but active goals, constraints, accepted plans, and failure history should be treated as durable memory.

### Cheap rules and expensive reasoning should work together

Pure rule-based memory management is blunt, and pure LLM-based management is expensive. The practical path is usually a hybrid.

### Goal drift is a real failure mode, not a prompt nit

Long-running agents stay more reliable when the active objective and current structured state are restated explicitly instead of being left implicit in long context.

### Whole-context rewriting can erase the very detail we need

Repeatedly asking a model to rewrite an accumulated context risks context collapse. Incremental curation of structured notes or playbooks is safer.

### Goal-focused retrieval still needs evidence guardrails

It is useful to let the active goal shape what memory is retrieved, but durable memory should stay tied to sources and provenance so the agent does not rationalize its way into false continuity.

### Short, high-signal notes beat long session dumps

The `.codex` files should make the next task easier, not turn into unsearchable logs.
