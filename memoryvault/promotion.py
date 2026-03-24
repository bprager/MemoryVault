from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import DurableFieldSuggestion, EvaluationReport


FIELD_NAME_BY_CATEGORY = {
    "goal": "final_goal_guard",
    "current_focus": "current_focus",
    "constraint": "constraints",
    "decision": "decisions",
    "blocker": "blockers",
    "assumption": "assumptions",
    "recent_failures": "recent_failures",
    "lesson": "lessons",
    "open_question": "open_questions",
    "source": "sources",
}


def suggest_durable_fields(base_dir: str | Path, threshold: int = 2) -> list[DurableFieldSuggestion]:
    evaluations = load_evaluations(base_dir)
    total_run_count = len(evaluations)
    if total_run_count == 0:
        return []

    missing_counts: dict[str, int] = {}
    for evaluation in evaluations:
        for category in evaluation.missing_categories:
            missing_counts[category] = missing_counts.get(category, 0) + 1

    suggestions: list[DurableFieldSuggestion] = []
    for category, missing_run_count in sorted(missing_counts.items()):
        field_name = FIELD_NAME_BY_CATEGORY.get(category, category)
        ratio = missing_run_count / total_run_count
        status = "promote_now" if missing_run_count >= threshold else "watch"
        rationale = (
            f"`{category}` was missing in {missing_run_count} of {total_run_count} runs. "
            "Repeated misses usually deserve a durable field or a better extraction rule."
        )
        suggestions.append(
            DurableFieldSuggestion(
                field_name=field_name,
                source_category=category,
                missing_run_count=missing_run_count,
                total_run_count=total_run_count,
                coverage_ratio=ratio,
                status=status,
                rationale=rationale,
            )
        )

    return suggestions


def write_field_suggestions(base_dir: str | Path, threshold: int = 2) -> Path:
    target = Path(base_dir) / "durable_field_suggestions.json"
    suggestions = suggest_durable_fields(base_dir, threshold=threshold)
    target.write_text(json.dumps([asdict(item) for item in suggestions], indent=2) + "\n", encoding="utf-8")
    return target


def load_evaluations(base_dir: str | Path) -> list[EvaluationReport]:
    base_path = Path(base_dir)
    evaluations: list[EvaluationReport] = []

    for path in sorted(base_path.glob("*/evaluation.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        evaluations.append(
            EvaluationReport(
                run_id=str(payload["run_id"]),
                scenario_id=str(payload["scenario_id"]),
                score=float(payload["score"]),
                checks=[],
                improvement_actions=[str(item) for item in payload.get("improvement_actions", [])],
                missing_categories=[str(item) for item in payload.get("missing_categories", [])],
            )
        )

    return evaluations
