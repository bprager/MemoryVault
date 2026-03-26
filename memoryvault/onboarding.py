from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from time import perf_counter
from typing import Iterable, Mapping
from uuid import uuid4

from .evaluation import evaluate_resume_packet
from .extractor import DEFAULT_PREFIX_TO_CATEGORY, extract_candidates
from .importer import load_scenarios_from_directory
from .logging_utils import get_logger
from .models import (
    EvaluationReport,
    ImprovementInsight,
    OnboardingBenchmarkReport,
    OnboardingScenarioResult,
    ProfileRefreshPlan,
    ProfileRefreshReport,
    RunManifest,
    Scenario,
    StrategyCategorySummary,
    StrategyProfileSummary,
    StrategyRunKindSummary,
    StrategyRunRecord,
    StrategyTaskFamilySummary,
    StrategyTrackerSummary,
    StrategyWorkspaceLineage,
    TransferBenchmarkReport,
    WorkspaceProfile,
)
from .resume import DEFAULT_FAILURE_MARKERS, build_resume_packet
from .storage import LocalArtifactStore

LOGGER = get_logger("onboarding")

REQUIRED_CONTROL_FIELDS = [
    "goal",
    "plan",
    "active_step",
    "constraint",
    "decision",
    "blocker",
    "failure",
    "lesson",
    "source_ref",
]

DEFAULT_SOURCE_PRIORITY = [
    "tests",
    "architecture_docs",
    "readme",
    "task_traces",
    "smoke_tests",
    "tool_logs",
    "source_files",
    "other",
]

LEARNABLE_FAILURE_MARKERS = frozenset(
    {
        "blocked",
        "drifted",
        "incomplete",
        "invalid",
        "mismatch",
        "missing",
        "regressed",
        "stale",
        "timed out",
        "timeout",
        "unavailable",
        "weak",
    }
)

LEARNABLE_PREFIX_ALIASES = {
    "current_focus": ("focus", "resume", "todo"),
    "constraint": ("guardrail", "rule"),
    "lesson": ("observation", "takeaway"),
    "open_question": ("open question",),
    "source": ("evidence", "reference"),
}

LEARNABLE_CUE_CATEGORIES = frozenset(
    {
        "blocker",
        "constraint",
        "current_focus",
        "decision",
        "lesson",
        "open_question",
        "source",
    }
)

CANONICAL_CUE_FRAGMENTS = {
    "blocker": (
        "waiting on",
        "blocked on",
        "blocked by",
        "cannot continue until",
    ),
    "constraint": (
        "stay within",
        "do not",
        "must keep",
        "only after",
        "keep within",
    ),
    "current_focus": (
        "before anything else",
        "start by",
        "focus on",
        "next move is",
        "next action is",
    ),
    "decision": (
        "decided to",
        "so we will",
        "instead we will",
    ),
    "lesson": (
        "this means",
        "learned that",
        "the lesson is",
        "takeaway is",
    ),
    "open_question": (
        "still unclear whether",
        "need to verify whether",
        "not yet clear whether",
        "open question is",
    ),
    "source": (
        "according to",
        "based on",
        "evidence from",
        "cited in",
    ),
}

DOMAIN_BENCHMARK_PROFILES = {
    "coding": "swe_bench_like",
    "research": "qasper_grounding",
    "tool_use": "taskbench_tool_use",
    "conversation": "longmemeval_like",
}

CATEGORY_TO_STARTER_FIELD = {
    "assumption": "assumptions",
    "blocker": "blockers",
    "decision": "decisions",
    "lesson": "lessons",
    "open_question": "open_questions",
}

KNOWN_TASK_FAMILY_PREFIXES = (
    "hf_conversation_bench",
    "hf_qasper",
    "hf_swe_bench_verified",
    "hf_taskbench",
    "longmemeval_like",
    "qasper_like",
    "swe_bench_like",
    "taskbench_like",
)

REFRESHABLE_ALIAS_CATEGORIES = frozenset(
    {
        "constraint",
        "current_focus",
        "lesson",
        "open_question",
        "source",
    }
)

REFRESHABLE_CUE_CATEGORIES = LEARNABLE_CUE_CATEGORIES

CATEGORY_TO_REFRESH_FIELD = {
    "assumption": "assumptions",
    "blocker": "blockers",
    "constraint": "constraints",
    "current_focus": "current_focus",
    "decision": "decisions",
    "lesson": "lessons",
    "open_question": "open_questions",
    "recent_failures": "recent_failures",
    "source": "sources",
}


def onboard_directory(
    path: str | Path,
    *,
    base_dir: str | Path = "var/memoryvault",
    workspace_id: str | None = None,
    sample_size: int | None = None,
    gate_threshold: float = 0.9,
) -> tuple[Path, WorkspaceProfile, OnboardingBenchmarkReport]:
    scenarios = load_scenarios_from_directory(path)
    resolved_workspace_id = workspace_id or Path(path).name.replace(" ", "_")
    return onboard_scenarios(
        scenarios,
        base_dir=base_dir,
        workspace_id=resolved_workspace_id,
        sample_size=sample_size,
        gate_threshold=gate_threshold,
    )


