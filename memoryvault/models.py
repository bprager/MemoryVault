from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def to_dict(instance: Any) -> dict[str, Any]:
    return asdict(instance)


@dataclass(slots=True)
class TaskEvent:
    sequence: int
    actor: str
    text: str
    source_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExpectedItem:
    name: str
    category: str
    keywords: list[str]


@dataclass(slots=True)
class Scenario:
    scenario_id: str
    title: str
    domain: str
    goal: str
    interruption_point: str
    events: list[TaskEvent]
    expected_items: list[ExpectedItem]


@dataclass(slots=True)
class RunManifest:
    run_id: str
    scenario_id: str
    title: str
    domain: str
    goal: str
    interruption_point: str
    final_goal_guard: str
    created_at: str


@dataclass(slots=True)
class MemoryCandidate:
    category: str
    summary: str
    evidence_event_ids: list[int]
    confidence: float


@dataclass(slots=True)
class ResumePacket:
    run_id: str
    scenario_id: str
    final_goal_guard: str
    current_focus: list[str]
    constraints: list[str]
    decisions: list[str]
    blockers: list[str]
    assumptions: list[str]
    recent_failures: list[str]
    lessons: list[str]
    open_questions: list[str]
    sources: list[str]
    candidate_counts: dict[str, int]


@dataclass(slots=True)
class EvaluationCheck:
    name: str
    category: str
    passed: bool
    details: str
    expected_keywords: list[str]


@dataclass(slots=True)
class EvaluationReport:
    run_id: str
    scenario_id: str
    score: float
    checks: list[EvaluationCheck]
    improvement_actions: list[str]
    missing_categories: list[str]


@dataclass(slots=True)
class DurableFieldSuggestion:
    field_name: str
    source_category: str
    missing_run_count: int
    total_run_count: int
    coverage_ratio: float
    status: str
    rationale: str


@dataclass(slots=True)
class WindTunnelVariantResult:
    variant_id: str
    description: str
    removed_fields: list[str]
    is_composite: bool
    score: float
    score_delta: float
    failed_check_names: list[str]
    missing_categories: list[str]


@dataclass(slots=True)
class WindTunnelFieldImpact:
    field_name: str
    variants_tested: int
    average_score_delta: float
    max_score_delta: float
    worst_variant_id: str


@dataclass(slots=True)
class WindTunnelReport:
    run_id: str
    scenario_id: str
    baseline_score: float
    baseline_missing_categories: list[str]
    variant_results: list[WindTunnelVariantResult]
    field_impacts: list[WindTunnelFieldImpact]
    most_fragile_fields: list[str]


@dataclass(slots=True)
class RunObservability:
    run_id: str
    scenario_id: str
    mode: str
    started_at: str
    finished_at: str
    total_duration_ms: int
    stage_durations_ms: dict[str, int]
    event_count: int
    candidate_count: int
    source_count: int
    check_count: int
    score: float
    wind_tunnel_variant_count: int = 0
    most_fragile_fields: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkspaceProfile:
    workspace_id: str
    profile_version: str
    sample_scenario_ids: list[str]
    holdout_scenario_ids: list[str]
    task_families: list[str]
    domain_counts: dict[str, int]
    source_type_counts: dict[str, int]
    candidate_type_counts: dict[str, int]
    source_priority_order: list[str]
    benchmark_profiles: list[str]
    failure_markers: list[str]
    prefix_aliases: dict[str, list[str]]
    required_control_fields: list[str]
    candidate_fields: list[str]
    generation_notes: list[str]
    cue_phrases: dict[str, list[str]] = field(default_factory=dict)
    artifact_schema_version: str = "workspace_profile.v1"


@dataclass(slots=True)
class OnboardingScenarioResult:
    scenario_id: str
    title: str
    domain: str
    task_family: str
    baseline_score: float
    adapted_score: float
    score_delta: float
    baseline_missing_categories: list[str]
    adapted_missing_categories: list[str]
    improved_categories: list[str]
    cue_disabled_score: float = 0.0
    cue_score_delta: float = 0.0
    cue_helped_categories: list[str] = field(default_factory=list)


@dataclass(slots=True)
class OnboardingBenchmarkReport:
    workspace_id: str
    profile_version: str
    sample_scenario_ids: list[str]
    holdout_scenario_ids: list[str]
    baseline_average_score: float
    adapted_average_score: float
    average_score_delta: float
    gate_threshold: float
    gate_passed: bool
    scenario_results: list[OnboardingScenarioResult]
    recommended_actions: list[str]
    cue_disabled_average_score: float = 0.0
    cue_average_score_delta: float = 0.0
    artifact_schema_version: str = "onboarding_benchmark.v1"


@dataclass(slots=True)
class TransferBenchmarkReport:
    workspace_id: str
    profile_version: str
    source_sample_scenario_ids: list[str]
    source_holdout_scenario_ids: list[str]
    target_scenario_ids: list[str]
    source_task_families: list[str]
    target_task_families: list[str]
    baseline_average_score: float
    adapted_average_score: float
    average_score_delta: float
    gate_threshold: float
    gate_passed: bool
    scenario_results: list[OnboardingScenarioResult]
    recommended_actions: list[str]
    cue_disabled_average_score: float = 0.0
    cue_average_score_delta: float = 0.0
    artifact_schema_version: str = "transfer_benchmark.v1"


