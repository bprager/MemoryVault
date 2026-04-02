from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .hf_adapters import fetch_and_adapt_hf_rows, list_hf_adapters, load_and_adapt_hf_rows
from .logging_utils import configure_logging
from .models import (
    OnboardingBenchmarkReport,
    ProfileRefreshReport,
    ReleaseBenchmarkReport,
    StrategyTrackerSummary,
    TransferBenchmarkReport,
    WindTunnelReport,
)
from .onboarding import (
    onboard_directory,
    onboard_scenarios,
    refresh_directory,
    refresh_scenarios,
    summarize_strategy_records,
    transfer_directory,
    transfer_scenarios,
)
from .pipeline import run_demo, run_scenario, run_scenario_file, run_wind_tunnel_file, run_wind_tunnel_scenario
from .public_data import list_public_data
from .promotion import suggest_durable_fields, write_field_suggestions
from .http_api import run_http_server
from .release_benchmark import run_release_benchmark
from .release_checks import ReleaseCandidateGateReport, run_release_candidate_gate
from .scenarios import list_scenarios


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MemoryVault discovery loop CLI")
    parser.add_argument("--log-level", default="WARNING", help="Python logging level: DEBUG, INFO, WARNING, or ERROR")
    parser.add_argument("--log-file", default=None, help="Optional path for a log file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-scenarios", help="Experimental: list built-in interrupted task scenarios")
    list_parser.add_argument("--json", action="store_true", help="Print scenarios as JSON")

    public_data_parser = subparsers.add_parser("list-public-data", help="Experimental: list Hugging Face benchmark leads")
    public_data_parser.add_argument("--json", action="store_true", help="Print public data leads as JSON")

    hf_adapter_parser = subparsers.add_parser("list-hf-adapters", help="Experimental: list supported Hugging Face dataset adapters")
    hf_adapter_parser.add_argument("--json", action="store_true", help="Print supported adapters as JSON")

    run_parser = subparsers.add_parser("run-scenario", help="Experimental: run one built-in scenario")
    run_parser.add_argument("scenario_id", help="Scenario id to execute")
    run_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")

    run_file_parser = subparsers.add_parser("run-file", help="Run an interrupted task described in a JSON file")
    run_file_parser.add_argument("path", help="Path to the task JSON file")
    run_file_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")

    demo_parser = subparsers.add_parser("demo", help="Experimental: run all built-in scenarios")
    demo_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")

    wind_scenario_parser = subparsers.add_parser("wind-tunnel-scenario", help="Experimental: run the wind tunnel on one built-in scenario")
    wind_scenario_parser.add_argument("scenario_id", help="Scenario id to execute")
    wind_scenario_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")

    wind_file_parser = subparsers.add_parser("wind-tunnel-file", help="Run the wind tunnel on one imported JSON trace")
    wind_file_parser.add_argument("path", help="Path to the task JSON file")
    wind_file_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")

    onboarding_parser = subparsers.add_parser(
        "onboard-directory",
        help="Generate a zero-touch workspace profile from JSON traces and run the onboarding benchmark gate",
    )
    onboarding_parser.add_argument("path", help="Directory containing JSON traces")
    onboarding_parser.add_argument("--workspace-id", default=None, help="Optional workspace id for generated artifacts")
    onboarding_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")
    onboarding_parser.add_argument("--sample-size", type=int, default=None, help="Optional representative sample size")
    onboarding_parser.add_argument(
        "--gate-threshold",
        type=float,
        default=0.9,
        help="Minimum adapted average score required for the onboarding gate to pass",
    )

    refresh_parser = subparsers.add_parser(
        "refresh-directory",
        help="Build a refreshed workspace profile from JSON traces using prior strategy rollups as evidence",
    )
    refresh_parser.add_argument("path", help="Directory containing JSON traces")
    refresh_parser.add_argument("--workspace-id", default=None, help="Optional workspace id for generated artifacts")
    refresh_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")
    refresh_parser.add_argument("--sample-size", type=int, default=None, help="Optional representative sample size")
    refresh_parser.add_argument(
        "--gate-threshold",
        type=float,
        default=0.9,
        help="Minimum adapted average score required for the refresh benchmark to pass",
    )

    transfer_directory_parser = subparsers.add_parser(
        "transfer-directory",
        help="Learn a workspace profile from one trace directory and test whether it transfers to another",
    )
    transfer_directory_parser.add_argument("source_path", help="Directory containing source JSON traces")
    transfer_directory_parser.add_argument("target_path", help="Directory containing target JSON traces")
    transfer_directory_parser.add_argument("--workspace-id", default=None, help="Optional workspace id for generated artifacts")
    transfer_directory_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")
    transfer_directory_parser.add_argument("--sample-size", type=int, default=None, help="Optional representative sample size")
    transfer_directory_parser.add_argument(
        "--gate-threshold",
        type=float,
        default=0.85,
        help="Minimum adapted average score required for the transfer gate to pass",
    )

    onboard_hf_file_parser = subparsers.add_parser(
        "onboard-hf-file",
        help="Experimental: run onboarding on saved Hugging Face dataset rows using a supported adapter",
    )
    onboard_hf_file_parser.add_argument("adapter_id", help="Adapter id, for example hf_taskbench")
    onboard_hf_file_parser.add_argument("path", help="Path to a Hugging Face rows JSON file")
    onboard_hf_file_parser.add_argument("--workspace-id", default=None, help="Optional workspace id for generated artifacts")
    onboard_hf_file_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")
    onboard_hf_file_parser.add_argument("--sample-size", type=int, default=None, help="Optional representative sample size")
    onboard_hf_file_parser.add_argument(
        "--gate-threshold",
        type=float,
        default=0.9,
        help="Minimum adapted average score required for the onboarding gate to pass",
    )

    refresh_hf_file_parser = subparsers.add_parser(
        "refresh-hf-file",
        help="Experimental: refresh a workspace profile from saved Hugging Face rows using prior strategy rollups as evidence",
    )
    refresh_hf_file_parser.add_argument("adapter_id", help="Adapter id, for example hf_taskbench")
    refresh_hf_file_parser.add_argument("path", help="Path to a Hugging Face rows JSON file")
    refresh_hf_file_parser.add_argument("--workspace-id", default=None, help="Optional workspace id for generated artifacts")
    refresh_hf_file_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")
    refresh_hf_file_parser.add_argument("--sample-size", type=int, default=None, help="Optional representative sample size")
    refresh_hf_file_parser.add_argument(
        "--gate-threshold",
        type=float,
        default=0.9,
        help="Minimum adapted average score required for the refresh benchmark to pass",
    )

    onboard_hf_remote_parser = subparsers.add_parser(
        "onboard-hf-first-rows",
        help="Experimental: fetch the first rows of a supported Hugging Face dataset and run onboarding on them",
    )
    onboard_hf_remote_parser.add_argument("adapter_id", help="Adapter id, for example hf_taskbench")
    onboard_hf_remote_parser.add_argument("--config", default=None, help="Optional dataset config override")
    onboard_hf_remote_parser.add_argument("--split", default=None, help="Optional dataset split override")
    onboard_hf_remote_parser.add_argument("--rows", type=int, default=8, help="Number of dataset rows to adapt")
    onboard_hf_remote_parser.add_argument("--token", default=None, help="Optional Hugging Face API token")
    onboard_hf_remote_parser.add_argument("--workspace-id", default=None, help="Optional workspace id for generated artifacts")
    onboard_hf_remote_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")
    onboard_hf_remote_parser.add_argument("--sample-size", type=int, default=None, help="Optional representative sample size")
    onboard_hf_remote_parser.add_argument(
        "--gate-threshold",
        type=float,
        default=0.9,
        help="Minimum adapted average score required for the onboarding gate to pass",
    )

    transfer_hf_file_parser = subparsers.add_parser(
        "transfer-hf-files",
        help="Experimental: learn on saved Hugging Face rows from one adapter and test transfer on another",
    )
    transfer_hf_file_parser.add_argument("source_adapter_id", help="Source adapter id, for example hf_taskbench")
    transfer_hf_file_parser.add_argument("source_path", help="Path to the source Hugging Face rows JSON file")
    transfer_hf_file_parser.add_argument("target_adapter_id", help="Target adapter id, for example hf_conversation_bench")
    transfer_hf_file_parser.add_argument("target_path", help="Path to the target Hugging Face rows JSON file")
    transfer_hf_file_parser.add_argument("--workspace-id", default=None, help="Optional workspace id for generated artifacts")
    transfer_hf_file_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")
    transfer_hf_file_parser.add_argument("--sample-size", type=int, default=None, help="Optional representative sample size")
    transfer_hf_file_parser.add_argument(
        "--gate-threshold",
        type=float,
        default=0.85,
        help="Minimum adapted average score required for the transfer gate to pass",
    )

    suggest_parser = subparsers.add_parser("suggest-fields", help="Suggest durable fields from repeated resume misses")
    suggest_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory containing run artifacts")
    suggest_parser.add_argument("--threshold", type=int, default=2, help="Minimum missing-run count to mark a field for promotion")
    suggest_parser.add_argument("--json", action="store_true", help="Print suggestions as JSON")

    strategy_summary_parser = subparsers.add_parser(
        "summarize-strategies",
        help="Summarize recorded onboarding and transfer strategy runs",
    )
    strategy_summary_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory containing strategy tracker artifacts")
    strategy_summary_parser.add_argument("--json", action="store_true", help="Print the strategy summary as JSON")

    release_benchmark_parser = subparsers.add_parser(
        "release-benchmark",
        help="Run the fixed offline release benchmark bundle and write a stable report artifact",
    )
    release_benchmark_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for release benchmark artifacts")
    release_benchmark_parser.add_argument("--json", action="store_true", help="Print the release benchmark report as JSON")

    release_candidate_parser = subparsers.add_parser(
        "release-candidate-check",
        help="Run the repo-local release verification gate and report whether the stable support promise still holds",
    )
    release_candidate_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for release benchmark artifacts")
    release_candidate_parser.add_argument("--skip-benchmark", action="store_true", help="Skip executing the release benchmark bundle")
    release_candidate_parser.add_argument("--json", action="store_true", help="Print the release-candidate gate report as JSON")

    serve_http_parser = subparsers.add_parser(
        "serve-http",
        help="Run the local HTTP service for the supported 1.0 integration path",
    )
    serve_http_parser.add_argument("--host", default="127.0.0.1", help="Host interface for the local HTTP service")
    serve_http_parser.add_argument("--port", type=int, default=8765, help="Port for the local HTTP service")
    serve_http_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for local service state")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(level=args.log_level, log_file=args.log_file)

    if args.command == "list-scenarios":
        scenarios = list_scenarios()
        if args.json:
            print(json.dumps([asdict(scenario) for scenario in scenarios], indent=2))
        else:
            for scenario in scenarios:
                print(f"{scenario.scenario_id}: {scenario.title}")
        return 0

    if args.command == "list-public-data":
        leads = list_public_data()
        if args.json:
            print(json.dumps([asdict(lead) for lead in leads], indent=2))
        else:
            for lead in leads:
                print(f"{lead.dataset_id}: {lead.name}")
                print(f"  focus: {lead.focus}")
                print(f"  why: {lead.why_it_fits}")
                print(f"  use: {lead.how_to_use_it}")
                print(f"  url: {lead.url}")
                print("")
        return 0

    if args.command == "list-hf-adapters":
        adapters = list_hf_adapters()
        if args.json:
            print(json.dumps([asdict(adapter) for adapter in adapters], indent=2))
        else:
            for adapter in adapters:
                print(f"{adapter.adapter_id}: {adapter.dataset_name}")
                print(f"  domain: {adapter.domain}")
                print(f"  default config: {adapter.default_config}")
                print(f"  default split: {adapter.default_split}")
                print(f"  why: {adapter.description}")
                print("")
        return 0

    if args.command == "run-scenario":
        run_dir, manifest, packet, evaluation = run_scenario(args.scenario_id, base_dir=args.base_dir)
        _print_run_summary(run_dir.as_posix(), manifest.goal, packet.final_goal_guard, evaluation.score, evaluation.improvement_actions)
        return 0

    if args.command == "run-file":
        run_dir, manifest, packet, evaluation = run_scenario_file(args.path, base_dir=args.base_dir)
        _print_run_summary(run_dir.as_posix(), manifest.goal, packet.final_goal_guard, evaluation.score, evaluation.improvement_actions)
        return 0

    if args.command == "demo":
        results = run_demo(base_dir=args.base_dir)
        for run_dir, manifest, packet, evaluation in results:
            _print_run_summary(run_dir.as_posix(), manifest.goal, packet.final_goal_guard, evaluation.score, evaluation.improvement_actions)
        return 0

    if args.command == "wind-tunnel-scenario":
        run_dir, manifest, _packet, _evaluation, wind_tunnel_report = run_wind_tunnel_scenario(
            args.scenario_id,
            base_dir=args.base_dir,
        )
        _print_wind_tunnel_summary(run_dir.as_posix(), manifest.goal, wind_tunnel_report)
        return 0

    if args.command == "wind-tunnel-file":
        run_dir, manifest, _packet, _evaluation, wind_tunnel_report = run_wind_tunnel_file(
            args.path,
            base_dir=args.base_dir,
        )
        _print_wind_tunnel_summary(run_dir.as_posix(), manifest.goal, wind_tunnel_report)
        return 0

    if args.command == "onboard-directory":
        run_dir, profile, benchmark = onboard_directory(
            args.path,
            base_dir=args.base_dir,
            workspace_id=args.workspace_id,
            sample_size=args.sample_size,
            gate_threshold=args.gate_threshold,
        )
        _print_onboarding_summary(run_dir.as_posix(), profile.workspace_id, profile.sample_scenario_ids, profile.holdout_scenario_ids, benchmark)
        return 0

    if args.command == "refresh-directory":
        run_dir, profile, benchmark, refresh_report = refresh_directory(
            args.path,
            base_dir=args.base_dir,
            workspace_id=args.workspace_id,
            sample_size=args.sample_size,
            gate_threshold=args.gate_threshold,
        )
        _print_refresh_summary(run_dir.as_posix(), profile.workspace_id, benchmark, refresh_report)
        return 0

    if args.command == "transfer-directory":
        run_dir, profile, source_benchmark, transfer_benchmark = transfer_directory(
            args.source_path,
            args.target_path,
            base_dir=args.base_dir,
            workspace_id=args.workspace_id,
            sample_size=args.sample_size,
            gate_threshold=args.gate_threshold,
        )
        _print_transfer_summary(run_dir.as_posix(), profile.workspace_id, source_benchmark, transfer_benchmark)
        return 0

    if args.command == "onboard-hf-file":
        scenarios = load_and_adapt_hf_rows(args.adapter_id, args.path)
        workspace_id = args.workspace_id or f"{args.adapter_id}_workspace"
        run_dir, profile, benchmark = onboard_scenarios(
            scenarios,
            base_dir=args.base_dir,
            workspace_id=workspace_id,
            sample_size=args.sample_size,
            gate_threshold=args.gate_threshold,
        )
        _print_onboarding_summary(run_dir.as_posix(), profile.workspace_id, profile.sample_scenario_ids, profile.holdout_scenario_ids, benchmark)
        return 0

    if args.command == "refresh-hf-file":
        scenarios = load_and_adapt_hf_rows(args.adapter_id, args.path)
        workspace_id = args.workspace_id or f"{args.adapter_id}_workspace"
        run_dir, profile, benchmark, refresh_report = refresh_scenarios(
            scenarios,
            base_dir=args.base_dir,
            workspace_id=workspace_id,
            sample_size=args.sample_size,
            gate_threshold=args.gate_threshold,
        )
        _print_refresh_summary(run_dir.as_posix(), profile.workspace_id, benchmark, refresh_report)
        return 0

    if args.command == "onboard-hf-first-rows":
        scenarios = fetch_and_adapt_hf_rows(
            args.adapter_id,
            config=args.config,
            split=args.split,
            length=args.rows,
            token=args.token,
        )
        workspace_id = args.workspace_id or f"{args.adapter_id}_workspace"
        run_dir, profile, benchmark = onboard_scenarios(
            scenarios,
            base_dir=args.base_dir,
            workspace_id=workspace_id,
            sample_size=args.sample_size,
            gate_threshold=args.gate_threshold,
        )
        _print_onboarding_summary(run_dir.as_posix(), profile.workspace_id, profile.sample_scenario_ids, profile.holdout_scenario_ids, benchmark)
        return 0

    if args.command == "transfer-hf-files":
        source_scenarios = load_and_adapt_hf_rows(args.source_adapter_id, args.source_path)
        target_scenarios = load_and_adapt_hf_rows(args.target_adapter_id, args.target_path)
        workspace_id = args.workspace_id or f"{args.source_adapter_id}_to_{args.target_adapter_id}"
        run_dir, profile, source_benchmark, transfer_benchmark = transfer_scenarios(
            source_scenarios,
            target_scenarios,
            base_dir=args.base_dir,
            workspace_id=workspace_id,
            sample_size=args.sample_size,
            gate_threshold=args.gate_threshold,
        )
        _print_transfer_summary(run_dir.as_posix(), profile.workspace_id, source_benchmark, transfer_benchmark)
        return 0

    if args.command == "suggest-fields":
        suggestions = suggest_durable_fields(args.base_dir, threshold=args.threshold)
        if args.json:
            print(json.dumps([asdict(item) for item in suggestions], indent=2))
        else:
            output_path = write_field_suggestions(args.base_dir, threshold=args.threshold)
            print(f"suggestions: {output_path.as_posix()}")
            if not suggestions:
                print("no repeated misses found")
            for item in suggestions:
                print(f"{item.field_name}: {item.status} ({item.missing_run_count}/{item.total_run_count})")
                print(f"  source category: {item.source_category}")
                print(f"  why: {item.rationale}")
        return 0

    if args.command == "summarize-strategies":
        summary = summarize_strategy_records(args.base_dir)
        if args.json:
            print(json.dumps(asdict(summary), indent=2))
        else:
            _print_strategy_summary(summary)
        return 0

    if args.command == "release-benchmark":
        run_dir, release_report = run_release_benchmark(base_dir=args.base_dir)
        if args.json:
            print(json.dumps(asdict(release_report), indent=2))
        else:
            _print_release_benchmark_summary(run_dir.as_posix(), release_report)
        return 0

    if args.command == "release-candidate-check":
        report = run_release_candidate_gate(
            benchmark_base_dir=args.base_dir,
            run_benchmark=not args.skip_benchmark,
        )
        if args.json:
            print(json.dumps(asdict(report), indent=2))
        else:
            _print_release_candidate_summary(report)
        return 0 if report.passed else 1

    if args.command == "serve-http":
        print(f"serving: http://{args.host}:{args.port}")
        run_http_server(host=args.host, port=args.port, base_dir=args.base_dir)
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


