from __future__ import annotations

import json
from pathlib import Path

from .models import ExpectedItem, Scenario, TaskEvent


def load_scenario_file(path: str | Path) -> Scenario:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))

    events = [
        TaskEvent(
            sequence=index + 1 if "sequence" not in event else int(event["sequence"]),
            actor=str(event["actor"]),
            text=str(event["text"]),
            source_refs=list(event.get("source_refs", [])),
            metadata=dict(event.get("metadata", {})),
        )
        for index, event in enumerate(payload["events"])
    ]

    expected_items = [
        ExpectedItem(
            name=str(item["name"]),
            category=str(item["category"]),
            keywords=[str(keyword) for keyword in item.get("keywords", [])],
        )
        for item in payload.get("expected_items", [])
    ]

    return Scenario(
        scenario_id=str(payload["scenario_id"]),
        title=str(payload["title"]),
        domain=str(payload["domain"]),
        goal=str(payload["goal"]),
        interruption_point=str(payload["interruption_point"]),
        events=events,
        expected_items=expected_items,
    )


def load_scenarios_from_directory(path: str | Path) -> list[Scenario]:
    source_dir = Path(path)
    files = sorted(candidate for candidate in source_dir.rglob("*.json") if candidate.is_file())
    return [load_scenario_file(candidate) for candidate in files]
