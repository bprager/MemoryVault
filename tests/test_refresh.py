from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from memoryvault.cli import main as cli_main
from memoryvault.hf_adapters import load_and_adapt_hf_rows
from memoryvault.models import ExpectedItem, Scenario, TaskEvent
from memoryvault.onboarding import (
    build_workspace_profile,
    refresh_scenarios,
    run_onboarding_benchmark,
    onboard_scenarios,
)


class RefreshLoopTests(unittest.TestCase):
    def test_refresh_reuses_prior_alias_evidence_for_same_workspace(self) -> None:
        seed_scenarios = load_and_adapt_hf_rows("hf_taskbench", "examples/huggingface_rows/taskbench_first_rows.json")
        refresh_scenarios_input = [
            Scenario(
                scenario_id="hf_taskbench_alpha_refresh_sample",
                title="Default-prefix booking note",
                domain="tool_use",
                goal="Keep the customer booking on track.",
                interruption_point="Paused after reading the latest default-format note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the customer booking on track."),
                    TaskEvent(sequence=2, actor="assistant", text="Next step: Recheck the latest booking note."),
                    TaskEvent(sequence=3, actor="assistant", text="Constraint: Stay within the approved budget."),
                    TaskEvent(sequence=4, actor="assistant", text="Source: notes/booking.md"),
                ],
                expected_items=[],
            ),
            Scenario(
                scenario_id="hf_taskbench_omega_refresh_holdout",
                title="Alias-heavy booking note",
                domain="tool_use",
                goal="Keep the customer booking on track.",
                interruption_point="Paused after reading an alias-heavy follow-up note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the customer booking on track."),
                    TaskEvent(sequence=2, actor="assistant", text="Focus: Confirm the room upgrade."),
                    TaskEvent(sequence=3, actor="assistant", text="Guardrail: Stay within the approved budget."),
                    TaskEvent(sequence=4, actor="assistant", text="Evidence: notes/booking.md"),
                ],
                expected_items=[
                    ExpectedItem(
                        name="focus survives",
                        category="current_focus",
                        keywords=["room upgrade"],
                    ),
                    ExpectedItem(
                        name="constraint survives",
                        category="constraint",
                        keywords=["approved budget"],
                    ),
                    ExpectedItem(
                        name="source survives",
                        category="source",
                        keywords=["notes/booking.md"],
                    ),
                ],
            ),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            _run_dir, seed_profile, seed_benchmark = onboard_scenarios(
                seed_scenarios,
                base_dir=temp_dir,
                workspace_id="refresh_workspace",
            )
            self.assertTrue(seed_benchmark.gate_passed)

            initial_profile = build_workspace_profile(
                "refresh_workspace",
                [refresh_scenarios_input[0]],
                [refresh_scenarios_input[1]],
            )
            initial_benchmark = run_onboarding_benchmark(initial_profile, [refresh_scenarios_input[1]])
            self.assertFalse(initial_profile.prefix_aliases)
            self.assertLess(initial_benchmark.adapted_average_score, 1.0)

            run_dir, refreshed_profile, refreshed_benchmark, refresh_report = refresh_scenarios(
                refresh_scenarios_input,
                base_dir=temp_dir,
                workspace_id="refresh_workspace",
            )

            self.assertTrue(run_dir.exists())
            self.assertTrue(refresh_report.candidate_changed)
            self.assertTrue(refresh_report.candidate_accepted)
            self.assertGreaterEqual(refresh_report.relevant_record_count, 1)
            self.assertIn(seed_profile.profile_version, refresh_report.evidence_profile_versions)
            self.assertGreater(
                refreshed_benchmark.adapted_average_score,
                initial_benchmark.adapted_average_score,
            )
            self.assertIn("focus", refreshed_profile.prefix_aliases["current_focus"])
            self.assertIn("guardrail", refreshed_profile.prefix_aliases["constraint"])
            self.assertIn("evidence", refreshed_profile.prefix_aliases["source"])

            refresh_report_payload = json.loads((run_dir / "refresh_report.json").read_text(encoding="utf-8"))
            self.assertEqual(refresh_report_payload["final_profile_version"], refreshed_profile.profile_version)

    def test_refresh_accepts_legacy_schema_less_profiles_and_tracker_records(self) -> None:
        seed_scenarios = load_and_adapt_hf_rows("hf_taskbench", "examples/huggingface_rows/taskbench_first_rows.json")
        refresh_scenarios_input = [
            Scenario(
                scenario_id="hf_taskbench_alpha_refresh_sample",
                title="Default-prefix booking note",
                domain="tool_use",
                goal="Keep the customer booking on track.",
                interruption_point="Paused after reading the latest default-format note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the customer booking on track."),
                    TaskEvent(sequence=2, actor="assistant", text="Next step: Recheck the latest booking note."),
                    TaskEvent(sequence=3, actor="assistant", text="Constraint: Stay within the approved budget."),
                    TaskEvent(sequence=4, actor="assistant", text="Source: notes/booking.md"),
                ],
                expected_items=[],
            ),
            Scenario(
                scenario_id="hf_taskbench_omega_refresh_holdout",
                title="Alias-heavy booking note",
                domain="tool_use",
                goal="Keep the customer booking on track.",
                interruption_point="Paused after reading an alias-heavy follow-up note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the customer booking on track."),
                    TaskEvent(sequence=2, actor="assistant", text="Focus: Confirm the room upgrade."),
                    TaskEvent(sequence=3, actor="assistant", text="Guardrail: Stay within the approved budget."),
                    TaskEvent(sequence=4, actor="assistant", text="Evidence: notes/booking.md"),
                ],
                expected_items=[
                    ExpectedItem(name="focus survives", category="current_focus", keywords=["room upgrade"]),
                    ExpectedItem(name="constraint survives", category="constraint", keywords=["approved budget"]),
                    ExpectedItem(name="source survives", category="source", keywords=["notes/booking.md"]),
                ],
            ),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, seed_profile, seed_benchmark = onboard_scenarios(
                seed_scenarios,
                base_dir=temp_dir,
                workspace_id="refresh_workspace",
            )
            self.assertTrue(seed_benchmark.gate_passed)

            profile_path = run_dir / "workspace_profile.json"
            profile_payload = json.loads(profile_path.read_text(encoding="utf-8"))
            profile_payload.pop("artifact_schema_version")
            profile_path.write_text(json.dumps(profile_payload, indent=2) + "\n", encoding="utf-8")

            tracker_path = Path(temp_dir) / "strategy_tracker.jsonl"
            tracker_payload = json.loads(tracker_path.read_text(encoding="utf-8").strip())
            tracker_payload.pop("artifact_schema_version")
            tracker_path.write_text(json.dumps(tracker_payload) + "\n", encoding="utf-8")

            _refresh_dir, refreshed_profile, _refreshed_benchmark, refresh_report = refresh_scenarios(
                refresh_scenarios_input,
                base_dir=temp_dir,
                workspace_id="refresh_workspace",
            )

            self.assertGreaterEqual(refresh_report.relevant_record_count, 1)
            self.assertIn(seed_profile.profile_version, refresh_report.evidence_profile_versions)
            self.assertIn("focus", refreshed_profile.prefix_aliases["current_focus"])

    def test_refresh_reuses_prior_content_cues_for_unlabeled_notes(self) -> None:
        seed_scenarios = [
            Scenario(
                scenario_id="synthetic_tool_use_alpha_seed",
                title="Seed richer unlabeled cues",
                domain="tool_use",
                goal="Keep the booking request on track without losing its rules.",
                interruption_point="Paused after reading a free-form note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the booking request on track without losing its rules."),
                    TaskEvent(sequence=2, actor="assistant", text="Stay within the approved budget even if the room changes."),
                    TaskEvent(sequence=3, actor="assistant", text="Waiting on the manager approval before confirming the upgrade."),
                    TaskEvent(sequence=4, actor="assistant", text="According to notes/booking.md, the current quote still expires tonight."),
                ],
                expected_items=[
                    ExpectedItem(name="keep budget rule", category="constraint", keywords=["approved budget"]),
                    ExpectedItem(name="keep blocker", category="blocker", keywords=["manager approval"]),
                    ExpectedItem(name="keep source", category="source", keywords=["notes/booking.md"]),
                ],
            ),
            Scenario(
                scenario_id="synthetic_tool_use_omega_seed",
                title="Prove richer unlabeled cues",
                domain="tool_use",
                goal="Keep the booking request on track without losing its rules.",
                interruption_point="Paused after reading the next free-form note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the booking request on track without losing its rules."),
                    TaskEvent(sequence=2, actor="assistant", text="Stay within the approved budget while confirming the late checkout."),
                    TaskEvent(sequence=3, actor="assistant", text="Waiting on the manager approval before locking the upgrade."),
                    TaskEvent(sequence=4, actor="assistant", text="According to notes/booking.md, the late-checkout option is still available."),
                ],
                expected_items=[
                    ExpectedItem(name="keep budget rule", category="constraint", keywords=["approved budget"]),
                    ExpectedItem(name="keep blocker", category="blocker", keywords=["manager approval"]),
                    ExpectedItem(name="keep source", category="source", keywords=["notes/booking.md"]),
                ],
            ),
        ]
        refresh_scenarios_input = [
            Scenario(
                scenario_id="synthetic_tool_use_alpha_refresh",
                title="Default-format booking note",
                domain="tool_use",
                goal="Keep the booking request on track without losing its rules.",
                interruption_point="Paused after reading the default-format note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the booking request on track without losing its rules."),
                    TaskEvent(sequence=2, actor="assistant", text="Next step: Confirm the late checkout."),
                    TaskEvent(sequence=3, actor="assistant", text="Constraint: Stay within the approved budget."),
                    TaskEvent(sequence=4, actor="assistant", text="Source: notes/booking.md"),
                ],
                expected_items=[],
            ),
            Scenario(
                scenario_id="synthetic_tool_use_omega_refresh",
                title="Free-form booking note",
                domain="tool_use",
                goal="Keep the booking request on track without losing its rules.",
                interruption_point="Paused after reading a free-form follow-up note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the booking request on track without losing its rules."),
                    TaskEvent(sequence=2, actor="assistant", text="Stay within the approved budget while confirming the late checkout."),
                    TaskEvent(sequence=3, actor="assistant", text="Waiting on the manager approval before locking the upgrade."),
                    TaskEvent(sequence=4, actor="assistant", text="According to notes/booking.md, the late-checkout option is still available."),
                ],
                expected_items=[
                    ExpectedItem(name="keep budget rule", category="constraint", keywords=["approved budget"]),
                    ExpectedItem(name="keep blocker", category="blocker", keywords=["manager approval"]),
                    ExpectedItem(name="keep source", category="source", keywords=["notes/booking.md"]),
                ],
            ),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            _run_dir, seed_profile, seed_benchmark = onboard_scenarios(
                seed_scenarios,
                base_dir=temp_dir,
                workspace_id="refresh_workspace",
            )
            self.assertTrue(seed_benchmark.gate_passed)
            self.assertIn("according to", seed_profile.cue_phrases["source"])

            initial_profile = build_workspace_profile(
                "refresh_workspace",
                [refresh_scenarios_input[0]],
                [refresh_scenarios_input[1]],
            )
            initial_benchmark = run_onboarding_benchmark(initial_profile, [refresh_scenarios_input[1]])
            self.assertFalse(initial_profile.cue_phrases)
            self.assertLess(initial_benchmark.adapted_average_score, 1.0)

            _run_dir, refreshed_profile, refreshed_benchmark, refresh_report = refresh_scenarios(
                refresh_scenarios_input,
                base_dir=temp_dir,
                workspace_id="refresh_workspace",
            )

            self.assertIn("source", refresh_report.carried_cue_phrases)
            self.assertIn("constraint", refresh_report.carried_cue_phrases)
            self.assertIn("blocker", refresh_report.carried_cue_phrases)
            self.assertIn("according to", refreshed_profile.cue_phrases["source"])
            self.assertGreater(
                refreshed_benchmark.adapted_average_score,
                initial_benchmark.adapted_average_score,
            )
            self.assertTrue(refresh_report.candidate_accepted)

    def test_refresh_without_prior_evidence_keeps_initial_profile(self) -> None:
        scenarios = [
            Scenario(
                scenario_id="hf_taskbench_alpha_refresh_sample",
                title="Default-prefix booking note",
                domain="tool_use",
                goal="Keep the customer booking on track.",
                interruption_point="Paused after reading the latest default-format note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the customer booking on track."),
                    TaskEvent(sequence=2, actor="assistant", text="Next step: Recheck the latest booking note."),
                ],
                expected_items=[],
            ),
            Scenario(
                scenario_id="hf_taskbench_omega_refresh_holdout",
                title="Alias-heavy booking note",
                domain="tool_use",
                goal="Keep the customer booking on track.",
                interruption_point="Paused after reading an alias-heavy follow-up note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the customer booking on track."),
                    TaskEvent(sequence=2, actor="assistant", text="Focus: Confirm the room upgrade."),
                ],
                expected_items=[
                    ExpectedItem(
                        name="focus survives",
                        category="current_focus",
                        keywords=["room upgrade"],
                    )
                ],
            ),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            _run_dir, profile, benchmark, refresh_report = refresh_scenarios(
                scenarios,
                base_dir=temp_dir,
                workspace_id="fresh_workspace",
            )

            self.assertFalse(refresh_report.candidate_changed)
            self.assertFalse(refresh_report.candidate_accepted)
            self.assertEqual(refresh_report.relevant_record_count, 0)
            self.assertEqual(refresh_report.initial_profile_version, profile.profile_version)
            self.assertEqual(refresh_report.final_profile_version, profile.profile_version)
            self.assertEqual(refresh_report.final_adapted_average_score, benchmark.adapted_average_score)

    def test_cli_refresh_hf_file_prints_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            seed_exit_code = cli_main(
                [
                    "onboard-hf-file",
                    "hf_taskbench",
                    "examples/huggingface_rows/taskbench_first_rows.json",
                    "--base-dir",
                    temp_dir,
                    "--workspace-id",
                    "refresh_cli_workspace",
                ]
            )
            self.assertEqual(seed_exit_code, 0)

            buffer = StringIO()
            with redirect_stdout(buffer):
                exit_code = cli_main(
                    [
                        "refresh-hf-file",
                        "hf_taskbench",
                        "examples/huggingface_rows/taskbench_first_rows.json",
                        "--base-dir",
                        temp_dir,
                        "--workspace-id",
                        "refresh_cli_workspace",
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("candidate accepted:", output)
            self.assertIn("evidence records:", output)
            tracker_lines = (Path(temp_dir) / "strategy_tracker.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(tracker_lines), 2)


if __name__ == "__main__":
    unittest.main()
