# Decisions

Last updated: 2026-03-31

## Active Decisions

### 2026-03-24: Add a repo-local `.codex` workspace

- Status: active
- Decision: store persistent agent-facing project memory in `.codex/`.
- Why: it creates a durable place for status, decisions, lessons, and operating instructions across Codex sessions.

### 2026-03-24: Use `AGENTS.md` to enforce `.codex` usage

- Status: active
- Decision: add a root `AGENTS.md` that instructs future Codex sessions to read and maintain `.codex/`.
- Why: creating the files alone is not enough; the repo needs a stable entry point that makes the workflow repeatable.

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

### 2026-03-24: Keep a root changelog in `Changelog.md`

- Status: active
- Decision: maintain a root `Changelog.md` file for notable project changes using the Keep a Changelog structure.
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

### 2026-03-24: Start observability with standard Python logging plus local artifacts

- Status: active
- Decision: add Python `logging` lifecycle messages and per-run JSON observability artifacts before introducing heavier monitoring infrastructure.
- Why: the tool needs enough observability to compare strategies and debug runs, but it is too early to justify a centralized stack.

### 2026-03-24: Enforce release-version sync against `Changelog.md`

- Status: active
- Decision: add a repo-local release check that compares `pyproject.toml` against the latest released version section in `Changelog.md`, and run it in the local quality gate.
- Why: the `0.3.0` release was made consistent by hand, but that alignment should be enforced so future releases do not drift.

### 2026-03-24: Use a canonical HTTP service as the main integration contract

- Status: active
- Decision: treat a versioned HTTP and JSON API, described with OpenAPI, as the source-of-truth service interface for MemoryVault.
- Why: it is the cleanest cross-language and cross-platform contract, and it keeps the core memory rules independent from any single agent host or SDK.

### 2026-03-24: Use MCP as the first-class agent adapter, not the only contract

- Status: active
- Decision: expose MemoryVault to agents through MCP, but implement MCP as a thin adapter over the canonical HTTP service.
- Why: MCP is the strongest current interoperability layer for agent tools and resources, but it is not the best sole boundary for non-agent services, shared infrastructure, or generated SDKs.

### 2026-03-24: Use a broker-neutral event plane for asynchronous work

- Status: active
- Decision: define asynchronous update, invalidation, and rebuild events in a CloudEvents-style contract, with NATS JetStream as the first likely implementation target.
- Why: background memory work, cache invalidation, and fan-out are natural event-driven workflows, but the message contract should stay portable across broker choices.

### 2026-03-24: Make tenancy, concurrency, and caching part of correctness

- Status: active
- Decision: design shared-agent operation around tenant and workspace isolation, optimistic concurrency, short-lived step leases, and explicit cache invalidation.
- Why: once multiple agents share the memory system, concurrency and cache behavior affect correctness just as much as retrieval quality does.

### 2026-03-24: Make onboarding zero-touch by default

- Status: active
- Decision: design the next onboarding release so a new workspace can be initialized without requiring a hand-authored ontology or manual graph preparation.
- Why: mandatory preparation slows adoption, biases the schema too early, and conflicts with the project's tool-first goal.

### 2026-03-24: Treat starter packs as optional soft hints

- Status: active
- Decision: support a generated YAML starter pack for source priority, candidate types, retrieval hints, and benchmark profiles, but keep it optional and regenerable.
- Why: a soft hint layer can speed convergence without turning a hand-maintained file into the truth source.

### 2026-03-24: Use semi-automatic graph creation only as provisional onboarding support

- Status: active
- Decision: use cheap graph bootstrapping and prompt adaptation to accelerate knowledge-plane onboarding, but do not let that provisional graph define control-plane truth.
- Why: graph bootstrapping is useful for candidate structure and clustering, but it is too noisy and indirect to replace explicit task memory.

### 2026-03-24: Start onboarding with representative traces and a held-out gate

- Status: active
- Decision: implement the first onboarding slice by learning a generated workspace profile from representative JSON traces, emitting an optional YAML starter pack, and validating it on held-out traces before trusting it.
- Why: this is the smallest design that proves onboarding can learn from evidence instead of only writing metadata.

### 2026-03-31: Make the `1.0` support promise explicit and executable

