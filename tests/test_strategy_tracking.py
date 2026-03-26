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
from memoryvault.onboarding import summarize_strategy_records, transfer_scenarios


class StrategyTrackingTests(unittest.TestCase):
    def test_transfer_benchmark_records_strategy_run_and_insights(self) -> None:
        source_scenarios = load_and_adapt_hf_rows("hf_taskbench", "examples/huggingface_rows/taskbench_first_rows.json")
        target_scenarios = load_and_adapt_hf_rows(
            "hf_conversation_bench",
            "examples/huggingface_rows/conversation_bench_first_rows.json",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, profile, source_benchmark, transfer_benchmark = transfer_scenarios(
                source_scenarios,
                target_scenarios,
                base_dir=temp_dir,
                workspace_id="transfer_workspace",
            )

            self.assertTrue(run_dir.exists())
            self.assertTrue(source_benchmark.gate_passed)
            self.assertTrue(transfer_benchmark.gate_passed)
            self.assertGreaterEqual(transfer_benchmark.average_score_delta, 0.5)
            self.assertEqual(transfer_benchmark.profile_version, profile.profile_version)
            self.assertTrue((run_dir / "transfer_benchmark.json").exists())
            self.assertTrue((run_dir / "strategy_record.json").exists())
            self.assertTrue((run_dir / "improvement_insights.json").exists())

            strategy_record = json.loads((run_dir / "strategy_record.json").read_text(encoding="utf-8"))
            self.assertEqual(strategy_record["run_kind"], "transfer")
            self.assertIn("hf_taskbench", strategy_record["source_task_families"])
            self.assertIn("hf_conversation_bench", strategy_record["evaluation_task_families"])
            self.assertGreater(strategy_record["improved_scenario_count"], 0)
            self.assertTrue(strategy_record["improved_category_counts"])
            self.assertIn("hf_conversation_bench", strategy_record["evaluation_task_family_metrics"])
            self.assertIn("cue_average_score_delta", strategy_record)
            self.assertIn("cue_helped_category_counts", strategy_record)

            tracker_lines = (Path(temp_dir) / "strategy_tracker.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(tracker_lines), 1)

    def test_strategy_summary_reports_cue_transfer_by_category(self) -> None:
        source_scenarios = [
            Scenario(
                scenario_id="synthetic_tool_use_alpha",
                title="Learn cross-family cue patterns",
                domain="tool_use",
                goal="Keep the review package grounded and sequenced.",
                interruption_point="Paused after reading a free-form handoff note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the review package grounded and sequenced."),
                    TaskEvent(sequence=2, actor="assistant", text="Before anything else, recheck the source checklist."),
                    TaskEvent(sequence=3, actor="assistant", text="So we will rebuild the package from the clean spreadsheet."),
                    TaskEvent(sequence=4, actor="assistant", text="This means the earlier draft is not safe to send."),
                    TaskEvent(sequence=5, actor="assistant", text="According to docs/review.md, the final packet still needs the signed cover page."),
                ],
                expected_items=[
                    ExpectedItem(name="keep focus", category="current_focus", keywords=["source checklist"]),
                    ExpectedItem(name="keep decision", category="decision", keywords=["clean spreadsheet"]),
                    ExpectedItem(name="keep lesson", category="lesson", keywords=["not safe to send"]),
                    ExpectedItem(name="keep source", category="source", keywords=["docs/review.md"]),
                ],
            ),
            Scenario(
                scenario_id="synthetic_tool_use_omega",
                title="Prove cross-family cue patterns",
                domain="tool_use",
                goal="Keep the review package grounded and sequenced.",
                interruption_point="Paused after reading the next free-form note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Keep the review package grounded and sequenced."),
                    TaskEvent(sequence=2, actor="assistant", text="Before anything else, recheck the delivery checklist."),
                    TaskEvent(sequence=3, actor="assistant", text="So we will send the smaller packet first."),
                    TaskEvent(sequence=4, actor="assistant", text="This means the first version cannot be trusted."),
                    TaskEvent(sequence=5, actor="assistant", text="According to docs/review.md, the signed cover page is still missing."),
                ],
                expected_items=[
                    ExpectedItem(name="keep focus", category="current_focus", keywords=["delivery checklist"]),
                    ExpectedItem(name="keep decision", category="decision", keywords=["smaller packet"]),
                    ExpectedItem(name="keep lesson", category="lesson", keywords=["cannot be trusted"]),
                    ExpectedItem(name="keep source", category="source", keywords=["docs/review.md"]),
                ],
            ),
        ]
        target_scenarios = [
            Scenario(
                scenario_id="synthetic_research_transfer",
                title="Transfer cue patterns into research work",
                domain="research",
                goal="Finish the evidence-grounded memo without drifting.",
                interruption_point="Paused after reading a research follow-up note.",
                events=[
                    TaskEvent(sequence=1, actor="assistant", text="Goal: Finish the evidence-grounded memo without drifting."),
                    TaskEvent(sequence=2, actor="assistant", text="Before anything else, recheck the evidence table."),
                    TaskEvent(sequence=3, actor="assistant", text="So we will rewrite the findings from the verified rows."),
                    TaskEvent(sequence=4, actor="assistant", text="This means the old summary cannot be trusted."),
                    TaskEvent(sequence=5, actor="assistant", text="According to docs/evidence.md, the disputed claim still lacks a citation."),
                ],
                expected_items=[
                    ExpectedItem(name="keep focus", category="current_focus", keywords=["evidence table"]),
                    ExpectedItem(name="keep decision", category="decision", keywords=["verified rows"]),
                    ExpectedItem(name="keep lesson", category="lesson", keywords=["cannot be trusted"]),
                    ExpectedItem(name="keep source", category="source", keywords=["docs/evidence.md"]),
                ],
            )
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            _run_dir, _profile, _source_benchmark, transfer_benchmark = transfer_scenarios(
                source_scenarios,
                target_scenarios,
                base_dir=temp_dir,
                workspace_id="cue_transfer_workspace",
            )

            self.assertGreater(transfer_benchmark.cue_average_score_delta, 0.0)

            summary = summarize_strategy_records(temp_dir)
            source_summary = next(item for item in summary.category_summaries if item.category == "source")
            focus_summary = next(item for item in summary.category_summaries if item.category == "current_focus")
            self.assertGreater(source_summary.cue_helped_scenario_count, 0)
            self.assertGreater(focus_summary.cue_helped_scenario_count, 0)
            self.assertIn("synthetic_research", source_summary.helped_task_families)
            self.assertGreater(source_summary.cue_average_score_delta, 0.0)

    def test_strategy_summary_combines_onboarding_and_transfer_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_main(
                [
                    "onboard-directory",
                    "examples/onboarding",
                    "--base-dir",
                    temp_dir,
                    "--workspace-id",
                    "summary_workspace",
                ]
            )
            cli_main(
                [
                    "transfer-hf-files",
                    "hf_taskbench",
                    "examples/huggingface_rows/taskbench_first_rows.json",
                    "hf_conversation_bench",
                    "examples/huggingface_rows/conversation_bench_first_rows.json",
                    "--base-dir",
                    temp_dir,
                    "--workspace-id",
                    "summary_transfer",
                ]
            )

            summary = summarize_strategy_records(temp_dir)

            self.assertEqual(summary.total_records, 2)
            self.assertEqual(sorted(item.run_kind for item in summary.run_kind_summaries), ["onboarding", "transfer"])
            self.assertIn("hf_taskbench", summary.task_families)
            self.assertIn("hf_conversation_bench", summary.task_families)
            self.assertIsNotNone(summary.latest_profile_version)
            self.assertTrue(any(item.helped_scenario_count > 0 for item in summary.category_summaries))
            self.assertTrue(any(item.task_family == "hf_conversation_bench" for item in summary.task_family_summaries))
            self.assertGreaterEqual(len(summary.profile_summaries), 2)
            self.assertGreaterEqual(len(summary.workspace_lineages), 2)
            onboarding_summary = next(item for item in summary.run_kind_summaries if item.run_kind == "onboarding")
            self.assertGreaterEqual(onboarding_summary.gate_pass_rate, 1.0)
            self.assertGreater(onboarding_summary.average_duration_per_scenario_ms, 0.0)

    def test_cli_transfer_and_strategy_summary_print_human_readable_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            buffer = StringIO()
            with redirect_stdout(buffer):
                exit_code = cli_main(
                    [
                        "transfer-hf-files",
                        "hf_taskbench",
                        "examples/huggingface_rows/taskbench_first_rows.json",
                        "hf_conversation_bench",
                        "examples/huggingface_rows/conversation_bench_first_rows.json",
                        "--base-dir",
                        temp_dir,
                        "--workspace-id",
                        "cli_transfer_workspace",
                    ]
                )
            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("transfer gate passed: yes", output)
            self.assertIn("target score delta:", output)
            self.assertIn("cue-only delta:", output)

            buffer = StringIO()
            with redirect_stdout(buffer):
                exit_code = cli_main(["summarize-strategies", "--base-dir", temp_dir])
            self.assertEqual(exit_code, 0)
            summary_output = buffer.getvalue()
            self.assertIn("records: 1", summary_output)
            self.assertIn("run kinds:", summary_output)
            self.assertIn("transfer:", summary_output)
            self.assertIn("recurring wins:", summary_output)
            self.assertIn("cue transfer:", summary_output)
            self.assertIn("task family results:", summary_output)
            self.assertIn("profile history:", summary_output)
            self.assertIn("workspace lineages:", summary_output)


if __name__ == "__main__":
    unittest.main()
