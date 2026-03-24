from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .evaluation import evaluate_resume_packet
from .extractor import extract_candidates
from .importer import load_scenario_file
from .models import EvaluationReport, ResumePacket, RunManifest, Scenario, WindTunnelReport
from .resume import build_resume_packet
from .scenarios import get_scenario, list_scenarios
from .storage import LocalArtifactStore
from .wind_tunnel import build_wind_tunnel_report


def run_scenario(scenario_id: str, base_dir: str | Path = "var/memoryvault") -> tuple[Path, RunManifest, ResumePacket, EvaluationReport]:
    scenario = get_scenario(scenario_id)
    return run_loaded_scenario(scenario, base_dir=base_dir)


def run_scenario_file(path: str | Path, base_dir: str | Path = "var/memoryvault") -> tuple[Path, RunManifest, ResumePacket, EvaluationReport]:
    scenario = load_scenario_file(path)
    return run_loaded_scenario(scenario, base_dir=base_dir)


def run_loaded_scenario(scenario: Scenario, base_dir: str | Path = "var/memoryvault") -> tuple[Path, RunManifest, ResumePacket, EvaluationReport]:
    manifest = _build_manifest(scenario)
    candidates = extract_candidates(scenario.events, fallback_goal=scenario.goal)
    packet = build_resume_packet(manifest, candidates)
    evaluation = evaluate_resume_packet(scenario, packet)
    store = LocalArtifactStore(base_dir)
    run_dir = store.save_run(manifest, scenario, scenario.events, candidates, packet, evaluation)
    return run_dir, manifest, packet, evaluation


def run_demo(base_dir: str | Path = "var/memoryvault") -> list[tuple[Path, RunManifest, ResumePacket, EvaluationReport]]:
    results: list[tuple[Path, RunManifest, ResumePacket, EvaluationReport]] = []
    for scenario in list_scenarios():
        results.append(run_scenario(scenario.scenario_id, base_dir=base_dir))
    return results


def run_wind_tunnel_scenario(
    scenario_id: str,
    base_dir: str | Path = "var/memoryvault",
) -> tuple[Path, RunManifest, ResumePacket, EvaluationReport, WindTunnelReport]:
    scenario = get_scenario(scenario_id)
    return run_wind_tunnel_loaded_scenario(scenario, base_dir=base_dir)


def run_wind_tunnel_file(
    path: str | Path,
    base_dir: str | Path = "var/memoryvault",
) -> tuple[Path, RunManifest, ResumePacket, EvaluationReport, WindTunnelReport]:
    scenario = load_scenario_file(path)
    return run_wind_tunnel_loaded_scenario(scenario, base_dir=base_dir)


def run_wind_tunnel_loaded_scenario(
    scenario: Scenario,
    base_dir: str | Path = "var/memoryvault",
) -> tuple[Path, RunManifest, ResumePacket, EvaluationReport, WindTunnelReport]:
    run_dir, manifest, packet, evaluation = run_loaded_scenario(scenario, base_dir=base_dir)
    report = build_wind_tunnel_report(manifest, scenario, packet, evaluation)
    store = LocalArtifactStore(base_dir)
    store.save_json_artifact(run_dir, "wind_tunnel_report.json", report)
    return run_dir, manifest, packet, evaluation, report


def _build_manifest(scenario: Scenario) -> RunManifest:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}-{scenario.scenario_id}-{uuid4().hex[:8]}"
    created_at = datetime.now(timezone.utc).isoformat()
    return RunManifest(
        run_id=run_id,
        scenario_id=scenario.scenario_id,
        title=scenario.title,
        domain=scenario.domain,
        goal=scenario.goal,
        interruption_point=scenario.interruption_point,
        final_goal_guard=scenario.goal,
        created_at=created_at,
    )