def onboard_scenarios(
    scenarios: list[Scenario],
    *,
    base_dir: str | Path = "var/memoryvault",
    workspace_id: str,
    sample_size: int | None = None,
    gate_threshold: float = 0.9,
) -> tuple[Path, WorkspaceProfile, OnboardingBenchmarkReport]:
    if not scenarios:
        raise ValueError("at least one scenario is required for onboarding")

    tracker_started = perf_counter()
    sample_scenarios, holdout_scenarios = split_representative_sample(scenarios, sample_size=sample_size)
    profile = build_workspace_profile(workspace_id, sample_scenarios, holdout_scenarios)
    benchmark = run_onboarding_benchmark(profile, holdout_scenarios, gate_threshold=gate_threshold)

    store = LocalArtifactStore(base_dir)
    run_dir = _create_onboarding_dir(base_dir, workspace_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    store.save_json_artifact(run_dir, "workspace_profile.json", profile)
    store.save_json_artifact(run_dir, "onboarding_benchmark.json", benchmark)
    store.save_json_artifact(
        run_dir,
        "onboarding_manifest.json",
        {
            "workspace_id": workspace_id,
            "sample_scenario_ids": [scenario.scenario_id for scenario in sample_scenarios],
            "holdout_scenario_ids": [scenario.scenario_id for scenario in holdout_scenarios],
        },
    )
    (run_dir / "starter_pack.yaml").write_text(render_starter_pack_yaml(profile), encoding="utf-8")
    duration_ms = int(round((perf_counter() - tracker_started) * 1000))
    strategy_record = build_strategy_record(
        run_kind="onboarding",
        workspace_id=workspace_id,
        profile=profile,
        artifact_dir=run_dir,
        source_scenarios=sample_scenarios,
        evaluation_scenarios=holdout_scenarios,
        benchmark=benchmark,
        duration_ms=duration_ms,
    )
    improvement_insights = build_improvement_insights(
        workspace_id=workspace_id,
        profile=profile,
        run_kind="onboarding",
        scenario_results=benchmark.scenario_results,
        recommended_actions=benchmark.recommended_actions,
    )
    store.save_json_artifact(run_dir, "strategy_record.json", strategy_record)
    store.save_json_artifact(run_dir, "improvement_insights.json", improvement_insights)
    store.append_jsonl_artifact("strategy_tracker.jsonl", strategy_record)
    for insight in improvement_insights:
        store.append_jsonl_artifact("improvement_insights.jsonl", insight)
    store.save_json_artifact(
        run_dir,
        "onboarding_observability.json",
        {
            "workspace_id": workspace_id,
            "sample_count": len(sample_scenarios),
            "holdout_count": len(holdout_scenarios),
            "duration_ms": duration_ms,
            "gate_passed": benchmark.gate_passed,
            "average_score_delta": benchmark.average_score_delta,
            "profile_version": profile.profile_version,
        },
    )
    LOGGER.info(
        "completed onboarding workspace_id=%s sample_count=%d holdout_count=%d delta=%.2f gate_passed=%s",
        workspace_id,
        len(sample_scenarios),
        len(holdout_scenarios),
        benchmark.average_score_delta,
        benchmark.gate_passed,
    )
    return run_dir, profile, benchmark


def refresh_directory(
    path: str | Path,
    *,
    base_dir: str | Path = "var/memoryvault",
    workspace_id: str | None = None,
    sample_size: int | None = None,
    gate_threshold: float = 0.9,
) -> tuple[Path, WorkspaceProfile, OnboardingBenchmarkReport, ProfileRefreshReport]:
    scenarios = load_scenarios_from_directory(path)
    resolved_workspace_id = workspace_id or Path(path).name.replace(" ", "_")
    return refresh_scenarios(
        scenarios,
        base_dir=base_dir,
        workspace_id=resolved_workspace_id,
        sample_size=sample_size,
        gate_threshold=gate_threshold,
    )


def refresh_scenarios(
    scenarios: list[Scenario],
    *,
    base_dir: str | Path = "var/memoryvault",
    workspace_id: str,
    sample_size: int | None = None,
    gate_threshold: float = 0.9,
) -> tuple[Path, WorkspaceProfile, OnboardingBenchmarkReport, ProfileRefreshReport]:
    if not scenarios:
        raise ValueError("at least one scenario is required for refresh")

    tracker_started = perf_counter()
    sample_scenarios, holdout_scenarios = split_representative_sample(scenarios, sample_size=sample_size)
    initial_profile = build_workspace_profile(workspace_id, sample_scenarios, holdout_scenarios)
    initial_benchmark = run_onboarding_benchmark(initial_profile, holdout_scenarios, gate_threshold=gate_threshold)
    refresh_plan = build_profile_refresh_plan(base_dir, workspace_id, initial_profile)
    candidate_profile = apply_profile_refresh_plan(initial_profile, refresh_plan)
    candidate_benchmark = run_onboarding_benchmark(candidate_profile, holdout_scenarios, gate_threshold=gate_threshold)

    candidate_changed = candidate_profile.profile_version != initial_profile.profile_version
    candidate_accepted = should_accept_refresh_candidate(
        initial_benchmark,
        candidate_benchmark,
        candidate_changed=candidate_changed,
    )
    final_profile = candidate_profile if candidate_accepted else initial_profile
    final_benchmark = candidate_benchmark if candidate_accepted else initial_benchmark
    refresh_report = build_profile_refresh_report(
        initial_profile=initial_profile,
        candidate_profile=candidate_profile,
        final_profile=final_profile,
        refresh_plan=refresh_plan,
        initial_benchmark=initial_benchmark,
        candidate_benchmark=candidate_benchmark,
        candidate_changed=candidate_changed,
        candidate_accepted=candidate_accepted,
    )

    store = LocalArtifactStore(base_dir)
    run_dir = _create_refresh_dir(base_dir, workspace_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    store.save_json_artifact(run_dir, "initial_workspace_profile.json", initial_profile)
    store.save_json_artifact(run_dir, "initial_onboarding_benchmark.json", initial_benchmark)
    store.save_json_artifact(run_dir, "refresh_plan.json", refresh_plan)
    store.save_json_artifact(run_dir, "refresh_candidate_profile.json", candidate_profile)
    store.save_json_artifact(run_dir, "refresh_candidate_benchmark.json", candidate_benchmark)
    store.save_json_artifact(run_dir, "refresh_report.json", refresh_report)
    store.save_json_artifact(run_dir, "workspace_profile.json", final_profile)
    store.save_json_artifact(run_dir, "onboarding_benchmark.json", final_benchmark)
    store.save_json_artifact(
        run_dir,
        "refresh_manifest.json",
        {
            "workspace_id": workspace_id,
            "sample_scenario_ids": [scenario.scenario_id for scenario in sample_scenarios],
            "holdout_scenario_ids": [scenario.scenario_id for scenario in holdout_scenarios],
            "initial_profile_version": initial_profile.profile_version,
            "candidate_profile_version": candidate_profile.profile_version,
            "final_profile_version": final_profile.profile_version,
        },
    )
    (run_dir / "starter_pack.yaml").write_text(render_starter_pack_yaml(final_profile), encoding="utf-8")
    duration_ms = int(round((perf_counter() - tracker_started) * 1000))
    strategy_record = build_strategy_record(
        run_kind="refresh",
        workspace_id=workspace_id,
        profile=final_profile,
        artifact_dir=run_dir,
        source_scenarios=sample_scenarios,
        evaluation_scenarios=holdout_scenarios,
        benchmark=final_benchmark,
        duration_ms=duration_ms,
    )
    improvement_insights = build_improvement_insights(
        workspace_id=workspace_id,
        profile=final_profile,
        run_kind="refresh",
        scenario_results=final_benchmark.scenario_results,
        recommended_actions=refresh_report.actions,
    )
    store.save_json_artifact(run_dir, "strategy_record.json", strategy_record)
    store.save_json_artifact(run_dir, "improvement_insights.json", improvement_insights)
    store.append_jsonl_artifact("strategy_tracker.jsonl", strategy_record)
    for insight in improvement_insights:
        store.append_jsonl_artifact("improvement_insights.jsonl", insight)
    store.save_json_artifact(
        run_dir,
        "refresh_observability.json",
        {
            "workspace_id": workspace_id,
            "sample_count": len(sample_scenarios),
            "holdout_count": len(holdout_scenarios),
            "duration_ms": duration_ms,
            "candidate_changed": candidate_changed,
            "candidate_accepted": candidate_accepted,
            "initial_profile_version": initial_profile.profile_version,
            "final_profile_version": final_profile.profile_version,
            "initial_adapted_average_score": initial_benchmark.adapted_average_score,
            "final_adapted_average_score": final_benchmark.adapted_average_score,
        },
    )
    LOGGER.info(
        "completed refresh workspace_id=%s evidence_records=%d changed=%s accepted=%s delta=%.2f",
        workspace_id,
        refresh_plan.relevant_record_count,
        candidate_changed,
        candidate_accepted,
        refresh_report.score_delta,
    )
    return run_dir, final_profile, final_benchmark, refresh_report


def transfer_directory(
    source_path: str | Path,
    target_path: str | Path,
    *,
    base_dir: str | Path = "var/memoryvault",
    workspace_id: str | None = None,
    sample_size: int | None = None,
    gate_threshold: float = 0.85,
) -> tuple[Path, WorkspaceProfile, OnboardingBenchmarkReport, TransferBenchmarkReport]:
    source_scenarios = load_scenarios_from_directory(source_path)
    target_scenarios = load_scenarios_from_directory(target_path)
    resolved_workspace_id = workspace_id or f"{Path(source_path).name}_to_{Path(target_path).name}"
    return transfer_scenarios(
        source_scenarios,
        target_scenarios,
        base_dir=base_dir,
        workspace_id=resolved_workspace_id,
        sample_size=sample_size,
        gate_threshold=gate_threshold,
    )


def transfer_scenarios(
    source_scenarios: list[Scenario],
    target_scenarios: list[Scenario],
    *,
    base_dir: str | Path = "var/memoryvault",
    workspace_id: str,
    sample_size: int | None = None,
    gate_threshold: float = 0.85,
) -> tuple[Path, WorkspaceProfile, OnboardingBenchmarkReport, TransferBenchmarkReport]:
    if not source_scenarios:
        raise ValueError("at least one source scenario is required for transfer benchmarking")
    if not target_scenarios:
        raise ValueError("at least one target scenario is required for transfer benchmarking")

    tracker_started = perf_counter()
    sample_scenarios, holdout_scenarios = split_representative_sample(source_scenarios, sample_size=sample_size)
    profile = build_workspace_profile(workspace_id, sample_scenarios, holdout_scenarios)
    source_benchmark = run_onboarding_benchmark(profile, holdout_scenarios, gate_threshold=gate_threshold)
    transfer_benchmark = run_transfer_benchmark(profile, target_scenarios, gate_threshold=gate_threshold)

    store = LocalArtifactStore(base_dir)
    run_dir = _create_transfer_dir(base_dir, workspace_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    store.save_json_artifact(run_dir, "workspace_profile.json", profile)
    store.save_json_artifact(run_dir, "source_onboarding_benchmark.json", source_benchmark)
    store.save_json_artifact(run_dir, "transfer_benchmark.json", transfer_benchmark)
    store.save_json_artifact(
        run_dir,
        "transfer_manifest.json",
        {
            "workspace_id": workspace_id,
            "profile_version": profile.profile_version,
            "source_sample_scenario_ids": [scenario.scenario_id for scenario in sample_scenarios],
            "source_holdout_scenario_ids": [scenario.scenario_id for scenario in holdout_scenarios],
            "target_scenario_ids": [scenario.scenario_id for scenario in target_scenarios],
            "source_task_families": sorted(infer_task_families(sample_scenarios + holdout_scenarios)),
            "target_task_families": sorted(infer_task_families(target_scenarios)),
        },
    )
    (run_dir / "starter_pack.yaml").write_text(render_starter_pack_yaml(profile), encoding="utf-8")
    duration_ms = int(round((perf_counter() - tracker_started) * 1000))
    strategy_record = build_strategy_record(
        run_kind="transfer",
        workspace_id=workspace_id,
        profile=profile,
        artifact_dir=run_dir,
        source_scenarios=sample_scenarios + holdout_scenarios,
        evaluation_scenarios=target_scenarios,
        benchmark=transfer_benchmark,
        duration_ms=duration_ms,
    )
    improvement_insights = build_improvement_insights(
        workspace_id=workspace_id,
        profile=profile,
        run_kind="transfer",
        scenario_results=transfer_benchmark.scenario_results,
        recommended_actions=transfer_benchmark.recommended_actions,
    )
    store.save_json_artifact(run_dir, "strategy_record.json", strategy_record)
    store.save_json_artifact(run_dir, "improvement_insights.json", improvement_insights)
    store.append_jsonl_artifact("strategy_tracker.jsonl", strategy_record)
    for insight in improvement_insights:
        store.append_jsonl_artifact("improvement_insights.jsonl", insight)
    store.save_json_artifact(
        run_dir,
        "transfer_observability.json",
        {
            "workspace_id": workspace_id,
            "profile_version": profile.profile_version,
            "source_sample_count": len(sample_scenarios),
            "source_holdout_count": len(holdout_scenarios),
            "target_count": len(target_scenarios),
            "duration_ms": duration_ms,
            "gate_passed": transfer_benchmark.gate_passed,
            "average_score_delta": transfer_benchmark.average_score_delta,
        },
    )
    LOGGER.info(
        "completed transfer benchmark workspace_id=%s source_count=%d target_count=%d delta=%.2f gate_passed=%s",
        workspace_id,
        len(source_scenarios),
        len(target_scenarios),
        transfer_benchmark.average_score_delta,
        transfer_benchmark.gate_passed,
    )
    return run_dir, profile, source_benchmark, transfer_benchmark


def split_representative_sample(
    scenarios: list[Scenario],
    sample_size: int | None = None,
) -> tuple[list[Scenario], list[Scenario]]:
    ordered = sorted(scenarios, key=lambda item: (item.domain, item.scenario_id))
    if len(ordered) == 1:
        return ordered, []

    target_size = sample_size if sample_size is not None else max(1, min(len(ordered) - 1, round(len(ordered) * 0.67)))
    target_size = max(1, min(target_size, len(ordered) - 1))

    selected_ids: set[str] = set()
    sample: list[Scenario] = []
    covered_domains: set[str] = set()

    for scenario in ordered:
        if len(sample) >= target_size:
            break
        if scenario.domain in covered_domains:
            continue
        sample.append(scenario)
        selected_ids.add(scenario.scenario_id)
        covered_domains.add(scenario.domain)

    remaining = sorted(
        (scenario for scenario in ordered if scenario.scenario_id not in selected_ids),
        key=lambda item: (-len(item.events), item.scenario_id),
    )
    for scenario in remaining:
        if len(sample) >= target_size:
            break
        sample.append(scenario)
        selected_ids.add(scenario.scenario_id)

    holdout = [scenario for scenario in ordered if scenario.scenario_id not in selected_ids]
    return sample, holdout


def build_workspace_profile(
    workspace_id: str,
    sample_scenarios: list[Scenario],
    holdout_scenarios: list[Scenario],
) -> WorkspaceProfile:
    domain_counts = Counter(scenario.domain for scenario in sample_scenarios)
    source_type_counts: Counter[str] = Counter()

    for scenario in sample_scenarios:
        for event in scenario.events:
            for source_ref in event.source_refs:
                source_type_counts[classify_source_ref(source_ref)] += 1

    failure_markers = sorted(
        {
            marker.lower()
            for marker in DEFAULT_FAILURE_MARKERS
        }
        | learn_failure_markers(sample_scenarios)
    )
    prefix_aliases = learn_prefix_aliases(sample_scenarios)
    cue_phrases = learn_cue_phrases(sample_scenarios)
    benchmark_profiles = infer_benchmark_profiles(sample_scenarios)
    source_priority_order = infer_source_priority_order(source_type_counts)
    candidate_type_counts: Counter[str] = Counter()
    for scenario in sample_scenarios:
        for candidate in extract_candidates(
            scenario.events,
            fallback_goal=scenario.goal,
            prefix_aliases=prefix_aliases,
            cue_phrases=cue_phrases,
            source_priority_order=source_priority_order,
        ):
            candidate_type_counts[candidate.category] += 1
    candidate_fields = infer_candidate_fields(candidate_type_counts)
    task_families = sorted(infer_task_families(sample_scenarios + holdout_scenarios))

    generation_notes = [
        f"Built from {len(sample_scenarios)} representative sample traces.",
        "Starter pack is optional and safe to regenerate.",
        "Profile-adapted failure markers, learned event-label aliases, and content cue phrases influence held-out scoring.",
    ]
    if holdout_scenarios:
        generation_notes.append(f"Held out {len(holdout_scenarios)} traces for onboarding validation.")
    else:
        generation_notes.append("No held-out traces were available, so onboarding validation is incomplete.")

    sample_scenario_ids = [scenario.scenario_id for scenario in sample_scenarios]
    holdout_scenario_ids = [scenario.scenario_id for scenario in holdout_scenarios]
    domain_count_map = dict(sorted(domain_counts.items()))
    source_type_count_map = dict(sorted(source_type_counts.items()))
    candidate_type_count_map = dict(sorted(candidate_type_counts.items()))
    required_control_fields = list(REQUIRED_CONTROL_FIELDS)
    profile_payload: dict[str, object] = {
        "sample_scenario_ids": sample_scenario_ids,
        "holdout_scenario_ids": holdout_scenario_ids,
        "task_families": task_families,
        "domain_counts": domain_count_map,
        "source_type_counts": source_type_count_map,
        "candidate_type_counts": candidate_type_count_map,
        "source_priority_order": source_priority_order,
        "benchmark_profiles": benchmark_profiles,
        "failure_markers": failure_markers,
        "prefix_aliases": prefix_aliases,
        "cue_phrases": cue_phrases,
        "required_control_fields": required_control_fields,
        "candidate_fields": candidate_fields,
        "generation_notes": generation_notes,
    }
    profile_version = compute_profile_version(profile_payload)

    return WorkspaceProfile(
        workspace_id=workspace_id,
        profile_version=profile_version,
        sample_scenario_ids=sample_scenario_ids,
        holdout_scenario_ids=holdout_scenario_ids,
        task_families=task_families,
        domain_counts=domain_count_map,
        source_type_counts=source_type_count_map,
        candidate_type_counts=candidate_type_count_map,
        source_priority_order=source_priority_order,
        benchmark_profiles=benchmark_profiles,
        failure_markers=failure_markers,
        prefix_aliases=prefix_aliases,
        cue_phrases=cue_phrases,
        required_control_fields=required_control_fields,
        candidate_fields=candidate_fields,
        generation_notes=generation_notes,
    )


def build_profile_refresh_plan(
    base_dir: str | Path,
    workspace_id: str,
    profile: WorkspaceProfile,
) -> ProfileRefreshPlan:
    relevant_records = select_relevant_strategy_records(base_dir, workspace_id, profile.task_families)
    if not relevant_records:
        return ProfileRefreshPlan(
            workspace_id=workspace_id,
            relevant_record_count=0,
            evidence_profile_versions=[],
            evidence_task_families=[],
            helped_categories=[],
            remaining_gap_categories=[],
            carried_failure_markers=[],
            carried_prefix_aliases={},
            promoted_candidate_fields=[],
            source_priority_promotions=[],
            benchmark_profiles=[],
            actions=["No prior successful strategy evidence matched this workspace or task family."],
            carried_cue_phrases={},
        )

    summary = summarize_strategy_records_for_records(relevant_records)
    profiles_by_version = load_workspace_profiles_for_records(relevant_records)
    ordered_profile_versions = [
        item.profile_version
        for item in summary.profile_summaries
        if item.profile_version in profiles_by_version
    ]
    evidence_profiles = [profiles_by_version[version] for version in ordered_profile_versions]
    helped_categories = [
        item.category
        for item in summary.category_summaries
        if item.helped_scenario_count > 0
    ]
    remaining_gap_categories = [
        item.category
        for item in summary.category_summaries
        if item.remaining_gap_scenario_count > 0
    ]
    relevant_categories = set(helped_categories) | set(remaining_gap_categories)

    carried_failure_markers: list[str] = []
    if "recent_failures" in relevant_categories:
        carried_failure_markers = sorted(
            {
                marker
                for evidence_profile in evidence_profiles
                for marker in evidence_profile.failure_markers
            }
        )

    carried_prefix_aliases: dict[str, list[str]] = {}
    for category in sorted(relevant_categories & REFRESHABLE_ALIAS_CATEGORIES):
        aliases = ordered_unique(
            alias
            for evidence_profile in evidence_profiles
            for alias in evidence_profile.prefix_aliases.get(category, [])
        )
        if aliases:
            carried_prefix_aliases[category] = aliases

    carried_cue_phrases: dict[str, list[str]] = {}
    for category in sorted(relevant_categories & REFRESHABLE_CUE_CATEGORIES):
        phrases = ordered_unique(
            phrase
            for evidence_profile in evidence_profiles
            for phrase in evidence_profile.cue_phrases.get(category, [])
        )
        if phrases:
            carried_cue_phrases[category] = phrases

    promoted_candidate_fields = sorted(
        {
            field_name
            for category in relevant_categories
            for field_name in [CATEGORY_TO_REFRESH_FIELD.get(category)]
            if field_name is not None
        }
    )
    source_priority_promotions = ordered_unique(
        source_type
        for evidence_profile in evidence_profiles
        for source_type in evidence_profile.source_priority_order[:3]
    )
    benchmark_profiles = ordered_unique(
        benchmark_profile
        for evidence_profile in evidence_profiles
        for benchmark_profile in evidence_profile.benchmark_profiles
    )
    evidence_task_families = [
        item.task_family
        for item in summary.task_family_summaries
        if item.average_score_delta > 0.0 and item.gate_pass_rate >= 0.5
    ]

    actions = [
        f"Reuse successful profile evidence from {len(ordered_profile_versions)} prior profile versions.",
    ]
    if carried_prefix_aliases:
        actions.append(
            "Carry forward learned aliases for " + ", ".join(sorted(carried_prefix_aliases)) + "."
        )
    if carried_failure_markers:
        actions.append("Carry forward learned failure markers from prior successful profiles.")
    if carried_cue_phrases:
        actions.append(
            "Carry forward learned content cues for " + ", ".join(sorted(carried_cue_phrases)) + "."
        )
    if promoted_candidate_fields:
        actions.append(
            "Promote candidate starter-pack fields from tracker evidence: "
            + ", ".join(promoted_candidate_fields)
            + "."
        )
    if "source" in relevant_categories and source_priority_promotions:
        actions.append(
            "Promote source types to the front of the priority order: "
            + ", ".join(source_priority_promotions[:3])
            + "."
        )

    return ProfileRefreshPlan(
        workspace_id=workspace_id,
        relevant_record_count=len(relevant_records),
        evidence_profile_versions=ordered_profile_versions,
        evidence_task_families=evidence_task_families,
        helped_categories=helped_categories,
        remaining_gap_categories=remaining_gap_categories,
        carried_failure_markers=carried_failure_markers,
        carried_prefix_aliases=carried_prefix_aliases,
        promoted_candidate_fields=promoted_candidate_fields,
        source_priority_promotions=source_priority_promotions,
        benchmark_profiles=benchmark_profiles,
        actions=actions,
        carried_cue_phrases=carried_cue_phrases,
    )


def apply_profile_refresh_plan(
    profile: WorkspaceProfile,
    refresh_plan: ProfileRefreshPlan,
) -> WorkspaceProfile:
    if refresh_plan.relevant_record_count == 0:
        return profile

    failure_markers = sorted(set(profile.failure_markers) | set(refresh_plan.carried_failure_markers))
    prefix_aliases = merge_prefix_aliases(profile.prefix_aliases, refresh_plan.carried_prefix_aliases)
    cue_phrases = merge_phrase_map(profile.cue_phrases, refresh_plan.carried_cue_phrases)
    candidate_fields = sorted(set(profile.candidate_fields) | set(refresh_plan.promoted_candidate_fields))
    source_priority_order = merge_priority_order(
        refresh_plan.source_priority_promotions,
        profile.source_priority_order,
    )
    benchmark_profiles = ordered_unique(profile.benchmark_profiles + refresh_plan.benchmark_profiles)

    changed = (
        failure_markers != profile.failure_markers
        or prefix_aliases != profile.prefix_aliases
        or cue_phrases != profile.cue_phrases
        or candidate_fields != profile.candidate_fields
        or source_priority_order != profile.source_priority_order
        or benchmark_profiles != profile.benchmark_profiles
    )
    if not changed:
        return profile

    generation_notes = list(profile.generation_notes) + [
        f"Refreshed using {refresh_plan.relevant_record_count} prior strategy runs.",
        "Refresh candidate was generated from tracker rollups and must still clear the held-out benchmark.",
    ]
    profile_payload: dict[str, object] = {
        "sample_scenario_ids": list(profile.sample_scenario_ids),
        "holdout_scenario_ids": list(profile.holdout_scenario_ids),
        "task_families": list(profile.task_families),
        "domain_counts": dict(profile.domain_counts),
        "source_type_counts": dict(profile.source_type_counts),
        "candidate_type_counts": dict(profile.candidate_type_counts),
        "source_priority_order": source_priority_order,
        "benchmark_profiles": benchmark_profiles,
        "failure_markers": failure_markers,
        "prefix_aliases": prefix_aliases,
        "cue_phrases": cue_phrases,
        "required_control_fields": list(profile.required_control_fields),
        "candidate_fields": candidate_fields,
        "generation_notes": generation_notes,
    }
    profile_version = compute_profile_version(profile_payload)
    return WorkspaceProfile(
        workspace_id=profile.workspace_id,
        profile_version=profile_version,
        sample_scenario_ids=list(profile.sample_scenario_ids),
        holdout_scenario_ids=list(profile.holdout_scenario_ids),
        task_families=list(profile.task_families),
        domain_counts=dict(profile.domain_counts),
        source_type_counts=dict(profile.source_type_counts),
        candidate_type_counts=dict(profile.candidate_type_counts),
        source_priority_order=source_priority_order,
        benchmark_profiles=benchmark_profiles,
        failure_markers=failure_markers,
        prefix_aliases=prefix_aliases,
        cue_phrases=cue_phrases,
        required_control_fields=list(profile.required_control_fields),
        candidate_fields=candidate_fields,
        generation_notes=generation_notes,
    )


def should_accept_refresh_candidate(
    initial_benchmark: OnboardingBenchmarkReport,
    candidate_benchmark: OnboardingBenchmarkReport,
    *,
    candidate_changed: bool,
) -> bool:
    if not candidate_changed:
        return False
    if candidate_benchmark.adapted_average_score > initial_benchmark.adapted_average_score:
        return True
    if candidate_benchmark.adapted_average_score == initial_benchmark.adapted_average_score:
        return candidate_benchmark.average_score_delta > initial_benchmark.average_score_delta
    return False


def build_profile_refresh_report(
    *,
    initial_profile: WorkspaceProfile,
    candidate_profile: WorkspaceProfile,
    final_profile: WorkspaceProfile,
    refresh_plan: ProfileRefreshPlan,
    initial_benchmark: OnboardingBenchmarkReport,
    candidate_benchmark: OnboardingBenchmarkReport,
    candidate_changed: bool,
    candidate_accepted: bool,
) -> ProfileRefreshReport:
    actions = list(refresh_plan.actions)
    if candidate_changed and candidate_accepted:
        actions.append(
            "Accepted refreshed profile because the held-out adapted score improved from "
            f"{initial_benchmark.adapted_average_score:.2f} to {candidate_benchmark.adapted_average_score:.2f}."
        )
    elif candidate_changed:
        actions.append(
            "Rejected refreshed profile because the held-out benchmark did not improve over the current baseline."
        )
    else:
        actions.append("No refreshable profile changes were produced from the available tracker evidence.")

    final_score = candidate_benchmark.adapted_average_score if candidate_accepted else initial_benchmark.adapted_average_score
    return ProfileRefreshReport(
        workspace_id=initial_profile.workspace_id,
        initial_profile_version=initial_profile.profile_version,
        candidate_profile_version=candidate_profile.profile_version,
        final_profile_version=final_profile.profile_version,
        candidate_changed=candidate_changed,
        candidate_accepted=candidate_accepted,
        relevant_record_count=refresh_plan.relevant_record_count,
        evidence_profile_versions=list(refresh_plan.evidence_profile_versions),
        evidence_task_families=list(refresh_plan.evidence_task_families),
        helped_categories=list(refresh_plan.helped_categories),
        remaining_gap_categories=list(refresh_plan.remaining_gap_categories),
        carried_failure_markers=list(refresh_plan.carried_failure_markers),
        carried_prefix_aliases=dict(refresh_plan.carried_prefix_aliases),
        promoted_candidate_fields=list(refresh_plan.promoted_candidate_fields),
        source_priority_promotions=list(refresh_plan.source_priority_promotions),
        initial_adapted_average_score=initial_benchmark.adapted_average_score,
        candidate_adapted_average_score=candidate_benchmark.adapted_average_score,
        final_adapted_average_score=final_score,
        score_delta=round(final_score - initial_benchmark.adapted_average_score, 4),
        actions=actions,
        carried_cue_phrases=dict(refresh_plan.carried_cue_phrases),
    )


def learn_failure_markers(sample_scenarios: list[Scenario]) -> set[str]:
    learned: set[str] = set()
    for scenario in sample_scenarios:
        for event in scenario.events:
            lowered = event.text.lower()
            if not (lowered.startswith("attempt:") or lowered.startswith("outcome:")):
                continue
            for marker in LEARNABLE_FAILURE_MARKERS:
                if marker in lowered:
                    learned.add(marker)
    return learned


def learn_prefix_aliases(sample_scenarios: list[Scenario]) -> dict[str, list[str]]:
    learned: dict[str, set[str]] = {category: set() for category in LEARNABLE_PREFIX_ALIASES}
    default_prefixes = {prefix.removesuffix(":") for prefix in DEFAULT_PREFIX_TO_CATEGORY}

    for scenario in sample_scenarios:
        for event in scenario.events:
            prefix = extract_prefix_label(event.text)
            if prefix is None or prefix in default_prefixes:
                continue
            for category, aliases in LEARNABLE_PREFIX_ALIASES.items():
                if prefix in aliases:
                    learned[category].add(prefix)

    return {
        category: sorted(values)
        for category, values in sorted(learned.items())
        if values
    }


def learn_cue_phrases(sample_scenarios: list[Scenario]) -> dict[str, list[str]]:
    learned: dict[str, set[str]] = {category: set() for category in LEARNABLE_CUE_CATEGORIES}

    for scenario in sample_scenarios:
        expected_by_category: dict[str, list[str]] = {}
        for item in scenario.expected_items:
            if item.category not in LEARNABLE_CUE_CATEGORIES:
                continue
            expected_by_category.setdefault(item.category, []).extend(item.keywords)

        for event in scenario.events:
            if extract_prefix_label(event.text) is not None:
                continue

            for category, keywords in expected_by_category.items():
                cue_phrases = _derive_cue_phrases(event.text, keywords, category)
                learned[category].update(cue_phrases)

            if event.source_refs:
                learned["source"].update(_derive_cue_phrases(event.text, list(event.source_refs), "source"))

    return {
        category: sorted(values)
        for category, values in sorted(learned.items())
        if values
    }


def _derive_cue_phrases(text: str, keywords: list[str], category: str) -> list[str]:
    lowered = text.lower()
    positions = [
        lowered.find(keyword.lower())
        for keyword in keywords
        if keyword and keyword.lower() in lowered
    ]
    if not positions:
        return []

    first_position = min(position for position in positions if position >= 0)
    if first_position <= 0:
        return []

    leading_segment = _normalize_cue_segment(text[:first_position])
    if not leading_segment:
        return []

    canonical_matches = [
        fragment
        for fragment in CANONICAL_CUE_FRAGMENTS.get(category, ())
        if fragment in leading_segment
    ]
    if canonical_matches:
        return ordered_unique(canonical_matches)

    fallback = _fallback_cue_phrase(leading_segment)
    if fallback is None:
        return []
    return [fallback]


def _normalize_cue_segment(value: str) -> str:
    words = re.findall(r"[a-z0-9_./-]+", value.lower())
    return " ".join(words)


def _fallback_cue_phrase(leading_segment: str) -> str | None:
    words = leading_segment.split()
    if len(words) < 2:
        return None
    if len(words) <= 4:
        phrase = " ".join(words)
    else:
        phrase = " ".join(words[:4])
    if len(phrase) < 5:
        return None
    return phrase


def infer_benchmark_profiles(sample_scenarios: list[Scenario]) -> list[str]:
    profiles = {
        DOMAIN_BENCHMARK_PROFILES[scenario.domain]
        for scenario in sample_scenarios
        if scenario.domain in DOMAIN_BENCHMARK_PROFILES
    }
    return sorted(profiles)


def infer_task_families(scenarios: list[Scenario]) -> set[str]:
    return {infer_task_family(scenario) for scenario in scenarios}


def infer_task_family(scenario: Scenario) -> str:
    lowered = scenario.scenario_id.lower()
    for prefix in KNOWN_TASK_FAMILY_PREFIXES:
        if lowered.startswith(prefix):
            return prefix
    return f"synthetic_{scenario.domain}"


def infer_candidate_fields(candidate_type_counts: Counter[str]) -> list[str]:
    inferred = {
        CATEGORY_TO_STARTER_FIELD[category]
        for category, count in candidate_type_counts.items()
        if count > 0 and category in CATEGORY_TO_STARTER_FIELD
    }
    if "attempt" in candidate_type_counts or "outcome" in candidate_type_counts:
        inferred.add("recent_failures")
    return sorted(inferred)


def infer_source_priority_order(source_type_counts: Counter[str]) -> list[str]:
    if not source_type_counts:
        return list(DEFAULT_SOURCE_PRIORITY)

    ranked = sorted(
        source_type_counts.items(),
        key=lambda item: (-item[1], DEFAULT_SOURCE_PRIORITY.index(item[0]) if item[0] in DEFAULT_SOURCE_PRIORITY else len(DEFAULT_SOURCE_PRIORITY)),
    )
    observed = [source_type for source_type, _count in ranked]
    trailing = [source_type for source_type in DEFAULT_SOURCE_PRIORITY if source_type not in observed]
    return observed + trailing


def compute_profile_version(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()[:12]


def run_onboarding_benchmark(
    profile: WorkspaceProfile,
    holdout_scenarios: list[Scenario],
    *,
    gate_threshold: float = 0.9,
) -> OnboardingBenchmarkReport:
    if not holdout_scenarios:
        return OnboardingBenchmarkReport(
            workspace_id=profile.workspace_id,
            profile_version=profile.profile_version,
            sample_scenario_ids=list(profile.sample_scenario_ids),
            holdout_scenario_ids=[],
            baseline_average_score=0.0,
            adapted_average_score=0.0,
            average_score_delta=0.0,
            gate_threshold=gate_threshold,
            gate_passed=False,
            scenario_results=[],
            recommended_actions=["Add at least one held-out trace before trusting the onboarding profile."],
            cue_disabled_average_score=0.0,
            cue_average_score_delta=0.0,
        )

    scenario_results, baseline_average, adapted_average, average_delta, cue_disabled_average, cue_average_delta = score_scenarios_with_profile(
        profile,
        holdout_scenarios,
    )
    gate_passed = adapted_average >= gate_threshold and average_delta >= 0.01

    recommended_actions = build_onboarding_actions(profile, scenario_results, gate_passed)
    return OnboardingBenchmarkReport(
        workspace_id=profile.workspace_id,
        profile_version=profile.profile_version,
        sample_scenario_ids=list(profile.sample_scenario_ids),
        holdout_scenario_ids=[scenario.scenario_id for scenario in holdout_scenarios],
        baseline_average_score=baseline_average,
        adapted_average_score=adapted_average,
        average_score_delta=average_delta,
        gate_threshold=gate_threshold,
        gate_passed=gate_passed,
        scenario_results=scenario_results,
        recommended_actions=recommended_actions,
        cue_disabled_average_score=cue_disabled_average,
        cue_average_score_delta=cue_average_delta,
    )


def run_transfer_benchmark(
    profile: WorkspaceProfile,
    target_scenarios: list[Scenario],
    *,
    gate_threshold: float = 0.85,
) -> TransferBenchmarkReport:
    if not target_scenarios:
        return TransferBenchmarkReport(
            workspace_id=profile.workspace_id,
            profile_version=profile.profile_version,
            source_sample_scenario_ids=list(profile.sample_scenario_ids),
            source_holdout_scenario_ids=list(profile.holdout_scenario_ids),
            target_scenario_ids=[],
            source_task_families=list(profile.task_families),
            target_task_families=[],
            baseline_average_score=0.0,
            adapted_average_score=0.0,
            average_score_delta=0.0,
            gate_threshold=gate_threshold,
            gate_passed=False,
            scenario_results=[],
            recommended_actions=["Add at least one target task family before running a transfer benchmark."],
            cue_disabled_average_score=0.0,
            cue_average_score_delta=0.0,
        )

    scenario_results, baseline_average, adapted_average, average_delta, cue_disabled_average, cue_average_delta = score_scenarios_with_profile(
        profile,
        target_scenarios,
    )
    gate_passed = adapted_average >= gate_threshold and average_delta >= 0.01
    recommended_actions = build_transfer_actions(profile, scenario_results, gate_passed)
    return TransferBenchmarkReport(
        workspace_id=profile.workspace_id,
        profile_version=profile.profile_version,
        source_sample_scenario_ids=list(profile.sample_scenario_ids),
        source_holdout_scenario_ids=list(profile.holdout_scenario_ids),
        target_scenario_ids=[scenario.scenario_id for scenario in target_scenarios],
        source_task_families=list(profile.task_families),
        target_task_families=sorted(infer_task_families(target_scenarios)),
        baseline_average_score=baseline_average,
        adapted_average_score=adapted_average,
        average_score_delta=average_delta,
        gate_threshold=gate_threshold,
        gate_passed=gate_passed,
        scenario_results=scenario_results,
        recommended_actions=recommended_actions,
        cue_disabled_average_score=cue_disabled_average,
        cue_average_score_delta=cue_average_delta,
    )


def score_scenarios_with_profile(
    profile: WorkspaceProfile,
    scenarios: list[Scenario],
) -> tuple[list[OnboardingScenarioResult], float, float, float, float, float]:
    scenario_results: list[OnboardingScenarioResult] = []
    baseline_scores: list[float] = []
    cue_disabled_scores: list[float] = []
    adapted_scores: list[float] = []
    cues_enabled = bool(profile.cue_phrases)

    for scenario in scenarios:
        baseline = evaluate_scenario_with_profile(scenario, failure_markers=None, prefix_aliases=None)
        cue_disabled = evaluate_scenario_with_profile(
            scenario,
            failure_markers=profile.failure_markers,
            prefix_aliases=profile.prefix_aliases,
            cue_phrases=None,
            source_priority_order=profile.source_priority_order,
        )
        adapted = evaluate_scenario_with_profile(
            scenario,
            failure_markers=profile.failure_markers,
            prefix_aliases=profile.prefix_aliases,
            cue_phrases=profile.cue_phrases,
            source_priority_order=profile.source_priority_order,
        )
        baseline_scores.append(baseline.score)
        cue_disabled_scores.append(cue_disabled.score)
        adapted_scores.append(adapted.score)

        improved_categories = sorted(set(baseline.missing_categories) - set(adapted.missing_categories))
        cue_helped_categories = (
            sorted(set(cue_disabled.missing_categories) - set(adapted.missing_categories))
            if cues_enabled
            else []
        )
        scenario_results.append(
            OnboardingScenarioResult(
                scenario_id=scenario.scenario_id,
                title=scenario.title,
                domain=scenario.domain,
                task_family=infer_task_family(scenario),
                baseline_score=baseline.score,
                adapted_score=adapted.score,
                score_delta=round(adapted.score - baseline.score, 4),
                baseline_missing_categories=baseline.missing_categories,
                adapted_missing_categories=adapted.missing_categories,
                improved_categories=improved_categories,
                cue_disabled_score=cue_disabled.score,
                cue_score_delta=round(adapted.score - cue_disabled.score, 4),
                cue_helped_categories=cue_helped_categories,
            )
        )

    baseline_average = round(sum(baseline_scores) / len(baseline_scores), 4)
    cue_disabled_average = round(sum(cue_disabled_scores) / len(cue_disabled_scores), 4)
    adapted_average = round(sum(adapted_scores) / len(adapted_scores), 4)
    average_delta = round(adapted_average - baseline_average, 4)
    cue_average_delta = round(adapted_average - cue_disabled_average, 4)
    return scenario_results, baseline_average, adapted_average, average_delta, cue_disabled_average, cue_average_delta


def evaluate_scenario_with_profile(
    scenario: Scenario,
    failure_markers: list[str] | None,
    prefix_aliases: dict[str, list[str]] | None,
    cue_phrases: dict[str, list[str]] | None = None,
    source_priority_order: list[str] | None = None,
) -> EvaluationReport:
    manifest = build_run_manifest(scenario)
    candidates = extract_candidates(
        scenario.events,
        fallback_goal=scenario.goal,
        prefix_aliases=prefix_aliases,
        cue_phrases=cue_phrases,
        source_priority_order=source_priority_order,
    )
    packet = build_resume_packet(manifest, candidates, failure_markers=failure_markers)
    return evaluate_resume_packet(scenario, packet)


def build_run_manifest(scenario: Scenario) -> RunManifest:
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


def classify_source_ref(source_ref: str) -> str:
    lowered = source_ref.lower()
    if "readme" in lowered:
        return "readme"
    if lowered.startswith("tests/") or "/tests/" in lowered or ".test" in lowered or "_test." in lowered:
        return "tests"
    if lowered.startswith("docs/") or lowered.endswith(".md"):
        return "architecture_docs"
    if lowered.startswith("smoke-tests/"):
        return "smoke_tests"
    if "." in source_ref and "/" not in source_ref:
        return "tool_logs"
    if lowered.endswith((".py", ".js", ".ts", ".tsx", ".go", ".rs", ".java")):
        return "source_files"
    return "other"


def build_onboarding_actions(
    profile: WorkspaceProfile,
    scenario_results: list[OnboardingScenarioResult],
    gate_passed: bool,
) -> list[str]:
    if not scenario_results:
        return ["Add held-out traces and rerun onboarding before promoting this profile."]

    actions: list[str] = []
    remaining_categories = Counter(
        category
        for result in scenario_results
        for category in result.adapted_missing_categories
    )
    improved_categories = {
        category
        for result in scenario_results
        for category in result.improved_categories
    }
    if remaining_categories:
        for category, _count in remaining_categories.most_common(3):
            actions.append(f"Improve onboarding support for `{category}` before promoting this profile further.")
    if not improved_categories or improved_categories == {"recent_failures"}:
        actions.append("Broaden onboarding signals beyond failure markers and label aliases so more than one category can improve.")
    if not gate_passed:
        actions.append("Keep this profile provisional and expand the representative sample before trusting it.")
    else:
        actions.append("Profile passed the benchmark gate; it is safe to use as a generated starter pack.")
    if "recent_failures" in profile.candidate_fields:
        actions.append("Promote the learned failure markers into the next refresh cycle and keep monitoring drift.")
    if profile.prefix_aliases:
        actions.append("Keep watching for new event-label styles so extraction keeps adapting beyond the default prefixes.")
    if profile.cue_phrases:
        actions.append("Keep watching for recurring content cues so refresh can improve unlabeled notes as well as labeled ones.")
    return actions


def build_transfer_actions(
    profile: WorkspaceProfile,
    scenario_results: list[OnboardingScenarioResult],
    gate_passed: bool,
) -> list[str]:
    if not scenario_results:
        return ["Add target scenarios before judging whether this profile transfers."]

    actions: list[str] = []
    improved_families = sorted(
        {
            result.task_family
            for result in scenario_results
            if result.score_delta > 0.0
        }
    )
    remaining_categories = Counter(
        category
        for result in scenario_results
        for category in result.adapted_missing_categories
    )
    if improved_families:
        actions.append(
            "Profile transferred useful behavior to "
            + ", ".join(f"`{family}`" for family in improved_families[:3])
            + "."
        )
    if remaining_categories:
        category, _count = remaining_categories.most_common(1)[0]
        actions.append(f"Strengthen transfer support for `{category}` before treating this profile as broadly reusable.")
    if not gate_passed:
        actions.append("Treat this profile as family-specific for now and gather more cross-family evidence.")
    else:
        actions.append("Profile passed the transfer gate; keep tracking whether the gain holds across additional families.")
    if "recent_failures" in profile.candidate_fields:
        actions.append("Keep failure-marker learning in the transfer loop and watch whether it generalizes or becomes family-specific.")
    if profile.cue_phrases:
        actions.append("Track whether learned content cues transfer cleanly or only help one task family.")
    return actions


def build_strategy_record(
    *,
    run_kind: str,
    workspace_id: str,
    profile: WorkspaceProfile,
    artifact_dir: Path,
    source_scenarios: list[Scenario],
    evaluation_scenarios: list[Scenario],
    benchmark: OnboardingBenchmarkReport | TransferBenchmarkReport,
    duration_ms: int,
) -> StrategyRunRecord:
    created_at = datetime.now(timezone.utc).isoformat()
    improved_category_counts = summarize_category_counts(
        scenario_results=benchmark.scenario_results,
        improved=True,
    )
    remaining_gap_category_counts = summarize_category_counts(
        scenario_results=benchmark.scenario_results,
        improved=False,
    )
    cue_helped_category_counts = summarize_cue_helped_category_counts(benchmark.scenario_results)
    return StrategyRunRecord(
        record_id=artifact_dir.name,
        created_at=created_at,
        run_kind=run_kind,
        workspace_id=workspace_id,
        profile_version=profile.profile_version,
        artifact_dir=artifact_dir.as_posix(),
        source_task_families=sorted(infer_task_families(source_scenarios)),
        evaluation_task_families=sorted(infer_task_families(evaluation_scenarios)),
        source_domains=sorted({scenario.domain for scenario in source_scenarios}),
        evaluation_domains=sorted({scenario.domain for scenario in evaluation_scenarios}),
        sample_count=len(profile.sample_scenario_ids),
        holdout_count=len(profile.holdout_scenario_ids),
        scenario_count=len(evaluation_scenarios),
        event_count=sum(len(scenario.events) for scenario in source_scenarios + evaluation_scenarios),
        duration_ms=duration_ms,
        baseline_average_score=benchmark.baseline_average_score,
        adapted_average_score=benchmark.adapted_average_score,
        average_score_delta=benchmark.average_score_delta,
        gate_threshold=benchmark.gate_threshold,
        gate_passed=benchmark.gate_passed,
        cue_disabled_average_score=benchmark.cue_disabled_average_score,
        cue_average_score_delta=benchmark.cue_average_score_delta,
        improved_scenario_count=sum(1 for result in benchmark.scenario_results if result.score_delta > 0.0),
        degraded_scenario_count=sum(1 for result in benchmark.scenario_results if result.score_delta < 0.0),
        improved_category_counts=improved_category_counts,
        remaining_gap_category_counts=remaining_gap_category_counts,
        cue_helped_category_counts=cue_helped_category_counts,
        evaluation_task_family_metrics=build_task_family_metrics(benchmark.scenario_results),
    )


def build_improvement_insights(
    *,
    workspace_id: str,
    profile: WorkspaceProfile,
    run_kind: str,
    scenario_results: list[OnboardingScenarioResult],
    recommended_actions: list[str],
) -> list[ImprovementInsight]:
    created_at = datetime.now(timezone.utc).isoformat()
    insights: list[ImprovementInsight] = []
    improved_categories = Counter(
        category
        for result in scenario_results
        for category in result.improved_categories
    )
    remaining_categories = Counter(
        category
        for result in scenario_results
        for category in result.adapted_missing_categories
    )

    if improved_categories:
        categories = [category for category, _count in improved_categories.most_common(3)]
        scenario_ids = [
            result.scenario_id
            for result in scenario_results
            if any(category in result.improved_categories for category in categories)
        ]
        insights.append(
            ImprovementInsight(
                created_at=created_at,
                workspace_id=workspace_id,
                profile_version=profile.profile_version,
                run_kind=run_kind,
                signal="helped",
                summary="Top improved categories: " + ", ".join(categories) + ".",
                categories=categories,
                scenario_ids=scenario_ids,
            )
        )

    if remaining_categories:
        categories = [category for category, _count in remaining_categories.most_common(3)]
        scenario_ids = [
            result.scenario_id
            for result in scenario_results
            if any(category in result.adapted_missing_categories for category in categories)
        ]
        insights.append(
            ImprovementInsight(
                created_at=created_at,
                workspace_id=workspace_id,
                profile_version=profile.profile_version,
                run_kind=run_kind,
                signal="remaining_gap",
                summary="Most common remaining gaps: " + ", ".join(categories) + ".",
                categories=categories,
                scenario_ids=scenario_ids,
            )
        )

    for action in recommended_actions[:2]:
        insights.append(
            ImprovementInsight(
                created_at=created_at,
                workspace_id=workspace_id,
                profile_version=profile.profile_version,
                run_kind=run_kind,
                signal="next_try",
                summary=action,
                categories=[],
                scenario_ids=[result.scenario_id for result in scenario_results],
            )
        )
    return insights


def load_strategy_records(base_dir: str | Path) -> list[StrategyRunRecord]:
    path = Path(base_dir) / "strategy_tracker.jsonl"
    if not path.exists():
        return []

    records: list[StrategyRunRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        records.append(StrategyRunRecord(**json.loads(stripped)))
    return records


def summarize_strategy_records(base_dir: str | Path) -> StrategyTrackerSummary:
    return summarize_strategy_records_for_records(load_strategy_records(base_dir))


def summarize_strategy_records_for_records(records: list[StrategyRunRecord]) -> StrategyTrackerSummary:
    if not records:
        return StrategyTrackerSummary(
            total_records=0,
            latest_profile_version=None,
            task_families=[],
            run_kind_summaries=[],
            category_summaries=[],
            task_family_summaries=[],
            profile_summaries=[],
            workspace_lineages=[],
        )

    ordered_records = sorted(records, key=lambda item: (item.created_at, item.record_id))
    kind_summaries: list[StrategyRunKindSummary] = []
    for run_kind in sorted({record.run_kind for record in ordered_records}):
        group = [record for record in ordered_records if record.run_kind == run_kind]
        count = len(group)
        kind_summaries.append(
            StrategyRunKindSummary(
                run_kind=run_kind,
                record_count=count,
                average_baseline_score=round(sum(item.baseline_average_score for item in group) / count, 4),
                average_adapted_score=round(sum(item.adapted_average_score for item in group) / count, 4),
                average_score_delta=round(sum(item.average_score_delta for item in group) / count, 4),
                average_duration_ms=round(sum(item.duration_ms for item in group) / count, 1),
                gate_pass_rate=round(sum(1.0 for item in group if item.gate_passed) / count, 4),
                average_events_per_scenario=round(
                    sum(item.event_count / max(item.scenario_count, 1) for item in group) / count,
                    2,
                ),
                average_duration_per_scenario_ms=round(
                    sum(item.duration_ms / max(item.scenario_count, 1) for item in group) / count,
                    2,
                ),
                average_duration_per_event_ms=round(
                    sum(item.duration_ms / max(item.event_count, 1) for item in group) / count,
                    4,
                ),
            )
        )

    latest_record = ordered_records[-1]
    task_families = sorted(
        {
            family
            for record in ordered_records
            for family in record.source_task_families + record.evaluation_task_families
        }
    )
    return StrategyTrackerSummary(
        total_records=len(ordered_records),
        latest_profile_version=latest_record.profile_version,
        task_families=task_families,
        run_kind_summaries=kind_summaries,
        category_summaries=build_category_summaries(ordered_records),
        task_family_summaries=build_task_family_summaries(ordered_records),
        profile_summaries=build_profile_summaries(ordered_records),
        workspace_lineages=build_workspace_lineages(ordered_records),
    )


def select_relevant_strategy_records(
    base_dir: str | Path,
    workspace_id: str,
    task_families: list[str],
) -> list[StrategyRunRecord]:
    current_task_families = set(task_families)
    ranked_records: list[tuple[int, int, str, StrategyRunRecord]] = []
    for record in load_strategy_records(base_dir):
        if not record.gate_passed or record.average_score_delta <= 0.0:
            continue
        record_task_families = set(record.source_task_families + record.evaluation_task_families)
        overlap_count = len(record_task_families & current_task_families)
        same_workspace = record.workspace_id == workspace_id
        if not same_workspace and overlap_count == 0:
            continue
        ranked_records.append(
            (
                0 if same_workspace else 1,
                -overlap_count,
                record.created_at,
                record,
            )
        )

    ordered = sorted(ranked_records, key=lambda item: (item[0], item[1], item[2], item[3].record_id))
    return [record for _workspace_rank, _overlap_rank, _created_at, record in ordered]


def load_workspace_profiles_for_records(records: list[StrategyRunRecord]) -> dict[str, WorkspaceProfile]:
    profiles: dict[str, WorkspaceProfile] = {}
    for record in records:
        if record.profile_version in profiles:
            continue
        path = Path(record.artifact_dir) / "workspace_profile.json"
        if not path.exists():
            continue
        profiles[record.profile_version] = load_workspace_profile(path)
    return profiles


def load_workspace_profile(path: str | Path) -> WorkspaceProfile:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return WorkspaceProfile(**payload)


def summarize_category_counts(
    *,
    scenario_results: list[OnboardingScenarioResult],
    improved: bool,
) -> dict[str, int]:
    counter = Counter(
        category
        for result in scenario_results
        for category in (result.improved_categories if improved else result.adapted_missing_categories)
    )
    return dict(sorted(counter.items()))


def summarize_cue_helped_category_counts(
    scenario_results: list[OnboardingScenarioResult],
) -> dict[str, int]:
    counter = Counter(
        category
        for result in scenario_results
        for category in result.cue_helped_categories
    )
    return dict(sorted(counter.items()))


def build_task_family_metrics(
    scenario_results: list[OnboardingScenarioResult],
) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[OnboardingScenarioResult]] = {}
    for result in scenario_results:
        grouped.setdefault(result.task_family, []).append(result)

    metrics: dict[str, dict[str, float | int]] = {}
    for task_family, results in sorted(grouped.items()):
        count = len(results)
        metrics[task_family] = {
            "scenario_count": count,
            "baseline_average_score": round(sum(item.baseline_score for item in results) / count, 4),
            "adapted_average_score": round(sum(item.adapted_score for item in results) / count, 4),
            "average_score_delta": round(sum(item.score_delta for item in results) / count, 4),
            "improved_scenario_count": sum(1 for item in results if item.score_delta > 0.0),
        }
    return metrics


def build_category_summaries(records: list[StrategyRunRecord]) -> list[StrategyCategorySummary]:
    helped_runs: Counter[str] = Counter()
    helped_scenarios: Counter[str] = Counter()
    remaining_runs: Counter[str] = Counter()
    remaining_scenarios: Counter[str] = Counter()
    cue_helped_runs: Counter[str] = Counter()
    cue_helped_scenarios: Counter[str] = Counter()
    cue_delta_totals: dict[str, float] = defaultdict(float)
    cue_delta_counts: Counter[str] = Counter()
    cue_task_families: dict[str, set[str]] = {}

    for record in records:
        for category, count in record.improved_category_counts.items():
            if count <= 0:
                continue
            helped_runs[category] += 1
            helped_scenarios[category] += count
        for category, count in record.remaining_gap_category_counts.items():
            if count <= 0:
                continue
            remaining_runs[category] += 1
            remaining_scenarios[category] += count
        for category, count in record.cue_helped_category_counts.items():
            if count <= 0:
                continue
            cue_helped_runs[category] += 1
            cue_helped_scenarios[category] += count
            cue_delta_totals[category] += record.cue_average_score_delta
            cue_delta_counts[category] += 1
            cue_task_families.setdefault(category, set()).update(record.evaluation_task_families)

    categories = sorted(
        set(helped_runs)
        | set(helped_scenarios)
        | set(remaining_runs)
        | set(remaining_scenarios)
        | set(cue_helped_runs)
        | set(cue_helped_scenarios),
        key=lambda item: (
            -(helped_scenarios[item] + remaining_scenarios[item] + cue_helped_scenarios[item]),
            item,
        ),
    )
    return [
        StrategyCategorySummary(
            category=category,
            helped_run_count=helped_runs[category],
            helped_scenario_count=helped_scenarios[category],
            remaining_gap_run_count=remaining_runs[category],
            remaining_gap_scenario_count=remaining_scenarios[category],
            cue_helped_run_count=cue_helped_runs[category],
            cue_helped_scenario_count=cue_helped_scenarios[category],
            cue_average_score_delta=round(
                cue_delta_totals[category] / cue_delta_counts[category],
                4,
            )
            if cue_delta_counts[category]
            else 0.0,
            helped_task_families=sorted(cue_task_families.get(category, set())),
        )
        for category in categories
    ]


def build_task_family_summaries(records: list[StrategyRunRecord]) -> list[StrategyTaskFamilySummary]:
    grouped: dict[str, list[tuple[StrategyRunRecord, dict[str, float | int]]]] = {}
    for record in records:
        metrics = record.evaluation_task_family_metrics or fallback_task_family_metrics(record)
        for task_family, task_metrics in metrics.items():
            grouped.setdefault(task_family, []).append((record, task_metrics))

    summaries: list[StrategyTaskFamilySummary] = []
    for task_family in sorted(grouped):
        entries = grouped[task_family]
        record_count = len(entries)
        scenario_count = sum(int(task_metrics.get("scenario_count", 0)) for _record, task_metrics in entries)
        weighted_scenario_count = max(scenario_count, 1)
        baseline_total = sum(
            float(task_metrics.get("baseline_average_score", record.baseline_average_score))
            * max(int(task_metrics.get("scenario_count", 0)), 1)
            for record, task_metrics in entries
        )
        adapted_total = sum(
            float(task_metrics.get("adapted_average_score", record.adapted_average_score))
            * max(int(task_metrics.get("scenario_count", 0)), 1)
            for record, task_metrics in entries
        )
        delta_total = sum(
            float(task_metrics.get("average_score_delta", record.average_score_delta))
            * max(int(task_metrics.get("scenario_count", 0)), 1)
            for record, task_metrics in entries
        )
        summaries.append(
            StrategyTaskFamilySummary(
                task_family=task_family,
                record_count=record_count,
                scenario_count=scenario_count,
                average_baseline_score=round(baseline_total / weighted_scenario_count, 4),
                average_adapted_score=round(adapted_total / weighted_scenario_count, 4),
                average_score_delta=round(delta_total / weighted_scenario_count, 4),
                improvement_rate=round(
                    sum(int(task_metrics.get("improved_scenario_count", 0)) for _record, task_metrics in entries)
                    / max(scenario_count, 1),
                    4,
                ),
                gate_pass_rate=round(
                    sum(1.0 for record, _task_metrics in entries if record.gate_passed) / record_count,
                    4,
                ),
            )
        )
    return summaries


def fallback_task_family_metrics(record: StrategyRunRecord) -> dict[str, dict[str, float | int]]:
    families = record.evaluation_task_families or ["unknown"]
    scenario_count = max(record.scenario_count, 1)
    family_scenario_count = max(1, round(scenario_count / len(families)))
    improved_per_family = 1 if record.improved_scenario_count > 0 else 0
    return {
        family: {
            "scenario_count": family_scenario_count,
            "baseline_average_score": record.baseline_average_score,
            "adapted_average_score": record.adapted_average_score,
            "average_score_delta": record.average_score_delta,
            "improved_scenario_count": improved_per_family,
        }
        for family in families
    }


def build_profile_summaries(records: list[StrategyRunRecord]) -> list[StrategyProfileSummary]:
    grouped: dict[str, list[StrategyRunRecord]] = {}
    for record in records:
        grouped.setdefault(record.profile_version, []).append(record)

    summaries: list[StrategyProfileSummary] = []
    for profile_version in sorted(
        grouped,
        key=lambda item: (
            -len(grouped[item]),
            -sum(record.average_score_delta for record in grouped[item]),
            item,
        ),
    ):
        group = sorted(grouped[profile_version], key=lambda item: (item.created_at, item.record_id))
        count = len(group)
        summaries.append(
            StrategyProfileSummary(
                profile_version=profile_version,
                record_count=count,
                first_seen_at=group[0].created_at,
                last_seen_at=group[-1].created_at,
                workspace_ids=sorted({record.workspace_id for record in group}),
                run_kinds=sorted({record.run_kind for record in group}),
                source_task_families=sorted(
                    {
                        family
                        for record in group
                        for family in record.source_task_families
                    }
                ),
                evaluation_task_families=sorted(
                    {
                        family
                        for record in group
                        for family in record.evaluation_task_families
                    }
                ),
                average_score_delta=round(sum(record.average_score_delta for record in group) / count, 4),
                gate_pass_rate=round(sum(1.0 for record in group if record.gate_passed) / count, 4),
            )
        )
    return summaries


def build_workspace_lineages(records: list[StrategyRunRecord]) -> list[StrategyWorkspaceLineage]:
    grouped: dict[str, list[StrategyRunRecord]] = {}
    for record in records:
        grouped.setdefault(record.workspace_id, []).append(record)

    lineages: list[StrategyWorkspaceLineage] = []
    for workspace_id in sorted(grouped):
        group = sorted(grouped[workspace_id], key=lambda item: (item.created_at, item.record_id))
        profile_versions = unique_in_order([record.profile_version for record in group])
        lineages.append(
            StrategyWorkspaceLineage(
                workspace_id=workspace_id,
                record_count=len(group),
                first_seen_at=group[0].created_at,
                last_seen_at=group[-1].created_at,
                profile_versions=profile_versions,
                latest_profile_version=profile_versions[-1],
                run_kinds=unique_in_order([record.run_kind for record in group]),
                average_score_delta=round(sum(record.average_score_delta for record in group) / len(group), 4),
            )
        )
    return lineages


def ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def unique_in_order(values: list[str]) -> list[str]:
    return ordered_unique(values)


def merge_prefix_aliases(
    base_aliases: dict[str, list[str]],
    extra_aliases: dict[str, list[str]],
) -> dict[str, list[str]]:
    merged = {category: list(aliases) for category, aliases in base_aliases.items()}
    for category, aliases in extra_aliases.items():
        merged[category] = ordered_unique(merged.get(category, []) + list(aliases))
    return {
        category: values
        for category, values in sorted(merged.items())
        if values
    }


def merge_phrase_map(
    base_phrases: dict[str, list[str]],
    extra_phrases: dict[str, list[str]],
) -> dict[str, list[str]]:
    merged = {category: list(phrases) for category, phrases in base_phrases.items()}
    for category, phrases in extra_phrases.items():
        merged[category] = ordered_unique(merged.get(category, []) + list(phrases))
    return {
        category: values
        for category, values in sorted(merged.items())
        if values
    }


def merge_priority_order(promoted_items: list[str], current_order: list[str]) -> list[str]:
    return ordered_unique(promoted_items + current_order)


def render_starter_pack_yaml(profile: WorkspaceProfile) -> str:
    lines = [
        "version: 1",
        "workspace:",
        f"  workspace_id: {_yaml_scalar(profile.workspace_id)}",
        f"  profile_version: {_yaml_scalar(profile.profile_version)}",
        f"  domain_hint: {_yaml_scalar(_top_domain(profile.domain_counts))}",
        "  primary_goals:",
        "    - preserve_goal_plan_failure_source",
        "  task_families:",
    ]
    for item in profile.task_families:
        lines.append(f"    - {item}")
    lines.extend(
        [
        "sources:",
        "  priority_order:",
        ]
    )
    for item in profile.source_priority_order:
        lines.append(f"    - {item}")
    lines.extend(
        [
            "  include_globs: []",
            "  exclude_globs: []",
            "  authority_hints: []",
            "extraction:",
            "  discover_entity_types: true",
            "  candidate_entity_types: []",
            "  candidate_relation_types: []",
            "  allow_claim_extraction: true",
            "  sample_strategy: representative",
            "memory:",
            "  required_control_fields:",
        ]
    )
    for item in profile.required_control_fields:
        lines.append(f"    - {item}")
    lines.append("  candidate_fields:")
    for item in profile.candidate_fields:
        lines.append(f"    - {item}")
    lines.extend(
        [
            "  failure_markers:",
        ]
    )
    for item in profile.failure_markers:
        lines.append(f"    - {_yaml_scalar(item)}")
    lines.append("  prefix_aliases:")
    for category, aliases in sorted(profile.prefix_aliases.items()):
        lines.append(f"    {category}:")
        for alias in aliases:
            lines.append(f"      - {_yaml_scalar(alias)}")
    lines.append("  cue_phrases:")
    for category, phrases in sorted(profile.cue_phrases.items()):
        lines.append(f"    {category}:")
        for phrase in phrases:
            lines.append(f"      - {_yaml_scalar(phrase)}")
    lines.extend(
        [
            "retrieval:",
            "  prefer_goal_conditioning: true",
            "  require_source_grounding: true",
            "  default_budget: medium",
            "benchmarks:",
            "  profiles:",
        ]
    )
    for item in profile.benchmark_profiles:
        lines.append(f"    - {item}")
    lines.extend(
        [
            "policies:",
            "  manual_edits_optional: true",
            "  promote_only_after_repeated_evidence: true",
        ]
    )
    return "\n".join(lines) + "\n"


def _top_domain(domain_counts: dict[str, int]) -> str | None:
    if not domain_counts:
        return None
    return max(sorted(domain_counts.items()), key=lambda item: item[1])[0]


def _yaml_scalar(value: str | None) -> str:
    if value is None:
        return "null"
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def _create_onboarding_dir(base_dir: str | Path, workspace_id: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(base_dir) / f"{timestamp}-onboarding-{workspace_id}-{uuid4().hex[:8]}"


def _create_transfer_dir(base_dir: str | Path, workspace_id: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(base_dir) / f"{timestamp}-transfer-{workspace_id}-{uuid4().hex[:8]}"


def _create_refresh_dir(base_dir: str | Path, workspace_id: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(base_dir) / f"{timestamp}-refresh-{workspace_id}-{uuid4().hex[:8]}"


def extract_prefix_label(text: str) -> str | None:
    if ":" not in text:
        return None
    prefix, _rest = text.split(":", 1)
    normalized = prefix.strip().lower()
    return normalized or None