def _print_run_summary(run_dir: str, goal: str, final_goal_guard: str, score: float, improvement_actions: list[str]) -> None:
    print(f"artifacts: {run_dir}")
    print(f"goal: {goal}")
    print(f"goal guard: {final_goal_guard}")
    print(f"resume score: {score:.2f}")
    if improvement_actions:
        print("improvements:")
        for action in improvement_actions:
            print(f"- {action}")
    else:
        print("improvements: none")
    print("")


def _print_wind_tunnel_summary(run_dir: str, goal: str, report: WindTunnelReport) -> None:
    print(f"artifacts: {run_dir}")
    print(f"goal: {goal}")
    print(f"baseline score: {report.baseline_score:.2f}")
    print("fragile fields:")
    if report.most_fragile_fields:
        for field_name in report.most_fragile_fields:
            print(f"- {field_name}")
    else:
        print("- none")
    print("variant damage:")
    for result in report.variant_results:
        print(f"- {result.variant_id}: delta {result.score_delta:.2f} score {result.score:.2f}")
    print("")


def _print_onboarding_summary(
    run_dir: str,
    workspace_id: str,
    sample_scenario_ids: list[str],
    holdout_scenario_ids: list[str],
    benchmark: OnboardingBenchmarkReport,
) -> None:
    print(f"artifacts: {run_dir}")
    print(f"workspace: {workspace_id}")
    print(f"profile version: {benchmark.profile_version}")
    print(f"sample traces: {len(sample_scenario_ids)}")
    print(f"held-out traces: {len(holdout_scenario_ids)}")
    print(f"baseline score: {benchmark.baseline_average_score:.2f}")
    print(f"adapted score: {benchmark.adapted_average_score:.2f}")
    print(f"score delta: {benchmark.average_score_delta:.2f}")
    print(f"cue-only delta: {benchmark.cue_average_score_delta:.2f}")
    print(f"gate passed: {'yes' if benchmark.gate_passed else 'no'}")
    print("actions:")
    for action in benchmark.recommended_actions:
        print(f"- {action}")
    print("")


