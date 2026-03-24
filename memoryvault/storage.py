from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import EvaluationReport, MemoryCandidate, ResumePacket, RunManifest, Scenario, TaskEvent


class LocalArtifactStore:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_run(
        self,
        manifest: RunManifest,
        scenario: Scenario,
        events: list[TaskEvent],
        candidates: list[MemoryCandidate],
        packet: ResumePacket,
        evaluation: EvaluationReport,
    ) -> Path:
        run_dir = self.base_dir / manifest.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        self._write_json(run_dir / "manifest.json", manifest)
        self._write_json(run_dir / "scenario.json", scenario)
        self._write_json(run_dir / "events.json", events)
        self._write_json(run_dir / "candidates.json", candidates)
        self._write_json(run_dir / "resume_packet.json", packet)
        self._write_json(run_dir / "evaluation.json", evaluation)
        self._append_jsonl(self.base_dir / "improvement_log.jsonl", evaluation)

        return run_dir

    def save_json_artifact(self, run_dir: str | Path, filename: str, payload: Any) -> Path:
        target = Path(run_dir) / filename
        self._write_json(target, payload)
        return target

    def _write_json(self, path: Path, payload: Any) -> None:
        path.write_text(
            json.dumps(_normalize(payload), indent=2) + "\n",
            encoding="utf-8",
        )

    def _append_jsonl(self, path: Path, payload: Any) -> None:
        encoded = json.dumps(_normalize(payload))
        with path.open("a", encoding="utf-8") as handle:
            handle.write(encoded + "\n")


def _normalize(payload: Any) -> Any:
    if hasattr(payload, "__dataclass_fields__"):
        return asdict(payload)
    if isinstance(payload, list):
        return [_normalize(item) for item in payload]
    if isinstance(payload, dict):
        return {key: _normalize(value) for key, value in payload.items()}
    return payload
