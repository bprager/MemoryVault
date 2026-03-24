from __future__ import annotations

from dataclasses import dataclass, replace

from .evaluation import evaluate_resume_packet
from .models import (
    EvaluationReport,
    ResumePacket,
    RunManifest,
    Scenario,
    WindTunnelFieldImpact,
    WindTunnelReport,
    WindTunnelVariantResult,
)


@dataclass(frozen=True, slots=True)
class VariantSpec:
    variant_id: str
    description: str
    removed_fields: tuple[str, ...]
    keep_only_goal: bool = False
    is_composite: bool = False


VARIANT_SPECS: tuple[VariantSpec, ...] = (
    VariantSpec(
        variant_id="drop_goal_guard",
        description="Remove the explicit final-goal reminder.",
        removed_fields=("final_goal_guard",),
    ),
    VariantSpec(
        variant_id="drop_current_focus",
        description="Remove the current focus and next-step package.",
        removed_fields=("current_focus",),
    ),
    VariantSpec(
        variant_id="drop_constraints",
        description="Remove constraints from the resume packet.",
        removed_fields=("constraints",),
    ),
    VariantSpec(
        variant_id="drop_decisions",
        description="Remove decisions from the resume packet.",
        removed_fields=("decisions",),
    ),
    VariantSpec(
        variant_id="drop_assumptions",
        description="Remove assumptions from the resume packet.",
        removed_fields=("assumptions",),
    ),
    VariantSpec(
        variant_id="drop_recent_failures",
        description="Remove recent failure history from the resume packet.",
        removed_fields=("recent_failures",),
    ),
    VariantSpec(
        variant_id="drop_lessons",
        description="Remove lessons from the resume packet.",
        removed_fields=("lessons",),
    ),
    VariantSpec(
        variant_id="drop_sources",
        description="Remove source links from the resume packet.",
        removed_fields=("sources",),
    ),
    VariantSpec(
        variant_id="goal_only",
        description="Keep only the explicit goal reminder and drop the rest of the memory package.",
        removed_fields=(
            "current_focus",
            "constraints",
            "decisions",
            "blockers",
            "assumptions",
            "recent_failures",
            "lessons",
            "open_questions",
            "sources",
        ),
        keep_only_goal=True,
        is_composite=True,
    ),
)


def build_wind_tunnel_report(
    manifest: RunManifest,
    scenario: Scenario,
    baseline_packet: ResumePacket,
    baseline_evaluation: EvaluationReport,
) -> WindTunnelReport:
    variant_results: list[WindTunnelVariantResult] = []

    for spec in VARIANT_SPECS:
        variant_packet = _apply_variant(baseline_packet, spec)
        evaluation = evaluate_resume_packet(scenario, variant_packet)
        variant_results.append(
            WindTunnelVariantResult(
                variant_id=spec.variant_id,
                description=spec.description,
                removed_fields=list(spec.removed_fields),
                is_composite=spec.is_composite,
                score=evaluation.score,
                score_delta=round(baseline_evaluation.score - evaluation.score, 4),
                failed_check_names=[check.name for check in evaluation.checks if not check.passed],
                missing_categories=evaluation.missing_categories,
            )
        )

    field_impacts = _summarize_field_impacts(variant_results)
    fragile_fields = [
        impact.field_name
        for impact in sorted(
            field_impacts,
            key=lambda item: (item.max_score_delta, item.average_score_delta, item.field_name),
            reverse=True,
        )
        if impact.max_score_delta > 0
    ]

    return WindTunnelReport(
        run_id=manifest.run_id,
        scenario_id=scenario.scenario_id,
        baseline_score=baseline_evaluation.score,
        baseline_missing_categories=baseline_evaluation.missing_categories,
        variant_results=variant_results,
        field_impacts=field_impacts,
        most_fragile_fields=fragile_fields[:5],
    )


def _apply_variant(packet: ResumePacket, spec: VariantSpec) -> ResumePacket:
    mutated = replace(
        packet,
        current_focus=list(packet.current_focus),
        constraints=list(packet.constraints),
        decisions=list(packet.decisions),
        blockers=list(packet.blockers),
        assumptions=list(packet.assumptions),
        recent_failures=list(packet.recent_failures),
        lessons=list(packet.lessons),
        open_questions=list(packet.open_questions),
        sources=list(packet.sources),
        candidate_counts=dict(packet.candidate_counts),
    )

    if spec.keep_only_goal:
        mutated.current_focus = []
        mutated.constraints = []
        mutated.decisions = []
        mutated.blockers = []
        mutated.assumptions = []
        mutated.recent_failures = []
        mutated.lessons = []
        mutated.open_questions = []
        mutated.sources = []

    for field_name in spec.removed_fields:
        if field_name == "final_goal_guard":
            mutated.final_goal_guard = ""
        else:
            setattr(mutated, field_name, [])

    return mutated


def _summarize_field_impacts(variant_results: list[WindTunnelVariantResult]) -> list[WindTunnelFieldImpact]:
    field_to_results: dict[str, list[WindTunnelVariantResult]] = {}
    for result in variant_results:
        if result.is_composite or len(result.removed_fields) != 1:
            continue
        for field_name in result.removed_fields:
            field_to_results.setdefault(field_name, []).append(result)

    impacts: list[WindTunnelFieldImpact] = []
    for field_name, results in sorted(field_to_results.items()):
        average_delta = round(sum(result.score_delta for result in results) / len(results), 4)
        worst_result = max(results, key=lambda result: result.score_delta)
        impacts.append(
            WindTunnelFieldImpact(
                field_name=field_name,
                variants_tested=len(results),
                average_score_delta=average_delta,
                max_score_delta=worst_result.score_delta,
                worst_variant_id=worst_result.variant_id,
            )
        )

    return impacts