def _print_transfer_summary(
    run_dir: str,
    workspace_id: str,
    source_benchmark: OnboardingBenchmarkReport,
    transfer_benchmark: TransferBenchmarkReport,
) -> None:
    print(f"artifacts: {run_dir}")
    print(f"workspace: {workspace_id}")
    print(f"profile version: {transfer_benchmark.profile_version}")
    print(f"source hold-out score: {source_benchmark.adapted_average_score:.2f}")
    print(f"target baseline score: {transfer_benchmark.baseline_average_score:.2f}")
    print(f"target adapted score: {transfer_benchmark.adapted_average_score:.2f}")
    print(f"target score delta: {transfer_benchmark.average_score_delta:.2f}")
    print(f"cue-only delta: {transfer_benchmark.cue_average_score_delta:.2f}")
    print(f"transfer gate passed: {'yes' if transfer_benchmark.gate_passed else 'no'}")
    print("actions:")
    for action in transfer_benchmark.recommended_actions:
        print(f"- {action}")
    print("")


def _print_strategy_summary(summary: StrategyTrackerSummary) -> None:
    print(f"records: {summary.total_records}")
    print(f"latest profile version: {summary.latest_profile_version or 'none'}")
    print("task families:")
    if summary.task_families:
        for family_name in summary.task_families:
            print(f"- {family_name}")
    else:
        print("- none")
    print("run kinds:")
    if summary.run_kind_summaries:
        for item in summary.run_kind_summaries:
            print(
                f"- {item.run_kind}: {item.record_count} records, "
                f"adapted {item.average_adapted_score:.2f}, delta {item.average_score_delta:.2f}, "
                f"pass {item.gate_pass_rate:.2f}, "
                f"duration {item.average_duration_ms:.1f}ms, "
                f"{item.average_duration_per_scenario_ms:.1f}ms/scenario"
            )
    else:
        print("- none")
    print("recurring wins:")
    helped_categories = [category for category in summary.category_summaries if category.helped_scenario_count > 0][:3]
    if helped_categories:
        for category in helped_categories:
            print(
                f"- {category.category}: helped in {category.helped_run_count} runs / "
                f"{category.helped_scenario_count} scenarios"
            )
    else:
        print("- none")
    print("recurring gaps:")
    remaining_categories = [
        category for category in summary.category_summaries if category.remaining_gap_scenario_count > 0
    ][:3]
    if remaining_categories:
        for category in remaining_categories:
            print(
                f"- {category.category}: still missing in {category.remaining_gap_run_count} runs / "
                f"{category.remaining_gap_scenario_count} scenarios"
            )
    else:
        print("- none")
    print("cue transfer:")
    cue_categories = [category for category in summary.category_summaries if category.cue_helped_scenario_count > 0][:5]
    if cue_categories:
        for category in cue_categories:
            family_text = ", ".join(category.helped_task_families[:3]) if category.helped_task_families else "none"
            print(
                f"- {category.category}: cue helped in {category.cue_helped_run_count} runs / "
                f"{category.cue_helped_scenario_count} scenarios, "
                f"cue delta {category.cue_average_score_delta:.2f}, families {family_text}"
            )
    else:
        print("- none")
    print("task family results:")
    if summary.task_family_summaries:
        for family in summary.task_family_summaries[:5]:
            print(
                f"- {family.task_family}: {family.record_count} records, "
                f"{family.scenario_count} scenarios, delta {family.average_score_delta:.2f}, "
                f"improvement rate {family.improvement_rate:.2f}, pass {family.gate_pass_rate:.2f}"
            )
    else:
        print("- none")
    print("profile history:")
    if summary.profile_summaries:
        for profile in summary.profile_summaries[:5]:
            print(
                f"- {profile.profile_version}: {profile.record_count} records, "
                f"delta {profile.average_score_delta:.2f}, pass {profile.gate_pass_rate:.2f}"
            )
    else:
        print("- none")
    print("workspace lineages:")
    if summary.workspace_lineages:
        for lineage in summary.workspace_lineages[:5]:
            print(
                f"- {lineage.workspace_id}: {' -> '.join(lineage.profile_versions)}, "
                f"delta {lineage.average_score_delta:.2f}"
            )
    else:
        print("- none")
    print("")