- Status: active
- Decision: document the `0.9.x` support promise in the README, PRD, and release plan, and make the release-candidate gate fail if those docs drift or if experimental CLI commands are not marked clearly in help text.
- Why: a release-candidate line is only trustworthy if the stable surface is explicit and the non-contractual surface is clearly separated instead of being left implicit.

### 2026-04-01: Cut `1.0.0` on the smaller local-first boundary

- Status: active
- Decision: ship `1.0.0` around the stable local-first workbench boundary that was rehearsed on `0.9.x`, and keep `python3 -m memoryvault release-candidate-check` as the repo-local release verification command for the stable line.
- Why: the supported HTTP path, verification commands, compatibility rules, and benchmark gate are now implemented, documented, and verified together, while the broader shared-service work is still honestly outside the first stable boundary.

### 2026-03-24: Make failure-marker expansion the first learned onboarding adaptation

- Status: active
- Decision: use the onboarding profile to expand the vocabulary that identifies `recent_failures` in resume packets.
- Why: it creates a measurable held-out improvement with minimal extra complexity and gives the onboarding loop a real effect on task continuity.

### 2026-03-24: Let onboarding learn non-default event labels from representative traces

- Status: active
- Decision: extend the onboarding profile so it can learn alternate event labels such as `Focus`, `Evidence`, and `Guardrail`, and feed those aliases back into candidate extraction.
- Why: public and synthetic traces do not always use the same labels, and learning those patterns creates held-out improvements beyond failure recall.

### 2026-03-24: Use saved Hugging Face row snapshots as the first public-data adapter path

- Status: active
- Decision: implement public dataset adapters around real Hugging Face row shapes, verified locally through saved `first-rows` style fixtures, with an optional dataset-viewer fetch path for live use.
- Why: this keeps tests offline and repeatable while still aligning the adapter layer with real public dataset formats.

### 2026-03-25: Track learned profiles as versioned strategy runs

- Status: active
- Decision: give each learned workspace profile a content-based version, record onboarding and transfer runs in a strategy tracker, and store short improvement notes alongside the run artifacts.
- Why: the project now needs a stable way to compare learned profiles across runs and see whether a change helped, regressed, or only worked in one task family.

### 2026-03-25: Require transfer evidence before calling a learned profile reusable

- Status: active
- Decision: add a transfer benchmark that learns on one task family and scores the learned profile on a different one before treating the profile as broadly useful.
- Why: same-family gains are not enough evidence that the memory behavior is general rather than overfit.

### 2026-03-25: Put category, cost, and lineage signals on each strategy record

- Status: active
- Decision: store improved-category counts, remaining-gap counts, task-family metrics, and basic cost signals directly on each strategy run record so the tracker can build cross-run summaries cheaply and consistently.
- Why: top-level run scores alone are too shallow to show which gains repeat, what they cost, or how learned profiles evolve over time.

### 2026-03-25: Accept refreshed profiles only on current benchmark improvement

- Status: active
- Decision: let the refresh loop carry forward prior successful profile settings as a candidate, but only replace the current profile when the held-out benchmark for the current workspace actually improves.
- Why: prior strategy evidence is useful guidance, but it is not truth; the current workspace still needs proof that the proposed refresh helps rather than merely sounding plausible.

### 2026-03-25: Let onboarding and refresh learn cue phrases from free-form notes

- Status: active
- Decision: extend the workspace profile beyond failure markers and label aliases so it can also learn and refresh short cue phrases from unlabeled notes, then use those cues during extraction.
- Why: tracker evidence was already richer than the runtime behavior. Carrying forward cue phrases closes that gap and lets held-out benchmarks improve source handling and control-state recovery even when traces do not use explicit labels.

### 2026-03-25: Measure cue phrases with a cue-disabled comparison

- Status: active
- Decision: for onboarding and transfer benchmarks, compare the full learned profile against the same profile with cue phrases turned off, then record the cue-only delta and cue-helped categories in the strategy tracker.
- Why: this is the simplest way to tell which cue categories are actually helping and whether those gains transfer across task families, instead of assuming every profile gain came from the cue layer.

### 2026-03-26: Freeze the first release benchmark as an offline public bundle

- Status: active
- Decision: make `python3 -m memoryvault release-benchmark` the fixed `0.5.x` release benchmark command over the saved TaskBench, SWE-bench Verified, QASPER, and conversation-bench fixtures, plus one TaskBench-to-conversation transfer check.
- Why: `0.5.x` needs one repeatable release benchmark contract that stays offline, comparable across runs, and broad enough that no single task family defines release quality by itself.

