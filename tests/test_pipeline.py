from __future__ import annotations

import io
import json
import runpy
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from memoryvault.cli import main as cli_main
from memoryvault.pipeline import run_demo, run_scenario, run_scenario_file, run_wind_tunnel_file, run_wind_tunnel_scenario
from memoryvault.public_data import list_public_data
from memoryvault.promotion import suggest_durable_fields


class PipelineTests(unittest.TestCase):
    def capture_cli(self, *args: str) -> tuple[int, str]:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = cli_main(list(args))
        return exit_code, buffer.getvalue()

    def test_single_scenario_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, manifest, packet, evaluation = run_scenario("bugfix_checkout", base_dir=temp_dir)

            self.assertTrue(run_dir.exists())
            self.assertEqual(packet.final_goal_guard, manifest.goal)
            self.assertGreaterEqual(evaluation.score, 0.80)

            resume_packet = json.loads((run_dir / "resume_packet.json").read_text(encoding="utf-8"))
            self.assertEqual(resume_packet["final_goal_guard"], manifest.goal)
            self.assertIn("tests/test_checkout.py::test_total_with_coupon", "\n".join(resume_packet["sources"]))

    def test_demo_records_improvements_when_expected_items_are_missed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            results = run_demo(base_dir=temp_dir)

            self.assertEqual(len(results), 3)
            improvement_log = Path(temp_dir) / "improvement_log.jsonl"
            lines = improvement_log.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 3)
            self.assertTrue(any("assumption" in line for line in lines))

    def test_public_data_registry_has_core_benchmark_leads(self) -> None:
        leads = list_public_data()

        self.assertGreaterEqual(len(leads), 6)
        self.assertTrue(any(lead.dataset_id == "hf_taskbench" for lead in leads))
        self.assertTrue(any(lead.dataset_id == "hf_longmemeval_cleaned" for lead in leads))

    def test_imported_trace_runs_through_same_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path("examples/interrupted_runs/swe_bench_like_bugfix.json")
            run_dir, _manifest, packet, evaluation = run_scenario_file(fixture, base_dir=temp_dir)

            self.assertTrue(run_dir.exists())
            self.assertIn("token logic", "\n".join(packet.assumptions))
            self.assertGreaterEqual(evaluation.score, 0.85)

    def test_generic_tool_use_trace_runs_through_same_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path("examples/interrupted_runs/taskbench_like_tool_chain.json")
            run_dir, _manifest, packet, evaluation = run_scenario_file(fixture, base_dir=temp_dir)

            self.assertTrue(run_dir.exists())
            self.assertIn("remain available", "\n".join(packet.assumptions))
            self.assertGreaterEqual(evaluation.score, 0.95)

    def test_cli_commands_cover_main_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            exit_code, output = self.capture_cli("list-scenarios")
            self.assertEqual(exit_code, 0)
            self.assertIn("bugfix_checkout", output)

            exit_code, output = self.capture_cli("list-public-data", "--json")
            self.assertEqual(exit_code, 0)
            self.assertIn("hf_taskbench", output)

            exit_code, output = self.capture_cli("run-scenario", "bugfix_checkout", "--base-dir", temp_dir)
            self.assertEqual(exit_code, 0)
            self.assertIn("resume score", output)

            exit_code, output = self.capture_cli(
                "run-file",
                "examples/interrupted_runs/taskbench_like_tool_chain.json",
                "--base-dir",
                temp_dir,
            )
            self.assertEqual(exit_code, 0)
            self.assertIn("goal guard", output)

            exit_code, output = self.capture_cli(
                "wind-tunnel-file",
                "examples/interrupted_runs/taskbench_like_tool_chain.json",
                "--base-dir",
                temp_dir,
            )
            self.assertEqual(exit_code, 0)
            self.assertIn("fragile fields", output)

            exit_code, output = self.capture_cli("suggest-fields", "--base-dir", temp_dir, "--threshold", "1")
            self.assertEqual(exit_code, 0)
            self.assertIn("suggestions:", output)

    def test_package_main_module_invokes_cli(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer), patch.object(sys, "argv", ["memoryvault", "list-scenarios"]):
            with self.assertRaises(SystemExit) as context:
                runpy.run_module("memoryvault", run_name="__main__")
        self.assertEqual(context.exception.code, 0)
        self.assertIn("bugfix_checkout", buffer.getvalue())

    def test_field_suggestions_promote_repeated_missing_categories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bugfix_fixture = Path("examples/interrupted_runs/swe_bench_like_bugfix.json")
            research_fixture = Path("examples/interrupted_runs/longmemeval_like_research.json")

            run_scenario_file(bugfix_fixture, base_dir=temp_dir)
            run_scenario_file(research_fixture, base_dir=temp_dir)

            suggestions = suggest_durable_fields(temp_dir, threshold=1)

            self.assertTrue(any(item.field_name == "recent_failures" for item in suggestions))
            self.assertTrue(any(item.status == "promote_now" for item in suggestions))

    def test_wind_tunnel_highlights_fragile_fields_for_builtin_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, _manifest, _packet, _evaluation, report = run_wind_tunnel_scenario("bugfix_checkout", base_dir=temp_dir)

            self.assertTrue(run_dir.exists())
            impact_map = {impact.field_name: impact.max_score_delta for impact in report.field_impacts}
            self.assertGreater(impact_map["final_goal_guard"], 0.0)
            self.assertGreater(impact_map["constraints"], 0.0)
            self.assertNotIn("open_questions", impact_map)
            self.assertTrue((run_dir / "wind_tunnel_report.json").exists())

    def test_wind_tunnel_runs_for_imported_trace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path("examples/interrupted_runs/taskbench_like_tool_chain.json")
            run_dir, _manifest, _packet, _evaluation, report = run_wind_tunnel_file(fixture, base_dir=temp_dir)

            self.assertTrue(run_dir.exists())
            self.assertGreaterEqual(report.baseline_score, 0.95)
            self.assertTrue(any(result.variant_id == "goal_only" for result in report.variant_results))


if __name__ == "__main__":
    unittest.main()
