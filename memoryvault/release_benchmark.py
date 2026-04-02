from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from uuid import uuid4

from .hf_adapters import load_and_adapt_hf_rows
from .models import (
    RELEASE_BENCHMARK_REPORT_SCHEMA_VERSION,
    ReleaseBenchmarkCaseResult,
    ReleaseBenchmarkReport,
)
from .onboarding import (
    ArtifactCompatibilityError,
    _load_json_payload,
    _normalize_artifact_payload,
    onboard_scenarios,
    transfer_scenarios,
)
from .release_checks import ensure_version_sync
from .storage import LocalArtifactStore

RELEASE_BENCHMARK_BUNDLE_ID = "public_release_bundle"
RELEASE_BENCHMARK_BUNDLE_VERSION = "0.5.v1"


@dataclass(frozen=True, slots=True)
class OnboardingCaseSpec:
    case_id: str
    title: str
    adapter_id: str
    rows_path: str
    gate_threshold: float = 0.9


@dataclass(frozen=True, slots=True)
class TransferCaseSpec:
    case_id: str
    title: str
    source_adapter_id: str
    source_rows_path: str
    target_adapter_id: str
    target_rows_path: str
    gate_threshold: float = 0.85


RELEASE_BENCHMARK_CASES: tuple[OnboardingCaseSpec | TransferCaseSpec, ...] = (
    OnboardingCaseSpec(
        case_id="hf_taskbench_onboarding",
        title="TaskBench offline onboarding gate",
        adapter_id="hf_taskbench",
        rows_path="examples/huggingface_rows/taskbench_first_rows.json",
    ),
    OnboardingCaseSpec(
        case_id="hf_swe_bench_verified_onboarding",
        title="SWE-bench Verified offline onboarding gate",
        adapter_id="hf_swe_bench_verified",
        rows_path="examples/huggingface_rows/swe_bench_verified_first_rows.json",
    ),
    OnboardingCaseSpec(
        case_id="hf_qasper_onboarding",
        title="QASPER offline onboarding gate",
        adapter_id="hf_qasper",
        rows_path="examples/huggingface_rows/qasper_first_rows.json",
    ),
    OnboardingCaseSpec(
        case_id="hf_conversation_bench_onboarding",
        title="Conversation Bench offline onboarding gate",
        adapter_id="hf_conversation_bench",
        rows_path="examples/huggingface_rows/conversation_bench_first_rows.json",
    ),
    TransferCaseSpec(
        case_id="hf_taskbench_to_conversation_transfer",
        title="TaskBench to Conversation Bench transfer gate",
        source_adapter_id="hf_taskbench",
        source_rows_path="examples/huggingface_rows/taskbench_first_rows.json",
        target_adapter_id="hf_conversation_bench",
        target_rows_path="examples/huggingface_rows/conversation_bench_first_rows.json",
    ),
)


def run_release_benchmark(
    *,
    base_dir: str | Path = "var/memoryvault",
    bundle_id: str = RELEASE_BENCHMARK_BUNDLE_ID,
    bundle_version: str = RELEASE_BENCHMARK_BUNDLE_VERSION,
) -> tuple[Path, ReleaseBenchmarkReport]:
    project_version = ensure_version_sync()
    report_dir = _create_release_benchmark_dir(base_dir, bundle_id)
    report_dir.mkdir(parents=True, exist_ok=True)
    bundle_runs_dir = report_dir / "bundle_runs"
    bundle_runs_dir.mkdir(parents=True, exist_ok=True)

    case_results: list[ReleaseBenchmarkCaseResult] = []
    for case_spec in RELEASE_BENCHMARK_CASES:
        if isinstance(case_spec, OnboardingCaseSpec):
            case_results.append(_run_onboarding_case(case_spec, bundle_runs_dir))
        else:
            case_results.append(_run_transfer_case(case_spec, bundle_runs_dir))

    task_families = sorted(
        {
            family
            for case_result in case_results
            for family in case_result.source_task_families + case_result.evaluation_task_families
        }
    )
    report = ReleaseBenchmarkReport(
        bundle_id=bundle_id,
        bundle_version=bundle_version,
        project_version=project_version,
        created_at=datetime.now(timezone.utc).isoformat(),
        report_dir=report_dir.as_posix(),
        required_case_ids=[case.case_id for case in RELEASE_BENCHMARK_CASES],
        task_families=task_families,
        total_case_count=len(case_results),
        passed_case_count=sum(1 for case in case_results if case.gate_passed),
        baseline_average_score=round(mean(case.baseline_average_score for case in case_results), 4),
        cue_disabled_average_score=round(mean(case.cue_disabled_average_score for case in case_results), 4),
        adapted_average_score=round(mean(case.adapted_average_score for case in case_results), 4),
        average_score_delta=round(mean(case.average_score_delta for case in case_results), 4),
        cue_average_score_delta=round(mean(case.cue_average_score_delta for case in case_results), 4),
        gate_passed=all(case.gate_passed for case in case_results),
        case_results=case_results,
    )
    LocalArtifactStore(report_dir).save_json_artifact(report_dir, "release_benchmark_report.json", report)
    return report_dir, report


