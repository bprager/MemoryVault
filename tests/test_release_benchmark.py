from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from memoryvault.cli import main as cli_main
from memoryvault.release_benchmark import (
    RELEASE_BENCHMARK_BUNDLE_ID,
    RELEASE_BENCHMARK_BUNDLE_VERSION,
    run_release_benchmark,
)


class ReleaseBenchmarkTests(unittest.TestCase):
    def test_run_release_benchmark_writes_stable_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, report = run_release_benchmark(base_dir=temp_dir)

            self.assertTrue(run_dir.exists())
            self.assertEqual(report.bundle_id, RELEASE_BENCHMARK_BUNDLE_ID)
            self.assertEqual(report.bundle_version, RELEASE_BENCHMARK_BUNDLE_VERSION)
            self.assertEqual(report.total_case_count, 5)
            self.assertEqual(report.passed_case_count, 5)
            self.assertTrue(report.gate_passed)
            self.assertIn("hf_taskbench", report.task_families)
            self.assertIn("hf_swe_bench_verified", report.task_families)
            self.assertIn("hf_qasper", report.task_families)
            self.assertIn("hf_conversation_bench", report.task_families)
            self.assertTrue((run_dir / "release_benchmark_report.json").exists())

            payload = json.loads((run_dir / "release_benchmark_report.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["artifact_schema_version"], "release_benchmark_report.v1")
            self.assertEqual(payload["required_case_ids"], [item["case_id"] for item in payload["case_results"]])
            self.assertEqual(len(payload["case_results"]), 5)
            self.assertEqual(payload["passed_case_count"], 5)
            self.assertGreater(payload["average_score_delta"], 0.0)

            for case in report.case_results:
                self.assertTrue(Path(case.artifact_dir).exists())
                self.assertGreaterEqual(case.adapted_average_score, case.baseline_average_score)
                self.assertGreater(case.scenario_count, 0)

    def test_cli_release_benchmark_prints_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            buffer = StringIO()
            with redirect_stdout(buffer):
                exit_code = cli_main(["release-benchmark", "--base-dir", temp_dir])

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("bundle: public_release_bundle (0.5.v1)", output)
            self.assertIn("cases passed: 5/5", output)
            self.assertIn("release bundle passed: yes", output)
            self.assertIn("hf_taskbench_to_conversation_transfer", output)


if __name__ == "__main__":
    unittest.main()
