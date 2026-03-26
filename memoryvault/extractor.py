from __future__ import annotations

from collections import defaultdict
import re
from typing import Iterable

from .models import MemoryCandidate, TaskEvent


DEFAULT_PREFIX_TO_CATEGORY = {
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


def extract_candidates(
    events: list[TaskEvent],
    fallback_goal: str,
    prefix_aliases: dict[str, list[str]] | None = None,
    cue_phrases: dict[str, list[str]] | None = None,
    source_priority_order: list[str] | None = None,
) -> list[MemoryCandidate]:
    candidates: list[MemoryCandidate] = []
    prefix_to_category = build_prefix_map(prefix_aliases)

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
        for prefix, category in prefix_to_category.items():
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

        if not matched and cue_phrases:
            candidates.extend(
                _extract_cue_candidates(
                    event,
                    cue_phrases=cue_phrases,
                    source_priority_order=source_priority_order,
                )
            )

        if not matched and ("failed" in lowered or "error" in lowered):
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


def build_prefix_map(prefix_aliases: dict[str, list[str]] | None = None) -> dict[str, str]:
    prefix_to_category = dict(DEFAULT_PREFIX_TO_CATEGORY)
    if not prefix_aliases:
        return prefix_to_category

    for category, aliases in prefix_aliases.items():
        for alias in aliases:
            normalized = alias.strip().lower()
            if not normalized:
                continue
            if not normalized.endswith(":"):
                normalized = f"{normalized}:"
            prefix_to_category[normalized] = category

    return prefix_to_category


def _extract_cue_candidates(
    event: TaskEvent,
    *,
    cue_phrases: dict[str, list[str]],
    source_priority_order: list[str] | None,
) -> list[MemoryCandidate]:
    lowered = event.text.lower()
    candidates: list[MemoryCandidate] = []

    for category, phrases in sorted(cue_phrases.items()):
        matched_phrase = next(
            (
                normalized
                for phrase in phrases
                for normalized in [_normalize_phrase(phrase)]
                if normalized and normalized in lowered
            ),
            None,
        )
        if matched_phrase is None:
            continue

        if category == "source":
            source_refs = _extract_source_like_refs(event.text, source_priority_order)
            if source_refs:
                for source_ref in source_refs:
                    candidates.append(
                        MemoryCandidate(
                            category="source",
                            summary=source_ref,
                            evidence_event_ids=[event.sequence],
                            confidence=0.75,
                        )
                    )
                continue

        candidates.append(
            MemoryCandidate(
                category=category,
                summary=_strip_leading_phrase(event.text, matched_phrase),
                evidence_event_ids=[event.sequence],
                confidence=0.65,
            )
        )

    return candidates


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


SOURCE_PATTERNS = (
    re.compile(r"\b(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:md|py|json|ya?ml|txt|csv|ts|tsx|js|go|rs|java)\b"),
    re.compile(r"\b[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?: at [A-Za-z0-9_.-]+)?\b"),
    re.compile(r"\b[a-z][a-z0-9_]*(?:\.[a-z0-9_]+){1,}\b"),
)


def _extract_source_like_refs(text: str, source_priority_order: list[str] | None) -> list[str]:
    found = ordered_unique(
        _clean_source_ref(match.group(0))
        for pattern in SOURCE_PATTERNS
        for match in pattern.finditer(text)
    )
    if not source_priority_order:
        return found

    return sorted(
        found,
        key=lambda item: (
            _source_priority_rank(item, source_priority_order),
            item.lower(),
        ),
    )


def _strip_leading_phrase(text: str, phrase: str) -> str:
    lowered = text.lower()
    if lowered.startswith(phrase):
        stripped = text[len(phrase) :].lstrip(" :-,.;")
        return stripped or text.strip()
    return text.strip()


def _normalize_phrase(value: str) -> str:
    words = re.findall(r"[a-z0-9_./-]+", value.lower())
    return " ".join(words)


def _clean_source_ref(value: str) -> str:
    return value.strip(" .,:;()[]{}")


def _source_priority_rank(source_ref: str, source_priority_order: list[str]) -> int:
    source_type = _classify_source_ref(source_ref)
    if source_type in source_priority_order:
        return source_priority_order.index(source_type)
    return len(source_priority_order)


def _classify_source_ref(source_ref: str) -> str:
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


def ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered
