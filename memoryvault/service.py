from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from .extractor import extract_candidates
from .models import (
    ExpectedItem,
    IdempotencyRecord,
    MemoryCandidate,
    ResumePacket,
    RunManifest,
    Scenario,
    SERVICE_TASK_STATE_SCHEMA_VERSION,
    ServiceTaskState,
    TaskEvent,
    TaskMemoryView,
)
from .resume import build_resume_packet, group_by_category


class TaskNotFoundError(KeyError):
    """Raised when a task has not been created yet."""


class TaskStateCompatibilityError(ValueError):
    """Raised when a saved task state file cannot be loaded compatibly."""


class TaskVersionConflictError(ValueError):
    """Raised when a write precondition does not match the current task version."""

    def __init__(self, task_id: str, *, expected_version: int, actual_version: int | None) -> None:
        if actual_version is None:
            message = f"task_version precondition failed for {task_id}: task does not exist yet"
        else:
            message = (
                f"task_version precondition failed for {task_id}: "
                f"expected {expected_version}, current is {actual_version}"
            )
        super().__init__(message)
        self.task_id = task_id
        self.expected_version = expected_version
        self.actual_version = actual_version


class IdempotencyConflictError(ValueError):
    """Raised when an idempotency key is reused for a different write."""


SUPPORTED_TASK_STATE_SCHEMAS = {SERVICE_TASK_STATE_SCHEMA_VERSION}


def build_memory_snapshot(
    *,
    task_id: str,
    title: str,
    domain: str,
    goal: str,
    interruption_point: str,
    events: list[TaskEvent],
    run_id: str,
    created_at: str,
    prefix_aliases: dict[str, list[str]] | None = None,
    cue_phrases: dict[str, list[str]] | None = None,
    source_priority_order: list[str] | None = None,
) -> tuple[RunManifest, list[MemoryCandidate], ResumePacket]:
    manifest = RunManifest(
        run_id=run_id,
        scenario_id=task_id,
        title=title,
        domain=domain,
        goal=goal,
        interruption_point=interruption_point,
        final_goal_guard=goal,
        created_at=created_at,
    )
    candidates = extract_memory_candidates(
        events,
        goal=goal,
        prefix_aliases=prefix_aliases,
        cue_phrases=cue_phrases,
        source_priority_order=source_priority_order,
    )
    packet = build_resume_packet_from_candidates(manifest, candidates)
    return manifest, candidates, packet


def extract_memory_candidates(
    events: list[TaskEvent],
    *,
    goal: str,
    prefix_aliases: dict[str, list[str]] | None = None,
    cue_phrases: dict[str, list[str]] | None = None,
    source_priority_order: list[str] | None = None,
) -> list[MemoryCandidate]:
    return extract_candidates(
        events,
        fallback_goal=goal,
        prefix_aliases=prefix_aliases,
        cue_phrases=cue_phrases,
        source_priority_order=source_priority_order,
    )


def build_resume_packet_from_candidates(manifest: RunManifest, candidates: list[MemoryCandidate]) -> ResumePacket:
    return build_resume_packet(manifest, candidates)


