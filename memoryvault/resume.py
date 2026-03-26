from __future__ import annotations

from collections import Counter
from typing import Iterable

from .models import MemoryCandidate, ResumePacket, RunManifest

DEFAULT_FAILURE_MARKERS = frozenset({"failed", "error", "broke", "wrong"})


def build_resume_packet(
    manifest: RunManifest,
    candidates: list[MemoryCandidate],
    failure_markers: Iterable[str] | None = None,
) -> ResumePacket:
    by_category = group_by_category(candidates)

    current_focus = (
        _unique_text(by_category.get("current_focus", []))
        or _unique_text(by_category.get("plan", []))
        or ["Resume by re-reading the last attempt and rebuilding the next step from raw history."]
    )

    recent_failures = _collect_recent_failures(by_category, failure_markers=failure_markers)

    return ResumePacket(
        run_id=manifest.run_id,
        scenario_id=manifest.scenario_id,
        final_goal_guard=manifest.final_goal_guard,
        current_focus=current_focus,
        constraints=_unique_text(by_category.get("constraint", [])),
        decisions=_unique_text(by_category.get("decision", [])),
        blockers=_unique_text(by_category.get("blocker", [])),
        assumptions=_unique_text(by_category.get("assumption", [])),
        recent_failures=recent_failures,
        lessons=_unique_text(by_category.get("lesson", [])),
        open_questions=_unique_text(by_category.get("open_question", [])),
        sources=_unique_text(by_category.get("source", [])),
        candidate_counts=dict(Counter(candidate.category for candidate in candidates)),
    )


def group_by_category(candidates: list[MemoryCandidate]) -> dict[str, list[MemoryCandidate]]:
    grouped: dict[str, list[MemoryCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.category, []).append(candidate)
    return grouped


def _collect_recent_failures(
    grouped: dict[str, list[MemoryCandidate]],
    failure_markers: Iterable[str] | None = None,
) -> list[str]:
    markers = {
        marker.lower()
        for marker in (DEFAULT_FAILURE_MARKERS if failure_markers is None else failure_markers)
        if marker.strip()
    }
    failure_texts: list[str] = []

    for candidate in grouped.get("attempt", []):
        lowered = candidate.summary.lower()
        if any(marker in lowered for marker in markers):
            failure_texts.append(candidate.summary)

    for candidate in grouped.get("outcome", []):
        lowered = candidate.summary.lower()
        if any(marker in lowered for marker in markers):
            failure_texts.append(candidate.summary)

    return _unique_strings(failure_texts)


def _unique_text(items: list[MemoryCandidate]) -> list[str]:
    return _unique_strings(candidate.summary for candidate in items)


def _unique_strings(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique
