from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .models import WindTunnelReport
from .pipeline import run_demo, run_scenario, run_scenario_file, run_wind_tunnel_file, run_wind_tunnel_scenario
from .public_data import list_public_data
from .promotion import suggest_durable_fields, write_field_suggestions
from .scenarios import list_scenarios


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MemoryVault discovery loop CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-scenarios", help="List built-in interrupted task scenarios")
    list_parser.add_argument("--json", action="store_true", help="Print scenarios as JSON")

    public_data_parser = subparsers.add_parser("list-public-data", help="List Hugging Face benchmark leads")
    public_data_parser.add_argument("--json", action="store_true", help="Print public data leads as JSON")

    run_parser = subparsers.add_parser("run-scenario", help="Run one built-in scenario")
    run_parser.add_argument("scenario_id", help="Scenario id to execute")
    run_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")

    run_file_parser = subparsers.add_parser("run-file", help="Run an interrupted task described in a JSON file")
    run_file_parser.add_argument("path", help="Path to the task JSON file")
    run_file_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")

    demo_parser = subparsers.add_parser("demo", help="Run all built-in scenarios")
    demo_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")

    wind_scenario_parser = subparsers.add_parser("wind-tunnel-scenario", help="Run the wind tunnel on one built-in scenario")
    wind_scenario_parser.add_argument("scenario_id", help="Scenario id to execute")
    wind_scenario_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")

    wind_file_parser = subparsers.add_parser("wind-tunnel-file", help="Run the wind tunnel on one imported JSON trace")
    wind_file_parser.add_argument("path", help="Path to the task JSON file")
    wind_file_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory for run artifacts")

    suggest_parser = subparsers.add_parser("suggest-fields", help="Suggest durable fields from repeated resume misses")
    suggest_parser.add_argument("--base-dir", default="var/memoryvault", help="Directory containing run artifacts")
    suggest_parser.add_argument("--threshold", type=int, default=2, help="Minimum missing-run count to mark a field for promotion")
    suggest_parser.add_argument("--json", action="store_true", help="Print suggestions as JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
        run_dir, manifest, _packet, _evaluation, report = run_wind_tunnel_scenario(args.scenario_id, base_dir=args.base_dir)
        _print_wind_tunnel_summary(run_dir.as_posix(), manifest.goal, report)
        return 0

    if args.command == "wind-tunnel-file":
        run_dir, manifest, _packet, _evaluation, report = run_wind_tunnel_file(args.path, base_dir=args.base_dir)
        _print_wind_tunnel_summary(run_dir.as_posix(), manifest.goal, report)
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


if __name__ == "__main__":
    raise SystemExit(main())