def _print_refresh_summary(
    run_dir: str,
    workspace_id: str,
    benchmark: OnboardingBenchmarkReport,
    refresh_report: ProfileRefreshReport,
) -> None:
    print(f"artifacts: {run_dir}")
    print(f"workspace: {workspace_id}")
    print(f"initial profile version: {refresh_report.initial_profile_version}")
    print(f"final profile version: {refresh_report.final_profile_version}")
    print(f"evidence records: {refresh_report.relevant_record_count}")
    print(f"initial adapted score: {refresh_report.initial_adapted_average_score:.2f}")
    print(f"final adapted score: {refresh_report.final_adapted_average_score:.2f}")
    print(f"refresh score delta: {refresh_report.score_delta:.2f}")
    print(f"candidate accepted: {'yes' if refresh_report.candidate_accepted else 'no'}")
    print(f"gate passed: {'yes' if benchmark.gate_passed else 'no'}")
    print("actions:")
    for action in refresh_report.actions:
        print(f"- {action}")
    print("")


def _print_release_benchmark_summary(run_dir: str, report: ReleaseBenchmarkReport) -> None:
    print(f"artifacts: {run_dir}")
    print(f"bundle: {report.bundle_id} ({report.bundle_version})")
    print(f"project version: {report.project_version}")
    print(f"cases passed: {report.passed_case_count}/{report.total_case_count}")
    print(f"baseline average: {report.baseline_average_score:.2f}")
    print(f"cue-disabled average: {report.cue_disabled_average_score:.2f}")
    print(f"adapted average: {report.adapted_average_score:.2f}")
    print(f"average delta: {report.average_score_delta:.2f}")
    print(f"cue-only delta: {report.cue_average_score_delta:.2f}")
    print(f"release bundle passed: {'yes' if report.gate_passed else 'no'}")
    print("task families:")
    for family in report.task_families:
        print(f"- {family}")
    print("case results:")
    for case in report.case_results:
        print(
            f"- {case.case_id}: {case.run_kind}, pass {'yes' if case.gate_passed else 'no'}, "
            f"delta {case.average_score_delta:.2f}, adapted {case.adapted_average_score:.2f}"
        )
    print("")


def _print_release_candidate_summary(report: ReleaseCandidateGateReport) -> None:
    print(f"release line: {report.release_line}")
    print(f"project version: {report.project_version}")
    print(f"benchmark ran: {'yes' if report.benchmark_ran else 'no'}")
    if report.benchmark_artifact_path is not None:
        print(f"benchmark artifact: {report.benchmark_artifact_path}")
    print(f"gate passed: {'yes' if report.passed else 'no'}")
    print("checks:")
    for check in report.checks:
        print(f"- {check.name}: {'pass' if check.passed else 'fail'}")
        print(f"  {check.details}")
    print("")


if __name__ == "__main__":
    raise SystemExit(main())
