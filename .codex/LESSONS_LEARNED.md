# Lessons Learned

Last updated: 2026-04-01

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

### When the schema is unclear, interrupted-task misses are better than whiteboard guesses

A small local harness that records runs, resumes work, and scores what was forgotten reveals the real durable-memory needs faster than trying to define the full memory model upfront.

### Keep the final goal visible even before the rest of memory is mature

The goal guard is cheap to preserve and protects against the worst kind of drift while the rest of the memory model is still being learned.

### Promote fields only after they miss repeatedly

The first field promotion should come from evidence across several runs. In the current prototype, assumptions crossed that bar and were added to the resume packet.

### A plain file intake path is enough to start with real tasks

You do not need live session capture before the harness becomes useful. A small JSON trace format is enough to get real or simulated interrupted tasks into the same evaluation loop.

### Tool-first framing avoids locking the memory model too early

If the project is treated like a domain product too soon, it becomes tempting to bake in fields that only fit one kind of work. A tool-first framing keeps the schema provisional until repeated evidence justifies it.

### Synthetic traces and public datasets are enough to start learning

You do not need production data to discover obvious memory gaps. Simulated interrupted traces plus public Hugging Face datasets are enough to start testing and improving the tool.

### Field ablations are more informative than field wish lists

As soon as the tool can remove one memory field at a time and measure the damage, it stops guessing about importance and starts observing it.

### Strict quality gates are cheap while the project is small

Coverage, linting, and Markdown checks are much easier to enforce now than after the repo grows. Set the bar early and keep it there.

### Basic observability is enough to start if it captures timings and counts

You do not need a full telemetry stack to make progress. Local logs plus per-run timing artifacts are enough to support early strategy comparison and debugging.

### Release consistency should be checked automatically, not remembered manually

The release notes and the version file lined up for `0.3.0`, but only because they were handled carefully by hand. A small automated sync check is cheap and prevents future drift.

### MCP is the right agent adapter, not the whole infrastructure contract

MCP is strong where agents need tools, resources, prompts, and transport flexibility. A shared memory system still benefits from one canonical HTTP service boundary underneath it.

### Cache invalidation is part of memory correctness in multi-agent systems

Once more than one agent can read and write the same task state, stale cached control-plane data is a correctness bug, not just a performance issue.

### A hard ontology is a poor default for a tool that is still learning

If the tool is supposed to discover what matters across different kinds of work, a mandatory ontology at onboarding time pushes it toward premature certainty. Soft hints are safer than hard commitments.

### Fast graph bootstrapping is useful only if it stays provisional

### Valid JSON is not enough for a safe write contract

The HTTP boundary should reject request bodies that are valid JSON but not JSON objects, and it should validate nested event and expected-item shapes before the service layer sees them. Otherwise malformed writes turn into confusing runtime errors or accidental mutation tests instead of clear client-facing failures.

### A release gate should be runnable, not only written down

If the repo only describes a future release gate in documents, release week turns into an argument about what the gate was supposed to mean. A small executable gate command keeps the `1.0` promise concrete and makes dry runs possible before a release-candidate line exists.

### A support promise is easier to trust when experimental surfaces are marked in the CLI

Once a release-candidate line exists, it is not enough to say in docs that some commands are still experimental. Marking those commands directly in `--help` output and checking that in the release gate keeps the stable promise obvious and reduces accidental support creep.

### A stable cut needs wording cleanup, not only a version bump

If the repo changes from release candidate to stable, update the command help, gate output, and docs at the same time. Otherwise the version says `1.0.0` while the tool still introduces itself as a rehearsal.

Cheap first-pass graph extraction can make onboarding faster, but it should feed discovery and ranking, not replace explicit goal, plan, and failure memory.

### A narrow learned adaptation is enough to prove the onboarding loop

The first onboarding slice does not need to learn everything. Learning one useful adaptation, then proving it helps on held-out traces, is a much better milestone than generating a broad profile that never changes behavior.

### Representative sampling should stay deterministic

Choosing one trace per domain first and holding the rest out makes the onboarding artifacts reproducible and keeps benchmark results comparable across runs.

### Public-data adapters are safer when tests use saved row snapshots

Using saved Hugging Face row payloads keeps the local quality gate deterministic and fast, while still forcing the adapter code to match real public dataset shapes.

### Learning event labels matters when public traces are not written in our house style

As soon as onboarding can learn markers like `Focus`, `Evidence`, and `Guardrail`, it starts improving held-out scores on public-style traces instead of only on hand-authored examples.

### Cross-family transfer needs a slightly softer gate than same-family onboarding

The first offline transfer benchmark showed a real improvement on a different task family, but it did not hit the stricter onboarding threshold. Transfer checks should still require positive evidence, but they do not need to demand the same absolute score as a same-family held-out gate.

### Profile versions should follow profile contents, not workspace names

If the version is tied to the workspace id, rerunning the same learned profile under a different label looks like a different strategy. A content-based version makes comparison cleaner and makes transfer runs easier to reason about.

### Strategy tracking gets more useful when each run carries reusable aggregates

If the tracker only stores one top-line score per run, every deeper question turns into reopening old benchmark files. Putting category counts, family metrics, and basic cost signals directly on the strategy record makes cross-run summaries cheap, deterministic, and easy to compare.

### Refresh suggestions should stay provisional until the current benchmark agrees

Past successful profiles are useful hints, but they can still overfit old traces or a neighboring task family. The safest refresh loop is: build a candidate from prior evidence, benchmark it on the current held-out traces, and only keep it if the benchmark improves.

### Tracker improvements are only real when they change extraction behavior

It is easy to let the tracker learn richer metadata than the runtime actually uses. That creates the appearance of progress without improving resumed work. The safer rule is: only count a richer signal as implemented when it changes extraction or resume behavior and clears the same held-out benchmark gate as everything else.

### Transfer claims get stronger when the new signal is isolated

If a benchmark only compares "nothing learned" against "everything learned," it is hard to tell which part of the profile actually caused the gain. A cue-disabled comparison is cheap and usually good enough to separate "the profile helped" from "the cue layer specifically helped."