def load_release_benchmark_report(path: str | Path) -> ReleaseBenchmarkReport:
    payload = _load_json_payload(path)
    compatible_payload = _normalize_artifact_payload(
        payload,
        expected_schema=RELEASE_BENCHMARK_REPORT_SCHEMA_VERSION,
        artifact_label="release benchmark report",
        source_path=path,
    )
    case_results = [
        ReleaseBenchmarkCaseResult(**item)
        for item in compatible_payload.pop("case_results", [])
    ]
    try:
        return ReleaseBenchmarkReport(
            **compatible_payload,
            case_results=case_results,
        )
    except TypeError as error:
        raise ArtifactCompatibilityError(f"{Path(path)} is not a valid release benchmark report: {error}") from error


def _run_onboarding_case(case_spec: OnboardingCaseSpec, bundle_runs_dir: Path) -> ReleaseBenchmarkCaseResult:
    scenarios = load_and_adapt_hf_rows(case_spec.adapter_id, case_spec.rows_path)
    workspace_id = f"release_{case_spec.case_id}"
    run_dir, profile, benchmark = onboard_scenarios(
        scenarios,
        base_dir=bundle_runs_dir,
        workspace_id=workspace_id,
        gate_threshold=case_spec.gate_threshold,
    )
    return ReleaseBenchmarkCaseResult(
        case_id=case_spec.case_id,
        title=case_spec.title,
        run_kind="onboarding",
        profile_version=profile.profile_version,
        artifact_dir=run_dir.as_posix(),
        source_task_families=list(profile.task_families),
        evaluation_task_families=sorted({item.task_family for item in benchmark.scenario_results}),
        scenario_count=len(benchmark.scenario_results),
        improved_scenario_count=sum(1 for item in benchmark.scenario_results if item.score_delta > 0.0),
        baseline_average_score=benchmark.baseline_average_score,
        cue_disabled_average_score=benchmark.cue_disabled_average_score,
        adapted_average_score=benchmark.adapted_average_score,
        average_score_delta=benchmark.average_score_delta,
        cue_average_score_delta=benchmark.cue_average_score_delta,
        gate_threshold=benchmark.gate_threshold,
        gate_passed=benchmark.gate_passed,
        recommended_actions=list(benchmark.recommended_actions),
    )


def _run_transfer_case(case_spec: TransferCaseSpec, bundle_runs_dir: Path) -> ReleaseBenchmarkCaseResult:
    source_scenarios = load_and_adapt_hf_rows(case_spec.source_adapter_id, case_spec.source_rows_path)
    target_scenarios = load_and_adapt_hf_rows(case_spec.target_adapter_id, case_spec.target_rows_path)
    workspace_id = f"release_{case_spec.case_id}"
    run_dir, profile, _source_benchmark, benchmark = transfer_scenarios(
        source_scenarios,
        target_scenarios,
        base_dir=bundle_runs_dir,
        workspace_id=workspace_id,
        gate_threshold=case_spec.gate_threshold,
    )
    return ReleaseBenchmarkCaseResult(
        case_id=case_spec.case_id,
        title=case_spec.title,
        run_kind="transfer",
        profile_version=profile.profile_version,
        artifact_dir=run_dir.as_posix(),
        source_task_families=list(benchmark.source_task_families),
        evaluation_task_families=list(benchmark.target_task_families),
        scenario_count=len(benchmark.scenario_results),
        improved_scenario_count=sum(1 for item in benchmark.scenario_results if item.score_delta > 0.0),
        baseline_average_score=benchmark.baseline_average_score,
        cue_disabled_average_score=benchmark.cue_disabled_average_score,
        adapted_average_score=benchmark.adapted_average_score,
        average_score_delta=benchmark.average_score_delta,
        cue_average_score_delta=benchmark.cue_average_score_delta,
        gate_threshold=benchmark.gate_threshold,
        gate_passed=benchmark.gate_passed,
        recommended_actions=list(benchmark.recommended_actions),
    )


def _create_release_benchmark_dir(base_dir: str | Path, bundle_id: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid4().hex[:8]
    return Path(base_dir) / f"{timestamp}-release-benchmark-{bundle_id}-{suffix}"
