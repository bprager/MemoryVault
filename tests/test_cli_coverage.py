from __future__ import annotations

import io
import json
import runpy
import tempfile
import unittest
import argparse
from contextlib import redirect_stdout
from unittest.mock import Mock
from unittest.mock import patch

from memoryvault.cli import (
    build_parser,
    _print_strategy_summary,
    _print_wind_tunnel_summary,
    main as cli_main,
)
from memoryvault.hf_adapters import load_and_adapt_hf_rows
from memoryvault.models import (
    StrategyCategorySummary,
    StrategyTrackerSummary,
    WindTunnelReport,
    WindTunnelVariantResult,
)
from memoryvault.release_checks import ReleaseCandidateGateReport, ReleaseGateCheck


class CliCoverageTests(unittest.TestCase):
    def capture_cli(self, *args: str) -> tuple[int, str]:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = cli_main(list(args))
        return exit_code, buffer.getvalue()

    def test_cli_covers_remaining_command_paths_and_json_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            exit_code, output = self.capture_cli("list-scenarios", "--json")
            self.assertEqual(exit_code, 0)
            scenarios = json.loads(output)
            self.assertTrue(any(item["scenario_id"] == "bugfix_checkout" for item in scenarios))

            exit_code, output = self.capture_cli("list-public-data")
            self.assertEqual(exit_code, 0)
            self.assertIn("focus:", output)
            self.assertIn("url:", output)

            exit_code, output = self.capture_cli("list-hf-adapters")
            self.assertEqual(exit_code, 0)
            self.assertIn("hf_taskbench", output)
            self.assertIn("default split:", output)

            exit_code, output = self.capture_cli("list-hf-adapters", "--json")
            self.assertEqual(exit_code, 0)
            adapters = json.loads(output)
            self.assertTrue(any(item["adapter_id"] == "hf_conversation_bench" for item in adapters))

            exit_code, output = self.capture_cli("demo", "--base-dir", temp_dir)
            self.assertEqual(exit_code, 0)
            self.assertIn("resume score:", output)
            self.assertIn("improvements:", output)

            exit_code, output = self.capture_cli("wind-tunnel-scenario", "bugfix_checkout", "--base-dir", temp_dir)
            self.assertEqual(exit_code, 0)
            self.assertIn("variant damage:", output)

            exit_code, output = self.capture_cli("refresh-directory", "examples/onboarding", "--base-dir", temp_dir)
            self.assertEqual(exit_code, 0)
            self.assertIn("candidate accepted:", output)
            self.assertIn("final profile version:", output)

            exit_code, output = self.capture_cli(
                "transfer-directory",
                "examples/onboarding",
                "examples/onboarding",
                "--base-dir",
                temp_dir,
            )
            self.assertEqual(exit_code, 0)
            self.assertIn("transfer gate passed:", output)
            self.assertIn("target score delta:", output)

            exit_code, output = self.capture_cli("suggest-fields", "--base-dir", temp_dir, "--threshold", "1", "--json")
            self.assertEqual(exit_code, 0)
            suggestions = json.loads(output)
            self.assertTrue(any(item["field_name"] == "recent_failures" for item in suggestions))

            exit_code, output = self.capture_cli("suggest-fields", "--base-dir", temp_dir, "--threshold", "1")
            self.assertEqual(exit_code, 0)
            self.assertIn("source category:", output)
            self.assertIn("why:", output)

            exit_code, output = self.capture_cli("summarize-strategies", "--base-dir", temp_dir, "--json")
            self.assertEqual(exit_code, 0)
            summary = json.loads(output)
            self.assertGreaterEqual(summary["total_records"], 2)

            exit_code, output = self.capture_cli("release-benchmark", "--base-dir", temp_dir, "--json")
            self.assertEqual(exit_code, 0)
            report = json.loads(output)
            self.assertEqual(report["total_case_count"], 5)
            self.assertTrue(report["gate_passed"])

    def test_cli_onboard_hf_first_rows_uses_fetch_path(self) -> None:
        scenarios = load_and_adapt_hf_rows("hf_taskbench", "examples/huggingface_rows/taskbench_first_rows.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("memoryvault.cli.fetch_and_adapt_hf_rows", return_value=scenarios) as mock_fetch:
                exit_code, output = self.capture_cli(
                    "onboard-hf-first-rows",
                    "hf_taskbench",
                    "--rows",
                    "4",
                    "--base-dir",
                    temp_dir,
                )

        self.assertEqual(exit_code, 0)
        self.assertIn("workspace: hf_taskbench_workspace", output)
        self.assertIn("gate passed: yes", output)
        mock_fetch.assert_called_once_with(
            "hf_taskbench",
            config=None,
            split=None,
            length=4,
            token=None,
        )

    def test_cli_serve_http_invokes_local_server(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("memoryvault.cli.run_http_server") as mock_run_server:
                exit_code, output = self.capture_cli(
                    "serve-http",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8877",
                    "--base-dir",
                    temp_dir,
                )

        self.assertEqual(exit_code, 0)
        self.assertIn("serving: http://127.0.0.1:8877", output)
        mock_run_server.assert_called_once_with(host="127.0.0.1", port=8877, base_dir=temp_dir)

    def test_cli_release_candidate_check_reports_gate_result(self) -> None:
        report = ReleaseCandidateGateReport(
            project_version="1.0.0",
            release_line="1.0.x",
            benchmark_ran=False,
            benchmark_artifact_path="/tmp/release-benchmark-report.json",
            checks=[
                ReleaseGateCheck(name="product_identity", passed=True, details="docs agree"),
                ReleaseGateCheck(name="supported_integration_surface", passed=True, details="surface is present"),
            ],
            passed=True,
        )

        with patch("memoryvault.cli.run_release_candidate_gate", return_value=report) as mock_gate:
            exit_code, output = self.capture_cli("release-candidate-check", "--skip-benchmark")

        self.assertEqual(exit_code, 0)
        self.assertIn("release line: 1.0.x", output)
        self.assertIn("gate passed: yes", output)
        self.assertIn("benchmark artifact: /tmp/release-benchmark-report.json", output)
        self.assertIn("- product_identity: pass", output)
        mock_gate.assert_called_once_with(benchmark_base_dir="var/memoryvault", run_benchmark=False)

    def test_cli_release_candidate_check_supports_json_and_failure_exit(self) -> None:
        report = ReleaseCandidateGateReport(
            project_version="1.0.0",
            release_line="1.0.x",
            benchmark_ran=False,
            benchmark_artifact_path=None,
            checks=[ReleaseGateCheck(name="quality_gate", passed=False, details="missing coverage")],
            passed=False,
        )

        with patch("memoryvault.cli.run_release_candidate_gate", return_value=report):
            exit_code, output = self.capture_cli("release-candidate-check", "--skip-benchmark", "--json")

        self.assertEqual(exit_code, 1)
        payload = json.loads(output)
        self.assertFalse(payload["passed"])
        self.assertEqual(payload["checks"][0]["name"], "quality_gate")

    def test_cli_unknown_command_path_returns_error_code(self) -> None:
        fake_parser = Mock()
        fake_parser.parse_args.return_value = type(
            "Args",
            (),
            {"command": "not-real", "log_level": "WARNING", "log_file": None},
        )()
        fake_parser.error = Mock()

        with patch("memoryvault.cli.build_parser", return_value=fake_parser):
            exit_code = cli_main([])

        self.assertEqual(exit_code, 2)
        fake_parser.error.assert_called_once_with("unknown command: not-real")

    def test_cli_module_main_invokes_entrypoint(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            with patch("sys.argv", ["memoryvault.cli", "list-scenarios", "--json"]):
                with self.assertRaises(SystemExit) as exc:
                    runpy.run_module("memoryvault.cli", run_name="__main__")

        self.assertEqual(exc.exception.code, 0)
        self.assertIn("bugfix_checkout", buffer.getvalue())

    def test_cli_help_marks_experimental_commands_clearly(self) -> None:
        parser = build_parser()
        subparsers_action = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
        help_by_command = {
            action.dest: action.help or ""
            for action in getattr(subparsers_action, "_choices_actions", [])
        }

        self.assertTrue(help_by_command["list-scenarios"].startswith("Experimental:"))
        self.assertTrue(help_by_command["onboard-hf-file"].startswith("Experimental:"))
        self.assertFalse(help_by_command["serve-http"].startswith("Experimental:"))

    def test_print_helpers_cover_empty_states(self) -> None:
        empty_summary = StrategyTrackerSummary(
            total_records=0,
            latest_profile_version=None,
            task_families=[],
            run_kind_summaries=[],
            category_summaries=[],
            task_family_summaries=[],
            profile_summaries=[],
            workspace_lineages=[],
        )
        cue_only_summary = StrategyTrackerSummary(
            total_records=1,
            latest_profile_version="v1",
            task_families=[],
            run_kind_summaries=[],
            category_summaries=[
                StrategyCategorySummary(
                    category="source",
                    helped_run_count=0,
                    helped_scenario_count=0,
                    remaining_gap_run_count=0,
                    remaining_gap_scenario_count=0,
                    cue_helped_run_count=1,
                    cue_helped_scenario_count=1,
                    cue_average_score_delta=0.25,
                    helped_task_families=[],
                )
            ],
            task_family_summaries=[],
            profile_summaries=[],
            workspace_lineages=[],
        )
        report = WindTunnelReport(
            run_id="run-1",
            scenario_id="scenario-1",
            baseline_score=1.0,
            baseline_missing_categories=[],
            variant_results=[
                WindTunnelVariantResult(
                    variant_id="goal_only",
                    description="Keep only the goal guard.",
                    removed_fields=["constraints"],
                    is_composite=False,
                    score=0.75,
                    score_delta=0.25,
                    failed_check_names=["keep constraints"],
                    missing_categories=["constraint"],
                )
            ],
            field_impacts=[],
            most_fragile_fields=[],
        )

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            _print_strategy_summary(empty_summary)
            _print_strategy_summary(cue_only_summary)
            _print_wind_tunnel_summary("/tmp/run-1", "Keep the task on track.", report)

        output = buffer.getvalue()
        self.assertIn("task families:\n- none", output)
        self.assertIn("cue transfer:\n- source: cue helped in 1 runs / 1 scenarios, cue delta 0.25, families none", output)
        self.assertIn("fragile fields:\n- none", output)


if __name__ == "__main__":
    unittest.main()
