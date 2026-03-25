from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter

from .models import EvaluationReport, ResumePacket, RunManifest, RunObservability, Scenario, WindTunnelReport


class ObservabilityTracker:
    def __init__(self, mode: str, scenario: Scenario) -> None:
        self.mode = mode
        self.scenario = scenario
        self.started_at = datetime.now(timezone.utc)
        self.started_perf = perf_counter()
        self.stage_durations_ms: dict[str, int] = {}

    def record_stage(self, stage_name: str, started_perf: float) -> None:
        self.stage_durations_ms[stage_name] = int(round((perf_counter() - started_perf) * 1000))

    def build_report(
        self,
        manifest: RunManifest,
        packet: ResumePacket,
        evaluation: EvaluationReport,
        wind_tunnel: WindTunnelReport | None = None,
    ) -> RunObservability:
        finished_at = datetime.now(timezone.utc)
        total_duration_ms = int(round((perf_counter() - self.started_perf) * 1000))
        return RunObservability(
            run_id=manifest.run_id,
            scenario_id=manifest.scenario_id,
            mode=self.mode,
            started_at=self.started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            total_duration_ms=total_duration_ms,
            stage_durations_ms=dict(self.stage_durations_ms),
            event_count=len(self.scenario.events),
            candidate_count=sum(packet.candidate_counts.values()),
            source_count=len(packet.sources),
            check_count=len(evaluation.checks),
            score=evaluation.score,
            wind_tunnel_variant_count=0 if wind_tunnel is None else len(wind_tunnel.variant_results),
            most_fragile_fields=[] if wind_tunnel is None else list(wind_tunnel.most_fragile_fields),
        )
