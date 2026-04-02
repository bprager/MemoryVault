from __future__ import annotations

import argparse
from dataclasses import dataclass
import re
from pathlib import Path
from typing import Iterable


VERSION_PATTERN = re.compile(r'^version\s*=\s*"(?P<version>\d+\.\d+\.\d+)"\s*$')
CHANGELOG_RELEASE_PATTERN = re.compile(r"^## \[(?P<version>\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}$")
PRODUCT_IDENTITY_PHRASE = "local-first memory-learning workbench"
SUPPORTED_HTTP_ENDPOINTS = (
    "POST /v1/events",
    "PUT /v1/tasks/{task_id}/state",
    "GET /v1/tasks/{task_id}/resume-packet",
    "POST /v1/tasks/{task_id}/retrieve",
)
QUALITY_GATE_FRAGMENTS = (
    "ruff check",
    "mypy",
    "markdown_lint.py",
    "check_version_sync.py",
    "coverage report --fail-under=95",
)
SUPPORT_PROMISE_HEADINGS = (
    "Current `1.0` support promise",
    "Experimental And Non-Contractual",
)
SUPPORTED_VERIFICATION_COMMANDS = (
    "python3 -m memoryvault release-benchmark",
    "python3 -m memoryvault release-candidate-check",
)
EXPERIMENTAL_COMMANDS = (
    "list-scenarios",
    "list-public-data",
    "list-hf-adapters",
    "run-scenario",
    "demo",
    "wind-tunnel-scenario",
    "onboard-hf-file",
    "refresh-hf-file",
    "onboard-hf-first-rows",
    "transfer-hf-files",
)


class ReleaseConsistencyError(ValueError):
    """Raised when release metadata is missing or inconsistent."""


@dataclass(frozen=True, slots=True)
class ReleaseGateCheck:
    name: str
    passed: bool
    details: str


@dataclass(frozen=True, slots=True)
class ReleaseCandidateGateReport:
    project_version: str
    release_line: str
    benchmark_ran: bool
    benchmark_artifact_path: str | None
    checks: list[ReleaseGateCheck]
    passed: bool


def read_project_version(pyproject_path: str | Path = "pyproject.toml") -> str:
    path = Path(pyproject_path)
    for line in path.read_text(encoding="utf-8").splitlines():
        match = VERSION_PATTERN.match(line.strip())
        if match:
            return match.group("version")
    raise ReleaseConsistencyError(f"project version not found in {path.as_posix()}")


def read_latest_release_version(changelog_path: str | Path = "Changelog.md") -> str:
    path = Path(changelog_path)
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CHANGELOG_RELEASE_PATTERN.match(line.strip())
        if match:
            return match.group("version")
    raise ReleaseConsistencyError(f"no released version entry found in {path.as_posix()}")


def ensure_version_sync(
    pyproject_path: str | Path = "pyproject.toml",
    changelog_path: str | Path = "Changelog.md",
) -> str:
    project_version = read_project_version(pyproject_path)
    changelog_version = read_latest_release_version(changelog_path)
    if project_version != changelog_version:
        raise ReleaseConsistencyError(
            "version mismatch: "
            f"pyproject.toml has {project_version} but {Path(changelog_path).as_posix()} has {changelog_version}"
        )
    return project_version


def run_release_candidate_gate(
    *,
    repo_root: str | Path = ".",
    benchmark_base_dir: str | Path = "var/memoryvault",
    run_benchmark: bool = True,
) -> ReleaseCandidateGateReport:
    root = Path(repo_root)
    project_version = ensure_version_sync(root / "pyproject.toml", root / "Changelog.md")

    checks = [
        _check_product_identity(root),
        _check_supported_integration_surface(root),
        _check_support_promise(root),
        _check_compatibility_story(root),
        _check_quality_gate_definition(root),
        _check_release_benchmark_definition(),
    ]

    benchmark_artifact_path: str | None = None
    if run_benchmark:
        benchmark_check, benchmark_artifact_path = _check_release_benchmark_execution(
            root=root,
            benchmark_base_dir=benchmark_base_dir,
        )
        checks.append(benchmark_check)

    return ReleaseCandidateGateReport(
        project_version=project_version,
        release_line=_release_line_for_version(project_version),
        benchmark_ran=run_benchmark,
        benchmark_artifact_path=benchmark_artifact_path,
        checks=checks,
        passed=all(check.passed for check in checks),
    )


