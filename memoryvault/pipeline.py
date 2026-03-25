from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from .evaluation import evaluate_resume_packet
from .extractor import extract_candidates
from .importer import load_scenario_file
from .logging_utils import get_logger
from .models import EvaluationReport, ResumePacket, RunManifest, Scenario, WindTunnelReport
from .observability import ObservabilityTracker
from .resume import build_resume_packet
from .scenarios import get_scenario, list_scenarios
from .storage import LocalArtifactStore
from .wind_tunnel import build_wind_tunnel_report

LOGGER = get_logger("pipeline")


def run_scenario(scenario_id: str, base_dir: str | Path = "var/memoryvault") -> tuple[Path, RunManifest, ResumePacket, EvaluationReport]:
    scenario = get_scenario(scenario_id)
    return run_loaded_scenario(scenario, base_dir=base_dir)


def run_scenario_file(path: str | Path, base_dir: str | Path = "var/memoryvault") -> tuple[Path, RunManifest, ResumePacket, EvaluationReport]:
    scenario = load_scenario_file(path)
    return run_loaded_scenario(scenario, base_dir=base_dir)


def run_loaded_scenario(scenario: Scenario, base_dir: str | Path = "var/memoryvault") -> tuple[Path, RunManifest, ResumePacket, EvaluationReport]:
    tracker = ObservabilityTracker(mode="scenario", scenario=scenario)
    LOGGER.info("starting scenario run scenario_id=%s domain=%s", scenario.scenario_id, scenario.domain)

    stage_started = perf_counter()
    manifest = _build_manifest(scenario)
    tracker.record_stage("manifest", stage_started)

    stage_started = perf_counter()
    candidates = extract_candidates(scenario.events, fallback_goal=scenario.goal)
    tracker.record_stage("extract_candidates", stage_started)

    stage_started = perf_counter()
    packet = build_resume_packet(manifest, candidates)
    tracker.record_stage("build_resume_packet", stage_started)

    stage_started = perf_counter()
    evaluation = evaluate_resume_packet(scenario, packet)
    tracker.record_stage("evaluate_resume_packet", stage_started)

    stage_started = perf_counter()
    store = LocalArtifactStore(base_dir)
    run_dir = store.save_run(manifest, scenario, scenario.events, candidates, packet, evaluation)
    tracker.record_stage("save_run", stage_started)
    store.save_json_artifact(run_dir, "observability.json", tracker.build_report(manifest, packet, evaluation))
    LOGGER.info(
        "completed scenario run run_id=%s score=%.2f candidates=%d duration_ms=%d",
        manifest.run_id,
        evaluation.score,
        len(candidates),
        sum(tracker.stage_durations_ms.values()),
    )
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
    LOGGER.info("starting wind tunnel scenario_id=%s", scenario.scenario_id)
    run_dir, manifest, packet, evaluation = run_loaded_scenario(scenario, base_dir=base_dir)
    tracker = ObservabilityTracker(mode="wind_tunnel", scenario=scenario)
    stage_started = perf_counter()
    report = build_wind_tunnel_report(manifest, scenario, packet, evaluation)
    tracker.record_stage("build_wind_tunnel_report", stage_started)

    stage_started = perf_counter()
    store = LocalArtifactStore(base_dir)
    store.save_json_artifact(run_dir, "wind_tunnel_report.json", report)
    tracker.record_stage("save_wind_tunnel_artifacts", stage_started)
    store.save_json_artifact(run_dir, "wind_tunnel_observability.json", tracker.build_report(manifest, packet, evaluation, wind_tunnel=report))
    LOGGER.info(
        "completed wind tunnel run_id=%s baseline_score=%.2f variants=%d fragile_fields=%s",
        manifest.run_id,
        report.baseline_score,
        len(report.variant_results),
        ",".join(report.most_fragile_fields) or "none",
    )
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