### 2026-03-26: Put schema markers on saved profile and benchmark artifacts

- Status: active
- Decision: include an explicit `artifact_schema_version` on saved workspace profiles and benchmark report artifacts while keeping the existing content-based `profile_version` for learned profiles.
- Why: the release plan now requires a real compatibility story; schema markers make additive versus breaking changes visible before migration logic exists.

### 2026-03-25: Define `MemoryVault 1.0` as a memory-learning workbench

- Status: active
- Decision: treat `MemoryVault 1.0` as a local-first memory-learning workbench that helps developers learn which memory strategies improve resumed long-running work.
- Why: that boundary matches the implemented repo truthfully, keeps `0.5.0` honest, and avoids pretending the planned shared-service integration already exists.

### 2026-03-27: Put explicit version markers on the first local HTTP slice

- Status: active
- Decision: require the first local HTTP slice to use `api_version: "v1"` in HTTP request and response envelopes, and require saved local task-state files to use `artifact_schema_version: "service_task_state.v1"` with a monotonic `task_version`.
- Why: the first supported integration path needs an explicit compatibility story from the start, not only after outside callers have already started depending on unstable payload shapes.

### 2026-03-30: Keep evidence, derived views, and judgments separate

- Status: active
- Decision: when the durable knowledge-plane schema hardens, tag records as source evidence, derived view, or judgment-like memory, and carry both occurrence time and recorded or updated time when the source allows it.
- Why: the Hindsight paper reinforces an architectural rule that already fits MemoryVault well: the system should be able to tell what it observed from what it inferred, without letting generated summaries quietly replace objective control-plane truth.

### 2026-03-30: Treat schema-less local task files as legacy `v1`

- Status: active
- Decision: load local task-state files without an `artifact_schema_version` as legacy `service_task_state.v1`, but reject unknown schema versions with a clear compatibility error instead of guessing.
- Why: the first local service slice already created saved task files and callers. A narrow legacy default keeps early local artifacts readable while still making real incompatibilities explicit.

### 2026-03-30: Use `If-Match` with `task_version` for the first write precondition

- Status: active
- Decision: support optimistic concurrency on local HTTP writes by accepting `If-Match` with the current `task_version`, and return `412 Precondition Failed` when the write is stale.
- Why: the local service already had monotonic task versions. Reusing that existing version counter is the smallest honest way to prevent lost updates without introducing a second write-token scheme.

### 2026-03-30: Use `Idempotency-Key` for safe local HTTP retries

- Status: active
- Decision: support optional `Idempotency-Key` on local HTTP writes and persist the first result so a retry with the same key and same write returns the original response, while the same key on a different write returns a conflict.
- Why: once optimistic concurrency is in place, the next correctness gap is duplicate retries. Reusing the original result is the smallest local-first way to make retries safe without replaying the write.

### 2026-03-30: Treat schema-less profile, benchmark, and strategy artifacts as legacy `v1`

- Status: active
- Decision: load schema-less `workspace_profile.json`, onboarding benchmark, transfer benchmark, release benchmark report, and strategy record artifacts as legacy current-version files, but reject unknown schema versions with explicit compatibility errors.
- Why: the repo already wrote these artifacts before every loader enforced schema checks. A narrow legacy fallback keeps early local artifacts usable while still making real incompatibilities impossible to miss.

### 2026-03-30: Reject non-object JSON bodies at the HTTP boundary

- Status: active
- Decision: require local HTTP write bodies to be JSON objects, and fail malformed nested event and expected-item payloads before they can reach service-layer mutation logic.
- Why: syntactically valid JSON is not enough for a safe write contract. Boundary validation is cheaper and clearer than letting wrong shapes trigger unhandled runtime errors or partial state changes.

### 2026-03-31: Use one repo-local release-candidate gate for the future `0.9.x` line

- Status: active
- Decision: define the planned `0.9.x` line around one concrete gate command, `python3 -m memoryvault release-candidate-check`, instead of leaving the final `1.0` gate as documentation only.
- Why: a release-candidate phase only matters if the repo can run the same gate repeatedly. Making the gate executable now keeps the later `0.9.x` line honest and reduces the chance that release-week arguments redefine `1.0` on the fly.