def _release_line_for_version(version: str) -> str:
    major, minor, _patch = version.split(".")
    return f"{major}.{minor}.x"


def _check_product_identity(root: Path) -> ReleaseGateCheck:
    missing_paths: list[str] = []
    for relative_path in ("README.md", "docs/PRD.md", "docs/release_plan.md"):
        if PRODUCT_IDENTITY_PHRASE not in _read_text(root / relative_path):
            missing_paths.append(relative_path)

    if missing_paths:
        return ReleaseGateCheck(
            name="product_identity",
            passed=False,
            details="missing identity phrase in: " + ", ".join(missing_paths),
        )

    return ReleaseGateCheck(
        name="product_identity",
        passed=True,
        details=f"README, PRD, and release plan all state '{PRODUCT_IDENTITY_PHRASE}'",
    )


def _check_supported_integration_surface(root: Path) -> ReleaseGateCheck:
    missing_files = [
        path
        for path in ("memoryvault/service.py", "memoryvault/http_api.py", "memoryvault/cli.py")
        if not (root / path).exists()
    ]
    if missing_files:
        return ReleaseGateCheck(
            name="supported_integration_surface",
            passed=False,
            details="missing integration files: " + ", ".join(missing_files),
        )

    readme_text = _read_text(root / "README.md")
    prd_text = _read_text(root / "docs/PRD.md")
    release_plan_text = _read_text(root / "docs/release_plan.md")
    missing_endpoints = [
        endpoint
        for endpoint in SUPPORTED_HTTP_ENDPOINTS
        if endpoint not in readme_text or endpoint not in release_plan_text
    ]
    if "serve-http" not in readme_text or "one local HTTP service" not in prd_text:
        return ReleaseGateCheck(
            name="supported_integration_surface",
            passed=False,
            details="README or PRD does not describe the supported local HTTP surface clearly",
        )
    if missing_endpoints:
        return ReleaseGateCheck(
            name="supported_integration_surface",
            passed=False,
            details="missing endpoint references in README or release plan: " + ", ".join(missing_endpoints),
        )

    return ReleaseGateCheck(
        name="supported_integration_surface",
        passed=True,
        details="local HTTP surface is implemented and documented as the current supported path",
    )


def _check_compatibility_story(root: Path) -> ReleaseGateCheck:
    prd_text = _read_text(root / "docs/PRD.md")
    release_plan_text = _read_text(root / "docs/release_plan.md")
    required_phrases = (
        "artifact_schema_version",
        "legacy current-version files",
        "unknown schema versions",
    )
    if any(phrase not in prd_text for phrase in required_phrases) or any(
        phrase not in release_plan_text for phrase in required_phrases
    ):
        return ReleaseGateCheck(
            name="compatibility_story",
            passed=False,
            details="PRD or release plan is missing the current artifact compatibility rules",
        )

    from .onboarding import (
        load_onboarding_benchmark,
        load_strategy_record,
        load_transfer_benchmark,
        load_workspace_profile,
    )
    from .release_benchmark import load_release_benchmark_report

    loader_names = {
        load_workspace_profile.__name__,
        load_onboarding_benchmark.__name__,
        load_transfer_benchmark.__name__,
        load_strategy_record.__name__,
        load_release_benchmark_report.__name__,
    }
    if len(loader_names) != 5:
        return ReleaseGateCheck(
            name="compatibility_story",
            passed=False,
            details="not all core artifact loaders are available for compatibility checks",
        )

    return ReleaseGateCheck(
        name="compatibility_story",
        passed=True,
        details="core artifact compatibility is both documented and enforced through dedicated loaders",
    )