class LocalMemoryService:
    def __init__(self, base_dir: str | Path = "var/memoryvault") -> None:
        self.base_dir = Path(base_dir)
        self.tasks_dir = self.base_dir / "service_state" / "tasks"
        self.idempotency_dir = self.base_dir / "service_state" / "idempotency"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.idempotency_dir.mkdir(parents=True, exist_ok=True)

    def import_scenario(self, task_id: str, scenario: Scenario) -> ServiceTaskState:
        self.upsert_task_state(
            task_id,
            title=scenario.title,
            domain=scenario.domain,
            goal=scenario.goal,
            interruption_point=scenario.interruption_point,
            expected_items=scenario.expected_items,
        )
        return self.append_events(task_id, scenario.events)

    def upsert_task_state(
        self,
        task_id: str,
        *,
        title: str | None = None,
        domain: str | None = None,
        goal: str | None = None,
        interruption_point: str | None = None,
        expected_items: list[ExpectedItem] | None = None,
        expected_task_version: int | None = None,
    ) -> ServiceTaskState:
        existing = self._maybe_load_task(task_id)
        _check_expected_task_version(task_id, existing, expected_task_version)
        now = _utc_now()

        if existing is None:
            missing = [
                field_name
                for field_name, value in {
                    "title": title,
                    "domain": domain,
                    "goal": goal,
                    "interruption_point": interruption_point,
                }.items()
                if value is None
            ]
            if missing:
                raise ValueError(f"missing required task fields: {', '.join(missing)}")
            task = ServiceTaskState(
                task_id=task_id,
                title=title or "",
                domain=domain or "",
                goal=goal or "",
                interruption_point=interruption_point or "",
                events=[],
                expected_items=list(expected_items or []),
                created_at=now,
                updated_at=now,
                task_version=1,
            )
        else:
            task = ServiceTaskState(
                task_id=task_id,
                title=title if title is not None else existing.title,
                domain=domain if domain is not None else existing.domain,
                goal=goal if goal is not None else existing.goal,
                interruption_point=interruption_point if interruption_point is not None else existing.interruption_point,
                events=list(existing.events),
                expected_items=list(expected_items if expected_items is not None else existing.expected_items),
                created_at=existing.created_at,
                updated_at=now,
                task_version=existing.task_version + 1,
                artifact_schema_version=SERVICE_TASK_STATE_SCHEMA_VERSION,
            )

        self._write_task(task)
        return task

    def append_events(
        self,
        task_id: str,
        events: list[TaskEvent],
        *,
        expected_task_version: int | None = None,
    ) -> ServiceTaskState:
        task = self.load_task(task_id)
        _check_expected_task_version(task_id, task, expected_task_version)
        task.events.extend(events)
        task.updated_at = _utc_now()
        task.task_version += 1
        self._write_task(task)
        return task

    def load_task(self, task_id: str) -> ServiceTaskState:
        task = self._maybe_load_task(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def get_resume_packet(self, task_id: str) -> ResumePacket:
        task = self.load_task(task_id)
        _manifest, _candidates, packet = build_memory_snapshot(
            task_id=task.task_id,
            title=task.title,
            domain=task.domain,
            goal=task.goal,
            interruption_point=task.interruption_point,
            events=task.events,
            run_id=f"task-{task.task_id}",
            created_at=task.updated_at,
        )
        return packet

    def retrieve_task_memory(self, task_id: str) -> TaskMemoryView:
        task = self.load_task(task_id)
        _manifest, candidates, packet = build_memory_snapshot(
            task_id=task.task_id,
            title=task.title,
            domain=task.domain,
            goal=task.goal,
            interruption_point=task.interruption_point,
            events=task.events,
            run_id=f"task-{task.task_id}",
            created_at=task.updated_at,
        )
        grouped = group_by_category(candidates)
        candidate_summaries = {
            category: [candidate.summary for candidate in items]
            for category, items in sorted(grouped.items())
        }
        return TaskMemoryView(
            task_id=task.task_id,
            title=task.title,
            domain=task.domain,
            goal=task.goal,
            interruption_point=task.interruption_point,
            event_count=len(task.events),
            task_version=task.task_version,
            candidate_summaries=candidate_summaries,
            resume_packet=packet,
        )

    def _task_path(self, task_id: str) -> Path:
        return self.tasks_dir / f"{task_id}.json"

    def load_idempotency_record(self, key: str) -> IdempotencyRecord | None:
        path = self._idempotency_path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise TaskStateCompatibilityError(f"idempotency record is not valid JSON: {path.name}") from exc
        return _idempotency_record_from_dict(cast(dict[str, Any], payload), path=path)

    def save_idempotency_record(
        self,
        *,
        key: str,
        request_fingerprint: str,
        status_code: int,
        response_payload: dict[str, Any],
    ) -> IdempotencyRecord:
        record = IdempotencyRecord(
            key=key,
            request_fingerprint=request_fingerprint,
            status_code=status_code,
            response_payload=response_payload,
            created_at=_utc_now(),
        )
        path = self._idempotency_path(key)
        path.write_text(json.dumps(asdict(record), indent=2) + "\n", encoding="utf-8")
        return record

    def ensure_idempotency_match(self, key: str, request_fingerprint: str) -> IdempotencyRecord | None:
        record = self.load_idempotency_record(key)
        if record is None:
            return None
        if record.request_fingerprint != request_fingerprint:
            raise IdempotencyConflictError(
                f"idempotency key reuse does not match the original write: {key}"
            )
        return record

    def build_idempotency_fingerprint(
        self,
        *,
        method: str,
        path: str,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> str:
        stable_payload = {
            "method": method,
            "path": path,
            "payload": payload,
            "if_match": headers.get("if-match"),
        }
        encoded = json.dumps(stable_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _maybe_load_task(self, task_id: str) -> ServiceTaskState | None:
        path = self._task_path(task_id)
        if not path.exists():
            return None
        try:
            raw_payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise TaskStateCompatibilityError(f"task state file is not valid JSON: {path.name}") from exc
        return _task_state_from_dict(cast(dict[str, Any], raw_payload), path=path)

    def _write_task(self, task: ServiceTaskState) -> None:
        path = self._task_path(task.task_id)
        path.write_text(json.dumps(asdict(task), indent=2) + "\n", encoding="utf-8")

    def _idempotency_path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.idempotency_dir / f"{digest}.json"


def _task_state_from_dict(payload: dict[str, Any], *, path: Path) -> ServiceTaskState:
    if not isinstance(payload, dict):
        raise TaskStateCompatibilityError(f"task state file must contain a JSON object: {path.name}")

    schema_version = str(payload.get("artifact_schema_version", SERVICE_TASK_STATE_SCHEMA_VERSION))
    if schema_version not in SUPPORTED_TASK_STATE_SCHEMAS:
        raise TaskStateCompatibilityError(
            f"unsupported task state schema in {path.name}: {schema_version}"
        )

    missing = [
        field_name
        for field_name in ("task_id", "title", "domain", "goal", "interruption_point", "created_at", "updated_at")
        if field_name not in payload
    ]
    if missing:
        raise TaskStateCompatibilityError(
            f"task state file missing required fields in {path.name}: {', '.join(missing)}"
        )

    events_payload = payload.get("events", [])
    if not isinstance(events_payload, list):
        raise TaskStateCompatibilityError(f"task state events must be a list in {path.name}")

    expected_items_payload = payload.get("expected_items", [])
    if not isinstance(expected_items_payload, list):
        raise TaskStateCompatibilityError(f"task state expected_items must be a list in {path.name}")

    return ServiceTaskState(
        task_id=str(payload["task_id"]),
        title=str(payload["title"]),
        domain=str(payload["domain"]),
        goal=str(payload["goal"]),
        interruption_point=str(payload["interruption_point"]),
        events=[_task_event_from_dict(item, path=path, index=index) for index, item in enumerate(events_payload)],
        expected_items=[
            _expected_item_from_dict(item, path=path, index=index)
            for index, item in enumerate(expected_items_payload)
        ],
        created_at=str(payload["created_at"]),
        updated_at=str(payload["updated_at"]),
        task_version=_parse_task_version(payload.get("task_version", 1), path=path),
        artifact_schema_version=SERVICE_TASK_STATE_SCHEMA_VERSION,
    )


def _idempotency_record_from_dict(payload: dict[str, Any], *, path: Path) -> IdempotencyRecord:
    if not isinstance(payload, dict):
        raise TaskStateCompatibilityError(f"idempotency record must contain a JSON object: {path.name}")
    missing = [
        field_name
        for field_name in ("key", "request_fingerprint", "status_code", "response_payload", "created_at")
        if field_name not in payload
    ]
    if missing:
        raise TaskStateCompatibilityError(
            f"idempotency record missing required fields in {path.name}: {', '.join(missing)}"
        )
    response_payload = payload["response_payload"]
    if not isinstance(response_payload, dict):
        raise TaskStateCompatibilityError(f"idempotency response_payload must be an object in {path.name}")
    return IdempotencyRecord(
        key=str(payload["key"]),
        request_fingerprint=str(payload["request_fingerprint"]),
        status_code=int(payload["status_code"]),
        response_payload=cast(dict[str, Any], response_payload),
        created_at=str(payload["created_at"]),
    )


def _task_event_from_dict(payload: dict[str, Any], *, path: Path, index: int) -> TaskEvent:
    if not isinstance(payload, dict):
        raise TaskStateCompatibilityError(f"task state event {index} must be an object in {path.name}")
    missing = [field_name for field_name in ("sequence", "actor", "text") if field_name not in payload]
    if missing:
        raise TaskStateCompatibilityError(
            f"task state event {index} missing required fields in {path.name}: {', '.join(missing)}"
        )
    return TaskEvent(
        sequence=int(payload["sequence"]),
        actor=str(payload["actor"]),
        text=str(payload["text"]),
        source_refs=[str(item) for item in payload.get("source_refs", [])],
        metadata=dict(payload.get("metadata", {})),
    )


def _expected_item_from_dict(payload: dict[str, Any], *, path: Path, index: int) -> ExpectedItem:
    if not isinstance(payload, dict):
        raise TaskStateCompatibilityError(f"task state expected item {index} must be an object in {path.name}")
    missing = [field_name for field_name in ("name", "category") if field_name not in payload]
    if missing:
        raise TaskStateCompatibilityError(
            f"task state expected item {index} missing required fields in {path.name}: {', '.join(missing)}"
        )
    return ExpectedItem(
        name=str(payload["name"]),
        category=str(payload["category"]),
        keywords=[str(item) for item in payload.get("keywords", [])],
    )


def _parse_task_version(value: Any, *, path: Path) -> int:
    try:
        task_version = int(value)
    except (TypeError, ValueError) as exc:
        raise TaskStateCompatibilityError(f"task state task_version must be an integer in {path.name}") from exc
    if task_version < 1:
        raise TaskStateCompatibilityError(f"task state task_version must be >= 1 in {path.name}")
    return task_version


def _check_expected_task_version(
    task_id: str,
    task: ServiceTaskState | None,
    expected_task_version: int | None,
) -> None:
    if expected_task_version is None:
        return
    actual_version = None if task is None else task.task_version
    if actual_version != expected_task_version:
        raise TaskVersionConflictError(
            task_id,
            expected_version=expected_task_version,
            actual_version=actual_version,
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
