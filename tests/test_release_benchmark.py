from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from memoryvault.cli import main as cli_main
from memoryvault.onboarding import ArtifactCompatibilityError
from memoryvault.release_benchmark import (
    RELEASE_BENCHMARK_BUNDLE_ID,
    RELEASE_BENCHMARK_BUNDLE_VERSION,
    load_release_benchmark_report,
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

    def test_release_benchmark_report_loader_accepts_legacy_schema_less_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, report = run_release_benchmark(base_dir=temp_dir)
            report_path = run_dir / "release_benchmark_report.json"
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            payload.pop("artifact_schema_version")
            report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

            loaded_report = load_release_benchmark_report(report_path)

            self.assertEqual(loaded_report.bundle_id, report.bundle_id)
            self.assertEqual(loaded_report.passed_case_count, report.passed_case_count)
            self.assertEqual(loaded_report.artifact_schema_version, "release_benchmark_report.v1")

    def test_release_benchmark_report_loader_rejects_unknown_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, _report = run_release_benchmark(base_dir=temp_dir)
            report_path = run_dir / "release_benchmark_report.json"
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            payload["artifact_schema_version"] = "release_benchmark_report.v9"
            report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(ArtifactCompatibilityError, "Unsupported release benchmark report schema"):
                load_release_benchmark_report(report_path)

    def test_release_benchmark_report_loader_rejects_invalid_payload_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, _report = run_release_benchmark(base_dir=temp_dir)
            report_path = run_dir / "release_benchmark_report.json"
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            payload.pop("bundle_id")
            report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(ArtifactCompatibilityError, "not a valid release benchmark report"):
                load_release_benchmark_report(report_path)

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
