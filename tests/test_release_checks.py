from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from memoryvault.cli import build_parser
from memoryvault.models import ReleaseBenchmarkCaseResult, ReleaseBenchmarkReport
from memoryvault.release_checks import (
    PRODUCT_IDENTITY_PHRASE,
    ReleaseConsistencyError,
    ensure_version_sync,
    read_latest_release_version,
    read_project_version,
    run_release_candidate_gate,
)


class ReleaseCheckTests(unittest.TestCase):
    def _write_release_candidate_repo(self, temp_path: Path, *, include_identity_in_readme: bool = True) -> None:
        (temp_path / "docs").mkdir(parents=True, exist_ok=True)
        (temp_path / "scripts").mkdir(parents=True, exist_ok=True)
        (temp_path / "memoryvault").mkdir(parents=True, exist_ok=True)

        identity_line = PRODUCT_IDENTITY_PHRASE if include_identity_in_readme else "different identity"
        readme_lines = [
            f"MemoryVault is a {identity_line}.",
            "python3 -m memoryvault serve-http --host 127.0.0.1 --port 8765",
            "POST /v1/events",
            "PUT /v1/tasks/{task_id}/state",
            "GET /v1/tasks/{task_id}/resume-packet",
            "POST /v1/tasks/{task_id}/retrieve",
            "## Current `1.0` support promise",
            "python3 -m memoryvault release-benchmark",
            "python3 -m memoryvault release-candidate-check",
            "## Experimental And Non-Contractual",
        ]
        (temp_path / "README.md").write_text("\n".join(readme_lines) + "\n", encoding="utf-8")
        (temp_path / "docs" / "PRD.md").write_text(
            "\n".join(
                [
                    f"MemoryVault 1.0 is a {PRODUCT_IDENTITY_PHRASE}.",
                    "one local HTTP service",
                    "Current `1.0` support promise",
                    "python3 -m memoryvault release-benchmark",
                    "python3 -m memoryvault release-candidate-check",
                    "Experimental And Non-Contractual",
                    "artifact_schema_version",
                    "legacy current-version files",
                    "unknown schema versions",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (temp_path / "docs" / "release_plan.md").write_text(
            "\n".join(
                [
                    f"MemoryVault 1.0 is a {PRODUCT_IDENTITY_PHRASE}.",
                    "POST /v1/events",
                    "PUT /v1/tasks/{task_id}/state",
                    "GET /v1/tasks/{task_id}/resume-packet",
                    "POST /v1/tasks/{task_id}/retrieve",
                    "Current `1.0` support promise",
                    "python3 -m memoryvault release-benchmark",
                    "python3 -m memoryvault release-candidate-check",
                    "Experimental And Non-Contractual",
                    "artifact_schema_version",
                    "legacy current-version files",
                    "unknown schema versions",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (temp_path / "scripts" / "check_quality.sh").write_text(
            "\n".join(
                [
                    "ruff check memoryvault tests scripts",
                    "python3 -m mypy memoryvault tests",
                    "python3 scripts/markdown_lint.py README.md docs .codex",
                    "python3 scripts/check_version_sync.py",
                    "python3 -m coverage report --fail-under=95 -m",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (temp_path / "pyproject.toml").write_text(
            '[project]\nname = "memoryvault"\nversion = "1.0.0"\n',
            encoding="utf-8",
        )
        (temp_path / "Changelog.md").write_text(
            "# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2026-04-01\n",
            encoding="utf-8",
        )
        (temp_path / "memoryvault" / "http_api.py").write_text("# stub\n", encoding="utf-8")
        (temp_path / "memoryvault" / "service.py").write_text("# stub\n", encoding="utf-8")
        (temp_path / "memoryvault" / "cli.py").write_text(
            "\n".join(
                [
                    "from __future__ import annotations",
                    "",
                    "import argparse",
                    "",
                    "def build_parser() -> argparse.ArgumentParser:",
                    '    parser = argparse.ArgumentParser()',
                    '    subparsers = parser.add_subparsers(dest="command", required=True)',
                    '    subparsers.add_parser("list-scenarios", help="Experimental: list scenarios")',
                    '    subparsers.add_parser("list-public-data", help="Experimental: list public data")',
                    '    subparsers.add_parser("list-hf-adapters", help="Experimental: list adapters")',
                    '    subparsers.add_parser("run-scenario", help="Experimental: run built-in scenario")',
                    '    subparsers.add_parser("demo", help="Experimental: run demo scenarios")',
                    '    subparsers.add_parser("wind-tunnel-scenario", help="Experimental: run built-in wind tunnel")',
                    '    subparsers.add_parser("onboard-hf-file", help="Experimental: onboard hf file")',
                    '    subparsers.add_parser("refresh-hf-file", help="Experimental: refresh hf file")',
                    '    subparsers.add_parser("onboard-hf-first-rows", help="Experimental: onboard fetched rows")',
                    '    subparsers.add_parser("transfer-hf-files", help="Experimental: transfer hf files")',
                    '    subparsers.add_parser("release-benchmark", help="release benchmark")',
                    '    subparsers.add_parser("release-candidate-check", help="release candidate check")',
                    '    subparsers.add_parser("serve-http", help="serve http")',
                    '    return parser',
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def _fake_release_report(self) -> ReleaseBenchmarkReport:
        return ReleaseBenchmarkReport(
            bundle_id="public_release_bundle",
            bundle_version="0.5.v1",
            project_version="1.0.0",
            created_at="2026-04-01T00:00:00+00:00",
            report_dir="/tmp/release-run",
            required_case_ids=[
                "hf_taskbench_onboarding",
                "hf_swe_bench_verified_onboarding",
                "hf_qasper_onboarding",
                "hf_conversation_bench_onboarding",
                "hf_taskbench_to_conversation_transfer",
            ],
            task_families=[
                "hf_taskbench",
                "hf_swe_bench_verified",
                "hf_qasper",
                "hf_conversation_bench",
            ],
            total_case_count=5,
            passed_case_count=5,
            baseline_average_score=0.4,
            cue_disabled_average_score=0.6,
            adapted_average_score=0.9,
            average_score_delta=0.5,
            cue_average_score_delta=0.3,
            gate_passed=True,
            case_results=[
                ReleaseBenchmarkCaseResult(
                    case_id="hf_taskbench_onboarding",
                    title="TaskBench",
                    run_kind="onboarding",
                    profile_version="v1",
                    artifact_dir="/tmp/case",
                    source_task_families=["hf_taskbench"],
                    evaluation_task_families=["hf_taskbench"],
                    scenario_count=2,
                    improved_scenario_count=2,
                    baseline_average_score=0.4,
                    cue_disabled_average_score=0.6,
                    adapted_average_score=1.0,
                    average_score_delta=0.6,
                    cue_average_score_delta=0.4,
                    gate_threshold=0.9,
                    gate_passed=True,
                    recommended_actions=[],
                )
                for _ in range(5)
            ],
        )

    def test_ensure_version_sync_accepts_matching_latest_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "pyproject.toml").write_text(
                '[project]\nname = "memoryvault"\nversion = "0.3.0"\n',
                encoding="utf-8",
            )
            (temp_path / "Changelog.md").write_text(
                "# Changelog\n\n## [Unreleased]\n\n## [0.3.0] - 2026-03-24\n",
                encoding="utf-8",
            )

            version = ensure_version_sync(temp_path / "pyproject.toml", temp_path / "Changelog.md")

            self.assertEqual(version, "0.3.0")

    def test_ensure_version_sync_rejects_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "pyproject.toml").write_text(
                '[project]\nname = "memoryvault"\nversion = "0.4.0"\n',
                encoding="utf-8",
            )
            (temp_path / "Changelog.md").write_text(
                "# Changelog\n\n## [Unreleased]\n\n## [0.3.0] - 2026-03-24\n",
                encoding="utf-8",
            )

            with self.assertRaises(ReleaseConsistencyError):
                ensure_version_sync(temp_path / "pyproject.toml", temp_path / "Changelog.md")

    def test_read_latest_release_version_skips_unreleased(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            changelog_path = Path(temp_dir) / "Changelog.md"
            changelog_path.write_text(
                "# Changelog\n\n## [Unreleased]\n\n## [0.3.1] - 2026-03-24\n\n## [0.3.0] - 2026-03-23\n",
                encoding="utf-8",
            )

            version = read_latest_release_version(changelog_path)

            self.assertEqual(version, "0.3.1")

    def test_read_project_version_rejects_missing_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject_path = Path(temp_dir) / "pyproject.toml"
            pyproject_path.write_text('[project]\nname = "memoryvault"\n', encoding="utf-8")

            with self.assertRaises(ReleaseConsistencyError):
                read_project_version(pyproject_path)

    def test_read_latest_release_version_rejects_missing_release_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            changelog_path = Path(temp_dir) / "Changelog.md"
            changelog_path.write_text("# Changelog\n\n## [Unreleased]\n", encoding="utf-8")

            with self.assertRaises(ReleaseConsistencyError):
                read_latest_release_version(changelog_path)

    def test_run_release_candidate_gate_accepts_consistent_repo_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._write_release_candidate_repo(temp_path)

            with patch(
                "memoryvault.release_benchmark.run_release_benchmark",
                return_value=(temp_path / "artifacts" / "run-1", self._fake_release_report()),
            ):
                report = run_release_candidate_gate(
                    repo_root=temp_path,
                    benchmark_base_dir="artifacts",
                    run_benchmark=True,
                )

            self.assertTrue(report.passed)
            self.assertTrue(report.benchmark_ran)
            self.assertIsNotNone(report.benchmark_artifact_path)
            self.assertTrue(all(check.passed for check in report.checks))

    def test_run_release_candidate_gate_reports_missing_identity_phrase(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._write_release_candidate_repo(temp_path, include_identity_in_readme=False)

            report = run_release_candidate_gate(
                repo_root=temp_path,
                benchmark_base_dir="artifacts",
                run_benchmark=False,
            )

            self.assertFalse(report.passed)
            self.assertFalse(report.benchmark_ran)
            identity_check = next(check for check in report.checks if check.name == "product_identity")
            self.assertFalse(identity_check.passed)
            self.assertIn("README.md", identity_check.details)

    def test_run_release_candidate_gate_reports_missing_integration_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._write_release_candidate_repo(temp_path)
            (temp_path / "memoryvault" / "service.py").unlink()

            report = run_release_candidate_gate(repo_root=temp_path, run_benchmark=False)

            surface_check = next(check for check in report.checks if check.name == "supported_integration_surface")
            self.assertFalse(surface_check.passed)
            self.assertIn("memoryvault/service.py", surface_check.details)

    def test_run_release_candidate_gate_reports_missing_endpoint_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._write_release_candidate_repo(temp_path)
            (temp_path / "docs" / "release_plan.md").write_text(
                f"MemoryVault 1.0 is a {PRODUCT_IDENTITY_PHRASE}.\nserve-http\nartifact_schema_version\nlegacy current-version files\nunknown schema versions\n",
                encoding="utf-8",
            )

            report = run_release_candidate_gate(repo_root=temp_path, run_benchmark=False)

            surface_check = next(check for check in report.checks if check.name == "supported_integration_surface")
            self.assertFalse(surface_check.passed)
            self.assertIn("POST /v1/events", surface_check.details)

    def test_run_release_candidate_gate_reports_missing_compatibility_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._write_release_candidate_repo(temp_path)
            (temp_path / "docs" / "PRD.md").write_text(
                f"MemoryVault 1.0 is a {PRODUCT_IDENTITY_PHRASE}.\none local HTTP service\n",
                encoding="utf-8",
            )

            report = run_release_candidate_gate(repo_root=temp_path, run_benchmark=False)

            compatibility_check = next(check for check in report.checks if check.name == "compatibility_story")
            self.assertFalse(compatibility_check.passed)
            self.assertIn("compatibility rules", compatibility_check.details)

    def test_run_release_candidate_gate_reports_missing_quality_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._write_release_candidate_repo(temp_path)
            (temp_path / "scripts" / "check_quality.sh").unlink()

            report = run_release_candidate_gate(repo_root=temp_path, run_benchmark=False)

            quality_check = next(check for check in report.checks if check.name == "quality_gate")
            self.assertFalse(quality_check.passed)
            self.assertIn("missing scripts/check_quality.sh", quality_check.details)

    def test_run_release_candidate_gate_reports_incomplete_quality_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._write_release_candidate_repo(temp_path)
            (temp_path / "scripts" / "check_quality.sh").write_text("ruff check memoryvault tests scripts\n", encoding="utf-8")

            report = run_release_candidate_gate(repo_root=temp_path, run_benchmark=False)

            quality_check = next(check for check in report.checks if check.name == "quality_gate")
            self.assertFalse(quality_check.passed)
            self.assertIn("mypy", quality_check.details)

    def test_run_release_candidate_gate_reports_incomplete_loader_set(self) -> None:
        import memoryvault.onboarding as onboarding

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._write_release_candidate_repo(temp_path)
            original_name = onboarding.load_transfer_benchmark.__name__
            onboarding.load_transfer_benchmark.__name__ = onboarding.load_workspace_profile.__name__
            try:
                report = run_release_candidate_gate(repo_root=temp_path, run_benchmark=False)
            finally:
                onboarding.load_transfer_benchmark.__name__ = original_name

            compatibility_check = next(check for check in report.checks if check.name == "compatibility_story")
            self.assertFalse(compatibility_check.passed)
            self.assertIn("not all core artifact loaders", compatibility_check.details)

    def test_run_release_candidate_gate_reports_missing_support_promise_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._write_release_candidate_repo(temp_path)
            (temp_path / "README.md").write_text(
                f"MemoryVault is a {PRODUCT_IDENTITY_PHRASE}.\npython3 -m memoryvault serve-http --host 127.0.0.1 --port 8765\n",
                encoding="utf-8",
            )

            report = run_release_candidate_gate(repo_root=temp_path, run_benchmark=False)

            support_check = next(check for check in report.checks if check.name == "support_promise")
            self.assertFalse(support_check.passed)
            self.assertIn("support-promise", support_check.details)

    def test_run_release_candidate_gate_reports_missing_experimental_cli_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._write_release_candidate_repo(temp_path)

            parser = build_parser()
            subparsers_action = next(action for action in parser._actions if hasattr(action, "_choices_actions"))
            for action in getattr(subparsers_action, "_choices_actions", []):
                if action.dest == "list-scenarios":
                    action.help = "list scenarios"
                    break

            with patch("memoryvault.cli.build_parser", return_value=parser):
                report = run_release_candidate_gate(repo_root=temp_path, run_benchmark=False)

            support_check = next(check for check in report.checks if check.name == "support_promise")
            self.assertFalse(support_check.passed)
            self.assertIn("list-scenarios", support_check.details)


if __name__ == "__main__":
    unittest.main()
