from __future__ import annotations

from .models import ExpectedItem, Scenario, TaskEvent


SCENARIOS: dict[str, Scenario] = {
    "bugfix_checkout": Scenario(
        scenario_id="bugfix_checkout",
        title="Resume a checkout bugfix without repeating a bad patch",
        domain="coding",
        goal="Fix the checkout total bug without changing tax rounding.",
        interruption_point="The session stopped after one failed patch and one new discovery.",
        events=[
            TaskEvent(
                sequence=1,
                actor="user",
                text="Goal: Fix the checkout total bug without changing tax rounding.",
            ),
            TaskEvent(
                sequence=2,
                actor="assistant",
                text=(
                    "Plan: Inspect the failing checkout test, trace the total calculation, "
                    "patch the smallest safe place, rerun the failing test."
                ),
            ),
            TaskEvent(
                sequence=3,
                actor="tool",
                text=(
                    "Source: tests/test_checkout.py::test_total_with_coupon failed with "
                    "expected total 41.00 and actual total 43.00."
                ),
                source_refs=["tests/test_checkout.py::test_total_with_coupon"],
            ),
            TaskEvent(
                sequence=4,
                actor="assistant",
                text="Constraint: Do not change tax rounding because other invoices depend on it.",
            ),
            TaskEvent(
                sequence=5,
                actor="assistant",
                text="Attempt: Patched shipping to apply before discount. The patch failed.",
            ),
            TaskEvent(
                sequence=6,
                actor="tool",
                text="Outcome: The checkout test still fails after the shipping patch.",
            ),
            TaskEvent(
                sequence=7,
                actor="assistant",
                text="Lesson: The discount is applied after tax, so the bug is not in shipping.",
            ),
            TaskEvent(
                sequence=8,
                actor="assistant",
                text="Next step: Inspect the discount calculator and coupon order.",
            ),
            TaskEvent(
                sequence=9,
                actor="assistant",
                text="Assumption: The coupon flow and the cart total flow still share one helper.",
            ),
        ],
        expected_items=[
            ExpectedItem(
                name="goal_guard",
                category="goal",
                keywords=["checkout total bug", "tax rounding"],
            ),
            ExpectedItem(
                name="protect_tax_rounding",
                category="constraint",
                keywords=["tax rounding"],
            ),
            ExpectedItem(
                name="remember_failed_patch",
                category="recent_failures",
                keywords=["shipping", "failed"],
            ),
            ExpectedItem(
                name="remember_new_discovery",
                category="lesson",
                keywords=["discount", "after tax"],
            ),
            ExpectedItem(
                name="know_next_step",
                category="current_focus",
                keywords=["discount calculator", "coupon order"],
            ),
            ExpectedItem(
                name="keep_source_link",
                category="source",
                keywords=["tests/test_checkout.py::test_total_with_coupon"],
            ),
            ExpectedItem(
                name="keep_assumption_visible",
                category="assumption",
                keywords=["share one helper"],
            ),
        ],
    ),
    "docs_research": Scenario(
        scenario_id="docs_research",
        title="Resume a document synthesis with grounded sources",
        domain="research",
        goal="Compare two session-memory approaches and write a source-grounded recommendation.",
        interruption_point="The session stopped after one weak draft and a correction about evidence.",
        events=[
            TaskEvent(
                sequence=1,
                actor="user",
                text="Goal: Compare two session-memory approaches and write a source-grounded recommendation.",
            ),
            TaskEvent(
                sequence=2,
                actor="assistant",
                text=(
                    "Plan: Read both design notes, pull the strongest claims with source links, "
                    "write a side-by-side comparison, then make a recommendation."
                ),
            ),
            TaskEvent(
                sequence=3,
                actor="assistant",
                text="Constraint: Separate proven claims from speculation in the final writeup.",
            ),
            TaskEvent(
                sequence=4,
                actor="assistant",
                text="Source: docs/session_memory_a.md says retrieval should happen after a goal reminder.",
                source_refs=["docs/session_memory_a.md"],
            ),
            TaskEvent(
                sequence=5,
                actor="assistant",
                text="Source: docs/session_memory_b.md says raw history must remain available for re-checking.",
                source_refs=["docs/session_memory_b.md"],
            ),
            TaskEvent(
                sequence=6,
                actor="assistant",
                text="Attempt: Drafted a recommendation before pulling quotes. The draft was weak.",
            ),
            TaskEvent(
                sequence=7,
                actor="assistant",
                text="Lesson: The recommendation needs exact source support before any final judgment.",
            ),
            TaskEvent(
                sequence=8,
                actor="assistant",
                text="Decision: Organize the comparison as trade-offs, not as a winner-take-all summary.",
            ),
            TaskEvent(
                sequence=9,
                actor="assistant",
                text="Next step: Build a side-by-side table with claims, evidence, and open questions.",
            ),
            TaskEvent(
                sequence=10,
                actor="assistant",
                text="Assumption: Both documents mean the same thing by session state.",
            ),
        ],
        expected_items=[
            ExpectedItem(
                name="goal_guard",
                category="goal",
                keywords=["source-grounded recommendation"],
            ),
            ExpectedItem(
                name="protect_evidence_boundary",
                category="constraint",
                keywords=["proven claims", "speculation"],
            ),
            ExpectedItem(
                name="remember_weak_draft",
                category="recent_failures",
                keywords=["draft", "weak"],
            ),
            ExpectedItem(
                name="remember_evidence_lesson",
                category="lesson",
                keywords=["exact source support"],
            ),
            ExpectedItem(
                name="keep_structure_decision",
                category="decision",
                keywords=["trade-offs"],
            ),
            ExpectedItem(
                name="know_next_step",
                category="current_focus",
                keywords=["side-by-side table", "open questions"],
            ),
            ExpectedItem(
                name="keep_sources",
                category="source",
                keywords=["docs/session_memory_a.md", "docs/session_memory_b.md"],
            ),
            ExpectedItem(
                name="keep_assumption_visible",
                category="assumption",
                keywords=["same thing", "session state"],
            ),
        ],
    ),
    "feature_rollout": Scenario(
        scenario_id="feature_rollout",
        title="Resume a small feature rollout without breaking compatibility",
        domain="coding",
        goal="Add an export command while keeping the existing output format stable.",
        interruption_point="The session stopped after a compatibility mistake and a corrected plan.",
        events=[
            TaskEvent(
                sequence=1,
                actor="user",
                text="Goal: Add an export command while keeping the existing output format stable.",
            ),
            TaskEvent(
                sequence=2,
                actor="assistant",
                text=(
                    "Plan: Add the new export entry point, reuse the current serializer, "
                    "and verify old consumers still read the same fields."
                ),
            ),
            TaskEvent(
                sequence=3,
                actor="assistant",
                text="Constraint: Do not rename existing JSON fields because downstream tools depend on them.",
            ),
            TaskEvent(
                sequence=4,
                actor="assistant",
                text="Attempt: Renamed created_at to createdAt in the serializer. That broke compatibility.",
            ),
            TaskEvent(
                sequence=5,
                actor="tool",
                text="Outcome: The export smoke check failed because the old parser could not find created_at.",
            ),
            TaskEvent(
                sequence=6,
                actor="assistant",
                text="Decision: Keep the serializer unchanged and add export as a thin wrapper.",
            ),
            TaskEvent(
                sequence=7,
                actor="assistant",
                text="Lesson: Backward compatibility depends on field names, not only on field values.",
            ),
            TaskEvent(
                sequence=8,
                actor="assistant",
                text="Source: smoke-tests/export_consumer.txt documents the expected field names.",
                source_refs=["smoke-tests/export_consumer.txt"],
            ),
            TaskEvent(
                sequence=9,
                actor="assistant",
                text="Next step: Add the export command without touching the serializer output schema.",
            ),
            TaskEvent(
                sequence=10,
                actor="assistant",
                text="Assumption: Only one downstream parser depends on created_at.",
            ),
        ],
        expected_items=[
            ExpectedItem(
                name="goal_guard",
                category="goal",
                keywords=["export command", "output format stable"],
            ),
            ExpectedItem(
                name="protect_compatibility",
                category="constraint",
                keywords=["rename existing JSON fields"],
            ),
            ExpectedItem(
                name="remember_bad_rename",
                category="recent_failures",
                keywords=["created_at", "broke compatibility"],
            ),
            ExpectedItem(
                name="keep_wrapper_decision",
                category="decision",
                keywords=["thin wrapper"],
            ),
            ExpectedItem(
                name="remember_schema_lesson",
                category="lesson",
                keywords=["field names"],
            ),
            ExpectedItem(
                name="know_next_step",
                category="current_focus",
                keywords=["without touching", "serializer output schema"],
            ),
            ExpectedItem(
                name="keep_source_link",
                category="source",
                keywords=["smoke-tests/export_consumer.txt"],
            ),
            ExpectedItem(
                name="keep_assumption_visible",
                category="assumption",
                keywords=["one downstream parser"],
            ),
        ],
    ),
}


def list_scenarios() -> list[Scenario]:
    return list(SCENARIOS.values())


def get_scenario(scenario_id: str) -> Scenario:
    return SCENARIOS[scenario_id]
