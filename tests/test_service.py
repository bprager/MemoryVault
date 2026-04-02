from __future__ import annotations

import tempfile
import unittest
from dataclasses import asdict
import json
from pathlib import Path

from memoryvault.importer import load_scenario_file
from memoryvault.pipeline import run_scenario_file
from memoryvault.service import (
    IdempotencyConflictError,
    LocalMemoryService,
    TaskNotFoundError,
    TaskStateCompatibilityError,
    TaskVersionConflictError,
)


class LocalMemoryServiceTests(unittest.TestCase):
    def test_service_round_trip_builds_expected_resume_packet(self) -> None:
        scenario = load_scenario_file("examples/interrupted_runs/taskbench_like_tool_chain.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            task = service.import_scenario("tool-chain-task", scenario)
            packet = service.get_resume_packet("tool-chain-task")
            view = service.retrieve_task_memory("tool-chain-task")

            self.assertEqual(task.task_id, "tool-chain-task")
            self.assertEqual(len(task.events), len(scenario.events))
            self.assertEqual(task.task_version, 2)
            self.assertEqual(packet.final_goal_guard, scenario.goal)
            self.assertTrue(any("reserve the selected room" in item.lower() for item in packet.current_focus))
            self.assertIn("constraint", view.candidate_summaries)
            self.assertEqual(view.event_count, len(scenario.events))
            self.assertEqual(view.task_version, 2)
            self.assertEqual(view.resume_packet.final_goal_guard, scenario.goal)
            task_path = Path(temp_dir) / "service_state" / "tasks" / "tool-chain-task.json"
            self.assertTrue(task_path.exists())
            saved = json.loads(task_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["artifact_schema_version"], "service_task_state.v1")
            self.assertEqual(saved["task_version"], 2)

    def test_service_resume_packet_matches_cli_content_for_same_input(self) -> None:
        scenario = load_scenario_file("examples/interrupted_runs/swe_bench_like_bugfix.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            service.import_scenario(scenario.scenario_id, scenario)
            service_packet = service.get_resume_packet(scenario.scenario_id)

            _run_dir, _manifest, cli_packet, _evaluation = run_scenario_file(
                "examples/interrupted_runs/swe_bench_like_bugfix.json",
                base_dir=temp_dir,
            )

            service_payload = asdict(service_packet)
            cli_payload = asdict(cli_packet)
            service_payload.pop("run_id", None)
            cli_payload.pop("run_id", None)
            self.assertEqual(service_payload, cli_payload)

    def test_append_events_rejects_unknown_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)

            with self.assertRaises(TaskNotFoundError):
                service.append_events("missing-task", [])

    def test_upsert_task_state_updates_existing_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            service.upsert_task_state(
                "demo-task",
                title="Original title",
                domain="coding",
                goal="Keep the fix on track.",
                interruption_point="Paused after the first repro.",
            )

            updated = service.upsert_task_state(
                "demo-task",
                goal="Keep the fix on track without touching shipping.",
            )

            self.assertEqual(updated.title, "Original title")
            self.assertEqual(updated.domain, "coding")
            self.assertEqual(updated.goal, "Keep the fix on track without touching shipping.")
            self.assertEqual(updated.task_version, 2)

    def test_repeated_event_appends_increase_task_version_and_preserve_existing_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            service.upsert_task_state(
                "demo-task",
                title="Original title",
                domain="coding",
                goal="Keep the fix on track.",
                interruption_point="Paused after the first repro.",
            )

            service.append_events("demo-task", [scenario_event(1, "Goal: Keep the fix on track.")])
            updated = service.append_events("demo-task", [scenario_event(2, "Constraint: Do not touch shipping.")])

            self.assertEqual(updated.task_version, 3)
            self.assertEqual(len(updated.events), 2)
            self.assertEqual(updated.events[0].sequence, 1)
            self.assertEqual(updated.events[1].sequence, 2)

    def test_upsert_task_state_rejects_stale_expected_task_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            created = service.upsert_task_state(
                "demo-task",
                title="Original title",
                domain="coding",
                goal="Keep the fix on track.",
                interruption_point="Paused after the first repro.",
            )
            self.assertEqual(created.task_version, 1)

            updated = service.upsert_task_state(
                "demo-task",
                goal="Keep the fix on track without touching shipping.",
                expected_task_version=1,
            )
            self.assertEqual(updated.task_version, 2)

            with self.assertRaisesRegex(TaskVersionConflictError, "expected 1, current is 2"):
                service.upsert_task_state(
                    "demo-task",
                    goal="Stale write should fail.",
                    expected_task_version=1,
                )

    def test_append_events_rejects_stale_expected_task_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            service.upsert_task_state(
                "demo-task",
                title="Original title",
                domain="coding",
                goal="Keep the fix on track.",
                interruption_point="Paused after the first repro.",
            )

            updated = service.append_events(
                "demo-task",
                [scenario_event(1, "Goal: Keep the fix on track.")],
                expected_task_version=1,
            )
            self.assertEqual(updated.task_version, 2)

            with self.assertRaisesRegex(TaskVersionConflictError, "expected 1, current is 2"):
                service.append_events(
                    "demo-task",
                    [scenario_event(2, "Constraint: Do not touch shipping.")],
                    expected_task_version=1,
                )

    def test_legacy_task_state_file_without_schema_marker_loads_as_v1_and_rewrites_on_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task_path = Path(temp_dir) / "service_state" / "tasks" / "legacy-task.json"
            task_path.parent.mkdir(parents=True, exist_ok=True)
            task_path.write_text(
                json.dumps(
                    {
                        "task_id": "legacy-task",
                        "title": "Legacy task",
                        "domain": "coding",
                        "goal": "Keep the fix on track.",
                        "interruption_point": "Paused after repro.",
                        "events": [{"sequence": 1, "actor": "assistant", "text": "Goal: Keep the fix on track."}],
                        "expected_items": [{"name": "keep_goal", "category": "goal"}],
                        "created_at": "2026-03-27T00:00:00+00:00",
                        "updated_at": "2026-03-27T00:00:00+00:00",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            service = LocalMemoryService(base_dir=temp_dir)
            loaded = service.load_task("legacy-task")
            self.assertEqual(loaded.artifact_schema_version, "service_task_state.v1")
            self.assertEqual(loaded.task_version, 1)
            self.assertEqual(loaded.expected_items[0].keywords, [])

            updated = service.append_events("legacy-task", [scenario_event(2, "Constraint: Do not touch shipping.")])
            self.assertEqual(updated.task_version, 2)

            saved = json.loads(task_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["artifact_schema_version"], "service_task_state.v1")
            self.assertEqual(saved["task_version"], 2)

    def test_unsupported_task_state_schema_raises_clear_compatibility_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task_path = Path(temp_dir) / "service_state" / "tasks" / "bad-task.json"
            task_path.parent.mkdir(parents=True, exist_ok=True)
            task_path.write_text(
                json.dumps(
                    {
                        "artifact_schema_version": "service_task_state.v9",
                        "task_id": "bad-task",
                        "title": "Bad task",
                        "domain": "coding",
                        "goal": "Keep the fix on track.",
                        "interruption_point": "Paused after repro.",
                        "events": [],
                        "expected_items": [],
                        "created_at": "2026-03-27T00:00:00+00:00",
                        "updated_at": "2026-03-27T00:00:00+00:00",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            service = LocalMemoryService(base_dir=temp_dir)
            with self.assertRaisesRegex(TaskStateCompatibilityError, "unsupported task state schema"):
                service.load_task("bad-task")

    def test_idempotency_record_round_trip_and_conflict_detection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            fingerprint = service.build_idempotency_fingerprint(
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={"goal": "Stay on track."},
                headers={"if-match": "1"},
            )

            self.assertIsNone(service.ensure_idempotency_match("demo-key", fingerprint))

            service.save_idempotency_record(
                key="demo-key",
                request_fingerprint=fingerprint,
                status_code=200,
                response_payload={"ok": True},
            )

            loaded = service.ensure_idempotency_match("demo-key", fingerprint)
            assert loaded is not None
            self.assertEqual(loaded.status_code, 200)
            self.assertEqual(loaded.response_payload, {"ok": True})

            with self.assertRaisesRegex(IdempotencyConflictError, "idempotency key reuse does not match"):
                service.ensure_idempotency_match("demo-key", "different-fingerprint")


def scenario_event(sequence: int, text: str):
    from memoryvault.models import TaskEvent

    return TaskEvent(sequence=sequence, actor="assistant", text=text)


if __name__ == "__main__":
    unittest.main()
