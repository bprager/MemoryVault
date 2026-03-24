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
