from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from memoryvault.cli import main as cli_main
from memoryvault.importer import load_scenarios_from_directory
from memoryvault.models import ExpectedItem, Scenario, TaskEvent
from memoryvault.onboarding import (
    build_workspace_profile,
    classify_source_ref,
    evaluate_scenario_with_profile,
    onboard_directory,
    render_starter_pack_yaml,
    run_onboarding_benchmark,
    split_representative_sample,
)


class OnboardingTests(unittest.TestCase):
    def test_split_representative_sample_covers_domains_and_holds_out_rest(self) -> None:
        scenarios = load_scenarios_from_directory("examples/onboarding")

        sample, holdout = split_representative_sample(scenarios)

        self.assertEqual(len(sample), 3)
        self.assertEqual(len(holdout), 1)
        self.assertEqual(sorted({scenario.domain for scenario in sample}), ["coding", "research", "tool_use"])
        self.assertEqual(holdout[0].scenario_id, "research_followup_summary")

    def test_onboarding_profile_learns_failure_markers_and_improves_holdout_score(self) -> None:
        scenarios = load_scenarios_from_directory("examples/onboarding")
        sample, holdout = split_representative_sample(scenarios)
        profile = build_workspace_profile("demo_workspace", sample, holdout)

        self.assertIn("weak", profile.failure_markers)
        self.assertIn("unavailable", profile.failure_markers)
        self.assertIn("recent_failures", profile.candidate_fields)
        self.assertIn("taskbench_tool_use", profile.benchmark_profiles)

        baseline = evaluate_scenario_with_profile(holdout[0], failure_markers=None, prefix_aliases=None)
        adapted = evaluate_scenario_with_profile(
            holdout[0],
            failure_markers=profile.failure_markers,
            prefix_aliases=profile.prefix_aliases,
        )

        self.assertLess(baseline.score, adapted.score)
        self.assertIn("recent_failures", baseline.missing_categories)
        self.assertNotIn("recent_failures", adapted.missing_categories)

        benchmark = run_onboarding_benchmark(profile, holdout, gate_threshold=0.9)
        self.assertTrue(benchmark.gate_passed)
        self.assertGreater(benchmark.average_score_delta, 0.1)

    def test_onboarding_profile_learns_content_cues_from_unlabeled_events(self) -> None:
        sample = Scenario(
            scenario_id="synthetic_tool_use_alpha",
            title="Learn richer unlabeled cues",
            domain="tool_use",
            goal="Keep the booking request on track without losing its rules.",
            interruption_point="Paused after reading a free-form note.",
            events=[
                TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the booking request on track without losing its rules."),
                TaskEvent(sequence=2, actor="assistant", text="Before anything else, recheck the room inventory."),
                TaskEvent(sequence=3, actor="assistant", text="Stay within the approved budget even if the room changes."),
                TaskEvent(sequence=4, actor="assistant", text="Waiting on the manager approval before confirming the upgrade."),
                TaskEvent(sequence=5, actor="assistant", text="According to notes/booking.md, the current quote still expires tonight."),
                TaskEvent(sequence=6, actor="assistant", text="So we will send the smaller quote first and hold the upgrade for later."),
                TaskEvent(sequence=7, actor="assistant", text="This means the first draft is not safe to send yet."),
                TaskEvent(sequence=8, actor="assistant", text="It is still unclear whether the manager approved the upgrade."),
            ],
            expected_items=[
                ExpectedItem(name="keep focus", category="current_focus", keywords=["recheck the room inventory"]),
                ExpectedItem(name="keep budget rule", category="constraint", keywords=["approved budget"]),
                ExpectedItem(name="keep blocker", category="blocker", keywords=["manager approval"]),
                ExpectedItem(name="keep source", category="source", keywords=["notes/booking.md"]),
                ExpectedItem(name="keep decision", category="decision", keywords=["smaller quote"]),
                ExpectedItem(name="keep lesson", category="lesson", keywords=["not safe to send"]),
                ExpectedItem(name="keep question", category="open_question", keywords=["manager approved"]),
            ],
        )
        holdout = Scenario(
            scenario_id="synthetic_tool_use_omega",
            title="Use richer unlabeled cues",
            domain="tool_use",
            goal="Keep the booking request on track without losing its rules.",
            interruption_point="Paused after reading the next free-form note.",
            events=[
                TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the booking request on track without losing its rules."),
                TaskEvent(sequence=2, actor="assistant", text="Before anything else, recheck the late-checkout inventory."),
                TaskEvent(sequence=3, actor="assistant", text="Stay within the approved budget while confirming the late checkout."),
                TaskEvent(sequence=4, actor="assistant", text="Waiting on the manager approval before locking the upgrade."),
                TaskEvent(sequence=5, actor="assistant", text="According to notes/booking.md, the late-checkout option is still available."),
                TaskEvent(sequence=6, actor="assistant", text="So we will hold the upgrade and send the smaller quote first."),
                TaskEvent(sequence=7, actor="assistant", text="This means the first offer cannot be trusted yet."),
                TaskEvent(sequence=8, actor="assistant", text="It is still unclear whether the manager approved the upgrade."),
            ],
            expected_items=[
                ExpectedItem(name="keep focus", category="current_focus", keywords=["recheck the late-checkout inventory"]),
                ExpectedItem(name="keep budget rule", category="constraint", keywords=["approved budget"]),
                ExpectedItem(name="keep blocker", category="blocker", keywords=["manager approval"]),
                ExpectedItem(name="keep source", category="source", keywords=["notes/booking.md"]),
                ExpectedItem(name="keep decision", category="decision", keywords=["smaller quote"]),
                ExpectedItem(name="keep lesson", category="lesson", keywords=["cannot be trusted"]),
                ExpectedItem(name="keep question", category="open_question", keywords=["manager approved"]),
            ],
        )

        profile = build_workspace_profile("cue_workspace", [sample], [holdout])
        self.assertIn("before anything else", profile.cue_phrases["current_focus"])
        self.assertIn("stay within", profile.cue_phrases["constraint"])
        self.assertIn("waiting on", profile.cue_phrases["blocker"])
        self.assertIn("according to", profile.cue_phrases["source"])
        self.assertIn("so we will", profile.cue_phrases["decision"])
        self.assertIn("this means", profile.cue_phrases["lesson"])
        self.assertIn("still unclear whether", profile.cue_phrases["open_question"])

        baseline = evaluate_scenario_with_profile(holdout, failure_markers=None, prefix_aliases=None)
        adapted = evaluate_scenario_with_profile(
            holdout,
            failure_markers=None,
            prefix_aliases=None,
            cue_phrases=profile.cue_phrases,
            source_priority_order=profile.source_priority_order,
        )

        self.assertLess(baseline.score, adapted.score)
        self.assertIn("current_focus", baseline.missing_categories)
        self.assertIn("constraint", baseline.missing_categories)
        self.assertIn("source", baseline.missing_categories)
        self.assertIn("decision", baseline.missing_categories)
        self.assertIn("lesson", baseline.missing_categories)
        self.assertIn("open_question", baseline.missing_categories)
        self.assertNotIn("current_focus", adapted.missing_categories)
        self.assertNotIn("constraint", adapted.missing_categories)
        self.assertNotIn("source", adapted.missing_categories)
        self.assertNotIn("decision", adapted.missing_categories)
        self.assertNotIn("lesson", adapted.missing_categories)
        self.assertNotIn("open_question", adapted.missing_categories)

    def test_onboard_directory_writes_profile_starter_pack_and_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, profile, benchmark = onboard_directory(
                "examples/onboarding",
                base_dir=temp_dir,
                workspace_id="synthetic_workspace",
            )

            self.assertTrue(run_dir.exists())
            self.assertEqual(profile.workspace_id, "synthetic_workspace")
            self.assertTrue(benchmark.gate_passed)
            self.assertTrue((run_dir / "workspace_profile.json").exists())
            self.assertTrue((run_dir / "starter_pack.yaml").exists())
            self.assertTrue((run_dir / "onboarding_benchmark.json").exists())
            self.assertTrue((run_dir / "strategy_record.json").exists())
            self.assertTrue((run_dir / "improvement_insights.json").exists())

            observability = json.loads((run_dir / "onboarding_observability.json").read_text(encoding="utf-8"))
            self.assertEqual(observability["workspace_id"], "synthetic_workspace")
            self.assertTrue(observability["gate_passed"])
            self.assertEqual(observability["profile_version"], profile.profile_version)

            tracker_lines = (Path(temp_dir) / "strategy_tracker.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(tracker_lines), 1)
            tracker_record = json.loads(tracker_lines[0])
            self.assertEqual(tracker_record["run_kind"], "onboarding")
            self.assertEqual(tracker_record["profile_version"], profile.profile_version)

            starter_pack = (run_dir / "starter_pack.yaml").read_text(encoding="utf-8")
            self.assertIn("workspace_id: 'synthetic_workspace'", starter_pack)
            self.assertIn(f"profile_version: '{profile.profile_version}'", starter_pack)
            self.assertIn("- 'weak'", starter_pack)

    def test_render_starter_pack_yaml_uses_profile_data(self) -> None:
        scenarios = load_scenarios_from_directory("examples/onboarding")
        sample, holdout = split_representative_sample(scenarios)
        profile = build_workspace_profile("yaml_workspace", sample, holdout)

        yaml_text = render_starter_pack_yaml(profile)

        self.assertIn("workspace_id: 'yaml_workspace'", yaml_text)
        self.assertIn("manual_edits_optional: true", yaml_text)
        self.assertIn("- recent_failures", yaml_text)

    def test_classify_source_ref_prefers_known_authoritative_groups(self) -> None:
        self.assertEqual(classify_source_ref("tests/test_cache.py"), "tests")
        self.assertEqual(classify_source_ref("docs/architecture.md"), "architecture_docs")
        self.assertEqual(classify_source_ref("README.md"), "readme")
        self.assertEqual(classify_source_ref("calendar.rooms.search"), "tool_logs")

    def test_cli_onboard_directory_prints_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            buffer = StringIO()
            with redirect_stdout(buffer):
                exit_code = cli_main(
                    [
                        "onboard-directory",
                        "examples/onboarding",
                        "--base-dir",
                        temp_dir,
                        "--workspace-id",
                        "cli_workspace",
                    ]
                )
            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("gate passed: yes", output)
            self.assertIn("score delta:", output)


if __name__ == "__main__":
    unittest.main()
