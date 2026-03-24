from __future__ import annotations

from collections import defaultdict

from .models import MemoryCandidate, TaskEvent


PREFIX_TO_CATEGORY = {
    "goal:": "goal",
    "plan:": "plan",
    "next step:": "current_focus",
    "constraint:": "constraint",
    "decision:": "decision",
    "blocker:": "blocker",
    "assumption:": "assumption",
    "attempt:": "attempt",
    "outcome:": "outcome",
    "lesson:": "lesson",
    "discovery:": "lesson",
    "question:": "open_question",
    "source:": "source",
}


def extract_candidates(events: list[TaskEvent], fallback_goal: str) -> list[MemoryCandidate]:
    candidates: list[MemoryCandidate] = []

    if fallback_goal:
        candidates.append(
            MemoryCandidate(
                category="goal",
                summary=fallback_goal,
                evidence_event_ids=[],
                confidence=1.0,
            )
        )

    for event in events:
        lowered = event.text.lower()
        matched = False
        for prefix, category in PREFIX_TO_CATEGORY.items():
            if lowered.startswith(prefix):
                summary = event.text[len(prefix) :].strip()
                candidates.append(
                    MemoryCandidate(
                        category=category,
                        summary=summary,
                        evidence_event_ids=[event.sequence],
                        confidence=0.8,
                    )
                )
                matched = True
                break

        if matched:
            continue

        if "failed" in lowered or "error" in lowered:
            candidates.append(
                MemoryCandidate(
                    category="outcome",
                    summary=event.text.strip(),
                    evidence_event_ids=[event.sequence],
                    confidence=0.55,
                )
            )

        for source_ref in event.source_refs:
            candidates.append(
                MemoryCandidate(
                    category="source",
                    summary=source_ref,
                    evidence_event_ids=[event.sequence],
                    confidence=0.9,
                )
            )

    return _dedupe_candidates(candidates)


def _dedupe_candidates(candidates: list[MemoryCandidate]) -> list[MemoryCandidate]:
    grouped: dict[tuple[str, str], list[MemoryCandidate]] = defaultdict(list)
    for candidate in candidates:
        key = (candidate.category, candidate.summary)
        grouped[key].append(candidate)

    deduped: list[MemoryCandidate] = []
    for (category, summary), bucket in grouped.items():
        evidence_event_ids = sorted({event_id for item in bucket for event_id in item.evidence_event_ids})
        confidence = max(item.confidence for item in bucket)
        deduped.append(
            MemoryCandidate(
                category=category,
                summary=summary,
                evidence_event_ids=evidence_event_ids,
                confidence=confidence,
            )
        )

    return sorted(deduped, key=lambda item: (item.category, item.summary))