def _check_support_promise(root: Path) -> ReleaseGateCheck:
    readme_text = _read_text(root / "README.md")
    prd_text = _read_text(root / "docs/PRD.md")
    release_plan_text = _read_text(root / "docs/release_plan.md")

    if any(heading not in readme_text for heading in SUPPORT_PROMISE_HEADINGS) or any(
        heading not in prd_text for heading in SUPPORT_PROMISE_HEADINGS
    ) or any(heading not in release_plan_text for heading in SUPPORT_PROMISE_HEADINGS):
        return ReleaseGateCheck(
            name="support_promise",
            passed=False,
            details="README, PRD, or release plan is missing the support-promise or experimental-surface sections",
        )

    if any(command not in readme_text for command in SUPPORTED_VERIFICATION_COMMANDS) or any(
        command not in prd_text for command in SUPPORTED_VERIFICATION_COMMANDS
    ) or any(command not in release_plan_text for command in SUPPORTED_VERIFICATION_COMMANDS):
        return ReleaseGateCheck(
            name="support_promise",
            passed=False,
            details="support-promise docs do not all name the supported verification commands",
        )

    from .cli import build_parser

    parser = build_parser()
    subparser_actions = [action for action in parser._actions if isinstance(action, argparse._SubParsersAction)]
    if not subparser_actions:
        return ReleaseGateCheck(
            name="support_promise",
            passed=False,
            details="CLI parser does not expose subcommands for support-promise checks",
        )
    choices_action = subparser_actions[0]
    help_by_command = {
        action.dest: action.help or ""
        for action in getattr(choices_action, "_choices_actions", [])
    }
    missing_experimental_markers = [
        command
        for command in EXPERIMENTAL_COMMANDS
        if not help_by_command.get(command, "").startswith("Experimental:")
    ]
    if missing_experimental_markers:
        return ReleaseGateCheck(
            name="support_promise",
            passed=False,
            details="experimental commands are not marked clearly in CLI help: " + ", ".join(missing_experimental_markers),
        )

    return ReleaseGateCheck(
        name="support_promise",
        passed=True,
        details="support promise is documented and experimental commands are marked clearly in CLI help",
    )


def _check_quality_gate_definition(root: Path) -> ReleaseGateCheck:
    quality_gate_path = root / "scripts" / "check_quality.sh"
    if not quality_gate_path.exists():
        return ReleaseGateCheck(
            name="quality_gate",
            passed=False,
            details="missing scripts/check_quality.sh",
        )

    quality_gate_text = _read_text(quality_gate_path)
    missing_fragments = [fragment for fragment in QUALITY_GATE_FRAGMENTS if fragment not in quality_gate_text]
    if missing_fragments:
        return ReleaseGateCheck(
            name="quality_gate",
            passed=False,
            details="quality gate is missing: " + ", ".join(missing_fragments),
        )

    return ReleaseGateCheck(
        name="quality_gate",
        passed=True,
        details="quality gate covers linting, typing, markdown, version sync, tests, and 95% coverage",
    )


def _check_release_benchmark_definition() -> ReleaseGateCheck:
    from .release_benchmark import RELEASE_BENCHMARK_CASES

    task_families = _benchmark_task_families(RELEASE_BENCHMARK_CASES)
    has_transfer_case = any(hasattr(case, "target_adapter_id") for case in RELEASE_BENCHMARK_CASES)
    if len(task_families) < 3 or not has_transfer_case:
        return ReleaseGateCheck(
            name="release_benchmark_definition",
            passed=False,
            details="benchmark bundle does not cover enough task families or lacks a transfer case",
        )

    return ReleaseGateCheck(
        name="release_benchmark_definition",
        passed=True,
        details=(
            f"benchmark bundle defines {len(RELEASE_BENCHMARK_CASES)} cases across "
            f"{len(task_families)} task families with a fixed transfer check"
        ),
    )


def _check_release_benchmark_execution(
    *,
    root: Path,
    benchmark_base_dir: str | Path,
) -> tuple[ReleaseGateCheck, str | None]:
    from .release_benchmark import RELEASE_BENCHMARK_CASES, run_release_benchmark

    resolved_base_dir = Path(benchmark_base_dir)
    if not resolved_base_dir.is_absolute():
        resolved_base_dir = root / resolved_base_dir
    run_dir, report = run_release_benchmark(base_dir=resolved_base_dir)
    expected_case_ids = [case.case_id for case in RELEASE_BENCHMARK_CASES]
    artifact_path = (run_dir / "release_benchmark_report.json").as_posix()
    passed = (
        report.gate_passed
        and len(report.task_families) >= 3
        and report.required_case_ids == expected_case_ids
        and report.total_case_count == len(expected_case_ids)
        and report.passed_case_count == len(expected_case_ids)
    )
    details = (
        f"report at {artifact_path} "
        f"covered {len(report.task_families)} task families and passed {report.passed_case_count}/{report.total_case_count} cases"
    )
    return ReleaseGateCheck(
        name="release_benchmark_execution",
        passed=passed,
        details=details,
    ), artifact_path


def _benchmark_task_families(case_specs: Iterable[object]) -> set[str]:
    families: set[str] = set()
    for case in case_specs:
        for field_name in ("adapter_id", "source_adapter_id", "target_adapter_id"):
            value = getattr(case, field_name, None)
            if value:
                families.add(str(value))
    return families


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")
