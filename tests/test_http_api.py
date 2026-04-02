from __future__ import annotations

import io
import tempfile
import unittest
from dataclasses import asdict
from email.message import Message
from http import HTTPStatus
from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock, patch

from memoryvault.http_api import (
    InvalidJsonBodyError,
    _build_handler,
    create_http_server,
    handle_http_request,
    run_http_server,
)
from memoryvault.importer import load_scenario_file
from memoryvault.pipeline import run_scenario_file
from memoryvault.service import LocalMemoryService


class HttpApiTests(unittest.TestCase):
    def test_http_end_to_end_flow_returns_resume_packet_and_memory_view(self) -> None:
        scenario = load_scenario_file("examples/interrupted_runs/taskbench_like_tool_chain.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            status, state_payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/tool-chain/state",
                payload={
                    "api_version": "v1",
                    "title": scenario.title,
                    "domain": scenario.domain,
                    "goal": scenario.goal,
                    "interruption_point": scenario.interruption_point,
                    "expected_items": [asdict(item) for item in scenario.expected_items],
                },
            )
            self.assertEqual(status, 200)
            self.assertTrue(state_payload["ok"])
            self.assertEqual(state_payload["api_version"], "v1")
            self.assertEqual(state_payload["data"]["task"]["task_id"], "tool-chain")

            status, append_payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={
                    "api_version": "v1",
                    "task_id": "tool-chain",
                    "events": [asdict(event) for event in scenario.events],
                },
            )
            self.assertEqual(status, 200)
            self.assertEqual(append_payload["data"]["appended_event_count"], len(scenario.events))
            self.assertEqual(append_payload["data"]["task"]["task_version"], 2)

            status, packet_payload = handle_http_request(
                service,
                method="GET",
                path="/v1/tasks/tool-chain/resume-packet",
            )
            self.assertEqual(status, 200)
            self.assertEqual(packet_payload["data"]["final_goal_guard"], scenario.goal)
            self.assertTrue(any("reserve the selected room" in item.lower() for item in packet_payload["data"]["current_focus"]))

            status, view_payload = handle_http_request(
                service,
                method="POST",
                path="/v1/tasks/tool-chain/retrieve",
                payload={"api_version": "v1"},
            )
            self.assertEqual(status, 200)
            self.assertEqual(view_payload["data"]["task_id"], "tool-chain")
            self.assertEqual(view_payload["data"]["event_count"], len(scenario.events))
            self.assertEqual(view_payload["data"]["task_version"], 2)
            self.assertIn("constraint", view_payload["data"]["candidate_summaries"])

    def test_http_resume_packet_matches_cli_content_for_same_input(self) -> None:
        scenario = load_scenario_file("examples/interrupted_runs/swe_bench_like_bugfix.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            handle_http_request(
                service,
                method="PUT",
                path=f"/v1/tasks/{scenario.scenario_id}/state",
                payload={
                    "api_version": "v1",
                    "title": scenario.title,
                    "domain": scenario.domain,
                    "goal": scenario.goal,
                    "interruption_point": scenario.interruption_point,
                    "expected_items": [asdict(item) for item in scenario.expected_items],
                },
            )
            handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={
                    "api_version": "v1",
                    "task_id": scenario.scenario_id,
                    "events": [asdict(event) for event in scenario.events],
                },
            )
            _status, http_packet = handle_http_request(
                service,
                method="GET",
                path=f"/v1/tasks/{scenario.scenario_id}/resume-packet",
            )

            _run_dir, _manifest, cli_packet, _evaluation = run_scenario_file(
                "examples/interrupted_runs/swe_bench_like_bugfix.json",
                base_dir=temp_dir,
            )
            cli_payload = asdict(cli_packet)
            cli_payload.pop("run_id", None)
            http_payload = http_packet["data"]
            http_payload.pop("run_id", None)
            self.assertEqual(http_payload, cli_payload)

    def test_http_returns_not_found_for_missing_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            status, payload = handle_http_request(
                service,
                method="GET",
                path="/v1/tasks/missing/resume-packet",
            )

        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "task_not_found")
        self.assertIn("task not found", payload["error"]["message"])

    def test_http_returns_conflict_for_incompatible_saved_task_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task_path = Path(temp_dir) / "service_state" / "tasks" / "demo.json"
            task_path.parent.mkdir(parents=True, exist_ok=True)
            task_path.write_text(
                '{\n'
                '  "artifact_schema_version": "service_task_state.v9",\n'
                '  "task_id": "demo",\n'
                '  "title": "Demo",\n'
                '  "domain": "coding",\n'
                '  "goal": "Stay on track.",\n'
                '  "interruption_point": "Paused after repro.",\n'
                '  "events": [],\n'
                '  "expected_items": [],\n'
                '  "created_at": "2026-03-27T00:00:00+00:00",\n'
                '  "updated_at": "2026-03-27T00:00:00+00:00"\n'
                '}\n',
                encoding="utf-8",
            )
            service = LocalMemoryService(base_dir=temp_dir)

            status, payload = handle_http_request(
                service,
                method="GET",
                path="/v1/tasks/demo/resume-packet",
            )

        self.assertEqual(status, HTTPStatus.CONFLICT)
        self.assertEqual(payload["error"]["code"], "incompatible_task_state")
        self.assertIn("unsupported task state schema", payload["error"]["message"])

    def test_handle_http_request_reports_bad_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)

            status, payload = handle_http_request(service, method="POST", path="/v1/events", payload={})
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertEqual(payload["error"]["code"], "invalid_request")
            self.assertIn("task_id is required", payload["error"]["message"])

            status, payload = handle_http_request(service, method="PUT", path="/v1/tasks/new/state", payload={})
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertIn("missing required task fields", payload["error"]["message"])

            status, payload = handle_http_request(service, method="POST", path="/v1/tasks/missing/retrieve", payload={"api_version": "v1"})
            self.assertEqual(status, HTTPStatus.NOT_FOUND)
            self.assertIn("task not found", payload["error"]["message"])

            status, payload = handle_http_request(service, method="GET", path="/not-real")
            self.assertEqual(status, HTTPStatus.NOT_FOUND)
            self.assertIn("unknown endpoint", payload["error"]["message"])

            status, payload = handle_http_request(service, method="GET", path="/not-real", payload={"api_version": "v9"})
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertEqual(payload["error"]["code"], "unsupported_api_version")

            status, payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={"task_id": "demo", "events": "bad-shape"},
            )
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertIn("events must be a list", payload["error"]["message"])

    def test_create_http_server_and_run_http_server_delegate_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)

            with patch("memoryvault.http_api.ThreadingHTTPServer", autospec=True) as mock_server_class:
                sentinel = object()
                mock_server_class.return_value = sentinel
                server = create_http_server(service, host="127.0.0.1", port=8877)

            self.assertIs(server, sentinel)
            mock_server_class.assert_called_once()
            self.assertEqual(mock_server_class.call_args.args[0], ("127.0.0.1", 8877))

            fake_server = Mock()
            fake_server.serve_forever.side_effect = RuntimeError("stop")
            with patch("memoryvault.http_api.create_http_server", return_value=fake_server) as mock_create_server:
                with self.assertRaises(RuntimeError):
                    run_http_server(host="127.0.0.1", port=8877, base_dir=temp_dir)

            mock_create_server.assert_called_once()
            fake_server.server_close.assert_called_once()

    def test_handler_class_reads_and_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            handler_class = _build_handler(service)

            handler = cast(Any, handler_class.__new__(handler_class))
            handler.headers = Message()
            handler.headers["Content-Length"] = "17"
            handler.rfile = io.BytesIO(b'{"hello":"world"}')
            handler.wfile = io.BytesIO()
            responses: list[HTTPStatus] = []
            headers: list[tuple[str, str]] = []
            handler.send_response = lambda status, message=None: responses.append(HTTPStatus(status))
            handler.send_header = lambda key, value: headers.append((key, value))
            handler.end_headers = lambda: headers.append(("END", ""))

            payload = handler._read_json_body()
            self.assertEqual(payload, {"hello": "world"})

            handler.headers = Message()
            handler.headers["Content-Length"] = "3"
            handler.rfile = io.BytesIO(b"{x}")
            with self.assertRaisesRegex(Exception, "valid JSON"):
                handler._read_json_body()

            handler._send_json(HTTPStatus.OK, {"ok": True})
            self.assertEqual(responses, [HTTPStatus.OK])
            self.assertTrue(any(key == "Content-Type" for key, _ in headers))
            self.assertIn(b'"ok": true', handler.wfile.getvalue())
            self.assertIsNone(cast(Any, handler).log_message("ignored"))

    def test_handler_methods_delegate_to_request_handler(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            handler_class = _build_handler(service)

            for method_name, path, expected_method in [
                ("do_POST", "/v1/events", "POST"),
                ("do_PUT", "/v1/tasks/demo/state", "PUT"),
                ("do_GET", "/v1/tasks/demo/resume-packet", "GET"),
            ]:
                handler = cast(Any, handler_class.__new__(handler_class))
                handler.path = path
                handler.headers = Message()
                handler._read_json_body = lambda: {"demo": True}
                handler._send_json = Mock()

                with patch("memoryvault.http_api.handle_http_request", return_value=(HTTPStatus.OK, {"ok": True})) as mock_handle:
                    getattr(handler, method_name)()

                if expected_method == "GET":
                    mock_handle.assert_called_once_with(
                        service,
                        method="GET",
                        path=path,
                        headers={},
                    )
                else:
                    mock_handle.assert_called_once_with(
                        service,
                        method=expected_method,
                        path=path,
                        payload={"demo": True},
                        headers={},
                    )
                handler._send_json.assert_called_once_with(HTTPStatus.OK, {"ok": True})

    def test_handler_methods_return_bad_request_for_invalid_json_and_invalid_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            handler_class = _build_handler(service)

            bad_json_handler = cast(Any, handler_class.__new__(handler_class))
            bad_json_handler.path = "/v1/events"
            bad_json_handler._read_json_body = Mock(side_effect=InvalidJsonBodyError("request body must be valid JSON"))
            bad_json_handler._send_json = Mock()

            getattr(bad_json_handler, "do_POST")()
            status, payload = bad_json_handler._send_json.call_args.args
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertEqual(payload["error"]["code"], "invalid_request")

            non_object_handler = cast(Any, handler_class.__new__(handler_class))
            non_object_handler.path = "/v1/events"
            non_object_handler.headers = Message()
            non_object_handler._read_json_body = Mock(return_value=["bad-shape"])
            non_object_handler._send_json = Mock()

            getattr(non_object_handler, "do_POST")()
            status, payload = non_object_handler._send_json.call_args.args
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertEqual(payload["error"]["code"], "invalid_request")
            self.assertIn("request body must be a JSON object", payload["error"]["message"])

            status, payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={"task_id": "demo", "events": [123]},
            )
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertIn("each event must be an object", payload["error"]["message"])

            status, payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={"task_id": "demo", "events": [{"actor": "assistant", "text": "Missing sequence."}]},
            )
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertIn("each event must include: sequence", payload["error"]["message"])

            status, payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={
                    "task_id": "demo",
                    "events": [{"sequence": 1, "actor": "assistant", "text": "Bad refs.", "source_refs": "notes.md"}],
                },
            )
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertIn("event source_refs must be a list", payload["error"]["message"])

            status, payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={
                    "task_id": "demo",
                    "events": [{"sequence": 1, "actor": "assistant", "text": "Bad metadata.", "metadata": "bad"}],
                },
            )
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertIn("event metadata must be an object", payload["error"]["message"])

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={
                    "title": "Demo",
                    "domain": "coding",
                    "goal": "Stay on track.",
                    "interruption_point": "Paused.",
                    "expected_items": [123],
                },
            )
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertIn("each expected item must be an object", payload["error"]["message"])

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={
                    "title": "Demo",
                    "domain": "coding",
                    "goal": "Stay on track.",
                    "interruption_point": "Paused.",
                    "expected_items": [{"name": "keep source"}],
                },
            )
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertIn("each expected item must include: category", payload["error"]["message"])

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={
                    "title": "Demo",
                    "domain": "coding",
                    "goal": "Stay on track.",
                    "interruption_point": "Paused.",
                    "expected_items": [{"name": "keep source", "category": "source", "keywords": "notes.md"}],
                },
            )
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertIn("expected item keywords must be a list", payload["error"]["message"])

    def test_http_rejects_non_object_request_body_without_mutating_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload=cast(Any, ["bad-shape"]),
            )
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertEqual(payload["error"]["code"], "invalid_request")
            self.assertIn("request body must be a JSON object", payload["error"]["message"])
            self.assertFalse((Path(temp_dir) / "service_state" / "tasks" / "demo.json").exists())

    def test_http_partial_update_and_repeated_append_keep_versions_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={
                    "title": "Demo",
                    "domain": "coding",
                    "goal": "Stay on track.",
                    "interruption_point": "Paused after repro.",
                },
            )
            self.assertEqual(status, HTTPStatus.OK)
            self.assertEqual(payload["data"]["task"]["task_version"], 1)

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={"goal": "Stay on track without touching shipping."},
            )
            self.assertEqual(status, HTTPStatus.OK)
            self.assertEqual(payload["data"]["task"]["task_version"], 2)
            self.assertEqual(payload["data"]["task"]["title"], "Demo")

            status, payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={"task_id": "demo", "events": [{"sequence": 1, "actor": "assistant", "text": "Goal: Stay on track."}]},
            )
            self.assertEqual(status, HTTPStatus.OK)
            self.assertEqual(payload["data"]["task"]["task_version"], 3)

            status, payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={"task_id": "demo", "events": [{"sequence": 2, "actor": "assistant", "text": "Constraint: Do not touch shipping."}]},
            )
            self.assertEqual(status, HTTPStatus.OK)
            self.assertEqual(payload["data"]["task"]["task_version"], 4)

    def test_http_if_match_allows_current_write_and_rejects_stale_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={
                    "title": "Demo",
                    "domain": "coding",
                    "goal": "Stay on track.",
                    "interruption_point": "Paused after repro.",
                },
            )
            self.assertEqual(status, HTTPStatus.OK)
            self.assertEqual(payload["data"]["task"]["task_version"], 1)

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={"goal": "Stay on track without touching shipping."},
                headers={"If-Match": "1"},
            )
            self.assertEqual(status, HTTPStatus.OK)
            self.assertEqual(payload["data"]["task"]["task_version"], 2)

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={"goal": "This stale write should fail."},
                headers={"If-Match": "1"},
            )
            self.assertEqual(status, HTTPStatus.PRECONDITION_FAILED)
            self.assertEqual(payload["error"]["code"], "precondition_failed")
            self.assertIn("expected 1, current is 2", payload["error"]["message"])

    def test_http_if_match_is_supported_for_event_appends(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={
                    "title": "Demo",
                    "domain": "coding",
                    "goal": "Stay on track.",
                    "interruption_point": "Paused after repro.",
                },
            )

            status, payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={"task_id": "demo", "events": [{"sequence": 1, "actor": "assistant", "text": "Goal: Stay on track."}]},
                headers={"If-Match": "1"},
            )
            self.assertEqual(status, HTTPStatus.OK)
            self.assertEqual(payload["data"]["task"]["task_version"], 2)

            status, payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={"task_id": "demo", "events": [{"sequence": 2, "actor": "assistant", "text": "Constraint: Do not touch shipping."}]},
                headers={"If-Match": "1"},
            )
            self.assertEqual(status, HTTPStatus.PRECONDITION_FAILED)
            self.assertEqual(payload["error"]["code"], "precondition_failed")

    def test_http_rejects_invalid_if_match_header(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={
                    "title": "Demo",
                    "domain": "coding",
                    "goal": "Stay on track.",
                    "interruption_point": "Paused after repro.",
                },
            )

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={"goal": "Bad header should fail."},
                headers={"If-Match": "bad"},
            )
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertEqual(payload["error"]["code"], "invalid_request")
            self.assertIn("If-Match must be the current task_version", payload["error"]["message"])

    def test_http_replays_same_state_write_for_same_idempotency_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            request_payload = {
                "title": "Demo",
                "domain": "coding",
                "goal": "Stay on track.",
                "interruption_point": "Paused after repro.",
            }

            first_status, first_payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload=request_payload,
                headers={"Idempotency-Key": "state-write-1"},
            )
            self.assertEqual(first_status, HTTPStatus.OK)
            self.assertEqual(first_payload["data"]["task"]["task_version"], 1)

            second_status, second_payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload=request_payload,
                headers={"Idempotency-Key": "state-write-1"},
            )
            self.assertEqual(second_status, HTTPStatus.OK)
            self.assertEqual(second_payload, first_payload)
            self.assertEqual(service.load_task("demo").task_version, 1)

    def test_http_replays_same_event_append_for_same_idempotency_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)
            handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={
                    "title": "Demo",
                    "domain": "coding",
                    "goal": "Stay on track.",
                    "interruption_point": "Paused after repro.",
                },
            )
            event_payload = {
                "task_id": "demo",
                "events": [{"sequence": 1, "actor": "assistant", "text": "Goal: Stay on track."}],
            }

            first_status, first_payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload=event_payload,
                headers={"Idempotency-Key": "append-1", "If-Match": "1"},
            )
            self.assertEqual(first_status, HTTPStatus.OK)
            self.assertEqual(first_payload["data"]["task"]["task_version"], 2)

            second_status, second_payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload=event_payload,
                headers={"Idempotency-Key": "append-1", "If-Match": "1"},
            )
            self.assertEqual(second_status, HTTPStatus.OK)
            self.assertEqual(second_payload, first_payload)
            self.assertEqual(len(service.load_task("demo").events), 1)

    def test_http_mixed_write_sequence_keeps_state_stable_across_replays_and_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={
                    "title": "Demo",
                    "domain": "coding",
                    "goal": "Stay on track.",
                    "interruption_point": "Paused after repro.",
                },
                headers={"Idempotency-Key": "state-1"},
            )
            self.assertEqual(status, HTTPStatus.OK)
            self.assertEqual(payload["data"]["task"]["task_version"], 1)

            append_status, append_payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={"task_id": "demo", "events": [{"sequence": 1, "actor": "assistant", "text": "Goal: Stay on track."}]},
                headers={"If-Match": "1", "Idempotency-Key": "append-1"},
            )
            self.assertEqual(append_status, HTTPStatus.OK)
            self.assertEqual(append_payload["data"]["task"]["task_version"], 2)

            replay_status, replay_payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={"task_id": "demo", "events": [{"sequence": 1, "actor": "assistant", "text": "Goal: Stay on track."}]},
                headers={"If-Match": "1", "Idempotency-Key": "append-1"},
            )
            self.assertEqual(replay_status, HTTPStatus.OK)
            self.assertEqual(replay_payload, append_payload)

            stale_status, stale_payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={"task_id": "demo", "events": [{"sequence": 2, "actor": "assistant", "text": "Constraint: Do not touch shipping."}]},
                headers={"If-Match": "1"},
            )
            self.assertEqual(stale_status, HTTPStatus.PRECONDITION_FAILED)
            self.assertEqual(stale_payload["error"]["code"], "precondition_failed")

            malformed_status, malformed_payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={"task_id": "demo", "events": [{"sequence": 2, "actor": "assistant"}]},
                headers={"If-Match": "2"},
            )
            self.assertEqual(malformed_status, HTTPStatus.BAD_REQUEST)
            self.assertEqual(malformed_payload["error"]["code"], "invalid_request")

            update_status, update_payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={"goal": "Stay on track without touching shipping."},
                headers={"If-Match": "2", "Idempotency-Key": "state-2"},
            )
            self.assertEqual(update_status, HTTPStatus.OK)
            self.assertEqual(update_payload["data"]["task"]["task_version"], 3)

            update_replay_status, update_replay_payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={"goal": "Stay on track without touching shipping."},
                headers={"If-Match": "2", "Idempotency-Key": "state-2"},
            )
            self.assertEqual(update_replay_status, HTTPStatus.OK)
            self.assertEqual(update_replay_payload, update_payload)

            retrieve_status, retrieve_payload = handle_http_request(
                service,
                method="POST",
                path="/v1/tasks/demo/retrieve",
                payload={"api_version": "v1"},
            )
            self.assertEqual(retrieve_status, HTTPStatus.OK)
            self.assertEqual(retrieve_payload["data"]["event_count"], 1)
            self.assertEqual(retrieve_payload["data"]["task_version"], 3)
            self.assertEqual(retrieve_payload["data"]["goal"], "Stay on track without touching shipping.")

    def test_http_rejects_idempotency_key_reuse_for_different_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)

            first_status, _first_payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={
                    "title": "Demo",
                    "domain": "coding",
                    "goal": "Stay on track.",
                    "interruption_point": "Paused after repro.",
                },
                headers={"Idempotency-Key": "shared-key"},
            )
            self.assertEqual(first_status, HTTPStatus.OK)

            second_status, second_payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={
                    "title": "Demo",
                    "domain": "coding",
                    "goal": "A different write should fail.",
                    "interruption_point": "Paused after repro.",
                },
                headers={"Idempotency-Key": "shared-key"},
            )
            self.assertEqual(second_status, HTTPStatus.CONFLICT)
            self.assertEqual(second_payload["error"]["code"], "idempotency_conflict")

    def test_http_rejects_empty_idempotency_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/demo/state",
                payload={
                    "title": "Demo",
                    "domain": "coding",
                    "goal": "Stay on track.",
                    "interruption_point": "Paused after repro.",
                },
                headers={"Idempotency-Key": "   "},
            )
            self.assertEqual(status, HTTPStatus.BAD_REQUEST)
            self.assertEqual(payload["error"]["code"], "invalid_request")
            self.assertIn("Idempotency-Key must not be empty", payload["error"]["message"])

    def test_http_accepts_legacy_request_shapes_without_api_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = LocalMemoryService(base_dir=temp_dir)

            status, payload = handle_http_request(
                service,
                method="PUT",
                path="/v1/tasks/legacy/state",
                payload={
                    "title": "Legacy",
                    "domain": "coding",
                    "goal": "Stay on track.",
                    "interruption_point": "Paused after repro.",
                },
            )
            self.assertEqual(status, HTTPStatus.OK)
            self.assertEqual(payload["data"]["task"]["artifact_schema_version"], "service_task_state.v1")

            status, payload = handle_http_request(
                service,
                method="POST",
                path="/v1/events",
                payload={
                    "task_id": "legacy",
                    "events": [{"sequence": 1, "actor": "assistant", "text": "Goal: Stay on track."}],
                },
            )
            self.assertEqual(status, HTTPStatus.OK)
            self.assertEqual(payload["data"]["task"]["task_version"], 2)


if __name__ == "__main__":
    unittest.main()