@dataclass(slots=True)
class ReleaseBenchmarkCaseResult:
    case_id: str
    title: str
    run_kind: str
    profile_version: str
    artifact_dir: str
    source_task_families: list[str]
    evaluation_task_families: list[str]
    scenario_count: int
    improved_scenario_count: int
    baseline_average_score: float
    cue_disabled_average_score: float
    adapted_average_score: float
    average_score_delta: float
    cue_average_score_delta: float
    gate_threshold: float
    gate_passed: bool
    recommended_actions: list[str]


@dataclass(slots=True)
class ReleaseBenchmarkReport:
    bundle_id: str
    bundle_version: str
    project_version: str
    created_at: str
    report_dir: str
    required_case_ids: list[str]
    task_families: list[str]
    total_case_count: int
    passed_case_count: int
    baseline_average_score: float
    cue_disabled_average_score: float
    adapted_average_score: float
    average_score_delta: float
    cue_average_score_delta: float
    gate_passed: bool
    case_results: list[ReleaseBenchmarkCaseResult]
    artifact_schema_version: str = "release_benchmark_report.v1"


@dataclass(slots=True)
class ProfileRefreshPlan:
    workspace_id: str
    relevant_record_count: int
    evidence_profile_versions: list[str]
    evidence_task_families: list[str]
    helped_categories: list[str]
    remaining_gap_categories: list[str]
    carried_failure_markers: list[str]
    carried_prefix_aliases: dict[str, list[str]]
    promoted_candidate_fields: list[str]
    source_priority_promotions: list[str]
    benchmark_profiles: list[str]
    actions: list[str]
    carried_cue_phrases: dict[str, list[str]] = field(default_factory=dict)


@dataclass(slots=True)
class ProfileRefreshReport:
    workspace_id: str
    initial_profile_version: str
    candidate_profile_version: str
    final_profile_version: str
    candidate_changed: bool
    candidate_accepted: bool
    relevant_record_count: int
    evidence_profile_versions: list[str]
    evidence_task_families: list[str]
    helped_categories: list[str]
    remaining_gap_categories: list[str]
    carried_failure_markers: list[str]
    carried_prefix_aliases: dict[str, list[str]]
    promoted_candidate_fields: list[str]
    source_priority_promotions: list[str]
    initial_adapted_average_score: float
    candidate_adapted_average_score: float
    final_adapted_average_score: float
    score_delta: float
    actions: list[str]
    carried_cue_phrases: dict[str, list[str]] = field(default_factory=dict)


@dataclass(slots=True)
class ImprovementInsight:
    created_at: str
    workspace_id: str
    profile_version: str
    run_kind: str
    signal: str
    summary: str
    categories: list[str]
    scenario_ids: list[str]


@dataclass(slots=True)
class StrategyRunRecord:
    record_id: str
    created_at: str
    run_kind: str
    workspace_id: str
    profile_version: str
    artifact_dir: str
    source_task_families: list[str]
    evaluation_task_families: list[str]
    source_domains: list[str]
    evaluation_domains: list[str]
    sample_count: int
    holdout_count: int
    scenario_count: int
    event_count: int
    duration_ms: int
    baseline_average_score: float
    adapted_average_score: float
    average_score_delta: float
    gate_threshold: float
    gate_passed: bool
    cue_disabled_average_score: float = 0.0
    cue_average_score_delta: float = 0.0
    improved_scenario_count: int = 0
    degraded_scenario_count: int = 0
    improved_category_counts: dict[str, int] = field(default_factory=dict)
    remaining_gap_category_counts: dict[str, int] = field(default_factory=dict)
    cue_helped_category_counts: dict[str, int] = field(default_factory=dict)
    evaluation_task_family_metrics: dict[str, dict[str, float | int]] = field(default_factory=dict)


@dataclass(slots=True)
class StrategyRunKindSummary:
    run_kind: str
    record_count: int
    average_baseline_score: float
    average_adapted_score: float
    average_score_delta: float
    average_duration_ms: float
    gate_pass_rate: float
    average_events_per_scenario: float
    average_duration_per_scenario_ms: float
    average_duration_per_event_ms: float


@dataclass(slots=True)
class StrategyCategorySummary:
    category: str
    helped_run_count: int
    helped_scenario_count: int
    remaining_gap_run_count: int
    remaining_gap_scenario_count: int
    cue_helped_run_count: int = 0
    cue_helped_scenario_count: int = 0
    cue_average_score_delta: float = 0.0
    helped_task_families: list[str] = field(default_factory=list)


@dataclass(slots=True)
class StrategyTaskFamilySummary:
    task_family: str
    record_count: int
    scenario_count: int
    average_baseline_score: float
    average_adapted_score: float
    average_score_delta: float
    improvement_rate: float
    gate_pass_rate: float


@dataclass(slots=True)
class StrategyProfileSummary:
    profile_version: str
    record_count: int
    first_seen_at: str
    last_seen_at: str
    workspace_ids: list[str]
    run_kinds: list[str]
    source_task_families: list[str]
    evaluation_task_families: list[str]
    average_score_delta: float
    gate_pass_rate: float


@dataclass(slots=True)
class StrategyWorkspaceLineage:
    workspace_id: str
    record_count: int
    first_seen_at: str
    last_seen_at: str
    profile_versions: list[str]
    latest_profile_version: str
    run_kinds: list[str]
    average_score_delta: float


@dataclass(slots=True)
class StrategyTrackerSummary:
    total_records: int
    latest_profile_version: str | None
    task_families: list[str]
    run_kind_summaries: list[StrategyRunKindSummary]
    category_summaries: list[StrategyCategorySummary]
    task_family_summaries: list[StrategyTaskFamilySummary]
    profile_summaries: list[StrategyProfileSummary]
    workspace_lineages: list[StrategyWorkspaceLineage]
