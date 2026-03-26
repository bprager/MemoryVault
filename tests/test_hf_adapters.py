from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from memoryvault.cli import main as cli_main
from memoryvault.hf_adapters import (
    fetch_hf_first_rows,
    list_hf_adapters,
    load_and_adapt_hf_rows,
)
from memoryvault.onboarding import build_workspace_profile, evaluate_scenario_with_profile, run_onboarding_benchmark, split_representative_sample


class HuggingFaceAdapterTests(unittest.TestCase):
    def test_list_hf_adapters_returns_supported_public_datasets(self) -> None:
        adapters = list_hf_adapters()

        self.assertTrue(any(adapter.adapter_id == "hf_taskbench" for adapter in adapters))
        self.assertTrue(any(adapter.adapter_id == "hf_swe_bench_verified" for adapter in adapters))
        self.assertTrue(any(adapter.adapter_id == "hf_qasper" for adapter in adapters))
        self.assertTrue(any(adapter.adapter_id == "hf_conversation_bench" for adapter in adapters))

    def test_taskbench_rows_adapt_into_onboarding_scenarios(self) -> None:
        scenarios = load_and_adapt_hf_rows("hf_taskbench", "examples/huggingface_rows/taskbench_first_rows.json")

        self.assertEqual(len(scenarios), 4)
        self.assertEqual(scenarios[0].domain, "tool_use")
        self.assertTrue(any(event.text.startswith("Focus:") for event in scenarios[0].events))
        self.assertTrue(any(event.text.startswith("Evidence:") for event in scenarios[0].events))

    def test_public_data_onboarding_learns_prefix_aliases_and_improves_holdout(self) -> None:
        scenarios = load_and_adapt_hf_rows("hf_taskbench", "examples/huggingface_rows/taskbench_first_rows.json")
        sample, holdout = split_representative_sample(scenarios)
        profile = build_workspace_profile("hf_taskbench_workspace", sample, holdout)

        self.assertIn("current_focus", profile.prefix_aliases)
        self.assertIn("focus", profile.prefix_aliases["current_focus"])
        self.assertIn("source", profile.prefix_aliases)
        self.assertIn("evidence", profile.prefix_aliases["source"])
        self.assertIn("constraint", profile.prefix_aliases)
        self.assertIn("guardrail", profile.prefix_aliases["constraint"])

        baseline = evaluate_scenario_with_profile(holdout[0], failure_markers=None, prefix_aliases=None)
        adapted = evaluate_scenario_with_profile(
            holdout[0],
            failure_markers=profile.failure_markers,
            prefix_aliases=profile.prefix_aliases,
        )

        self.assertLess(baseline.score, adapted.score)
        self.assertIn("current_focus", baseline.missing_categories)
        self.assertIn("constraint", baseline.missing_categories)
        self.assertIn("source", baseline.missing_categories)
        self.assertNotIn("current_focus", adapted.missing_categories)
        self.assertNotIn("constraint", adapted.missing_categories)
        self.assertNotIn("source", adapted.missing_categories)

        benchmark = run_onboarding_benchmark(profile, holdout, gate_threshold=0.9)
        self.assertTrue(benchmark.gate_passed)
        self.assertGreater(benchmark.average_score_delta, 0.5)

    def test_qasper_and_swe_bench_rows_adapt_cleanly(self) -> None:
        qasper = load_and_adapt_hf_rows("hf_qasper", "examples/huggingface_rows/qasper_first_rows.json")
        swe = load_and_adapt_hf_rows("hf_swe_bench_verified", "examples/huggingface_rows/swe_bench_verified_first_rows.json")

        self.assertEqual(qasper[0].domain, "research")
        self.assertEqual(swe[0].domain, "coding")
        self.assertTrue(any(item.category == "source" for item in qasper[0].expected_items))
        self.assertTrue(any(item.category == "constraint" for item in swe[0].expected_items))

    def test_conversation_bench_rows_adapt_cleanly(self) -> None:
        conversation = load_and_adapt_hf_rows(
            "hf_conversation_bench",
            "examples/huggingface_rows/conversation_bench_first_rows.json",
        )

        self.assertEqual(conversation[0].domain, "conversation")
        self.assertTrue(any(event.text.startswith("Guardrail:") for event in conversation[0].events))
        self.assertTrue(any(item.category == "constraint" for item in conversation[0].expected_items))
        self.assertTrue(any(item.category == "source" for item in conversation[0].expected_items))

    def test_fetch_hf_first_rows_uses_dataset_viewer_response_shape(self) -> None:
        payload = {
            "rows": [
                {
                    "row_idx": 0,
                    "row": {
                        "id": "tb_remote",
                        "instruction": "Schedule the shuttle after checking the route.",
                        "tool_steps": ["Step 1: Check the route.", "Step 2: Schedule the shuttle."],
                    },
                }
            ]
        }

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
                return None

            def read(self) -> bytes:
                return json.dumps(payload).encode("utf-8")

        with patch("memoryvault.hf_adapters.urlopen", return_value=FakeResponse()) as mock_urlopen:
            rows = fetch_hf_first_rows("hf_taskbench", length=1)

        self.assertEqual(rows[0]["id"], "tb_remote")
        mock_urlopen.assert_called_once()

    def test_cli_onboard_hf_file_runs_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            buffer = StringIO()
            with redirect_stdout(buffer):
                exit_code = cli_main(
                    [
                        "onboard-hf-file",
                        "hf_taskbench",
                        "examples/huggingface_rows/taskbench_first_rows.json",
                        "--base-dir",
                        temp_dir,
                        "--workspace-id",
                        "hf_cli_workspace",
                    ]
                )
            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("workspace: hf_cli_workspace", output)
            self.assertIn("gate passed: yes", output)

    def test_cli_onboard_conversation_hf_file_runs_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            buffer = StringIO()
            with redirect_stdout(buffer):
                exit_code = cli_main(
                    [
                        "onboard-hf-file",
                        "hf_conversation_bench",
                        "examples/huggingface_rows/conversation_bench_first_rows.json",
                        "--base-dir",
                        temp_dir,
                        "--workspace-id",
                        "conversation_cli_workspace",
                    ]
                )
            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("workspace: conversation_cli_workspace", output)
            self.assertIn("gate passed: yes", output)


if __name__ == "__main__":
    unittest.main()
