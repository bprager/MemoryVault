from __future__ import annotations

import json
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .models import ExpectedItem, TaskEvent, to_dict
from .service import (
    IdempotencyConflictError,
    LocalMemoryService,
    TaskNotFoundError,
    TaskStateCompatibilityError,
    TaskVersionConflictError,
)

HTTP_API_VERSION = "v1"
TASK_STATE_PATTERN = re.compile(r"^/v1/tasks/(?P<task_id>[^/]+)/state$")
RESUME_PACKET_PATTERN = re.compile(r"^/v1/tasks/(?P<task_id>[^/]+)/resume-packet$")
RETRIEVE_PATTERN = re.compile(r"^/v1/tasks/(?P<task_id>[^/]+)/retrieve$")


class InvalidJsonBodyError(ValueError):
    """Raised when an HTTP request body is not valid JSON."""


def create_http_server(
    service: LocalMemoryService,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> ThreadingHTTPServer:
    handler = _build_handler(service)
    return ThreadingHTTPServer((host, port), handler)


def run_http_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    base_dir: str | Path = "var/memoryvault",
) -> None:
    service = LocalMemoryService(base_dir=base_dir)
    server = create_http_server(service, host=host, port=port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def handle_http_request(
    service: LocalMemoryService,
    *,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[HTTPStatus, Any]:
    request_path = urlparse(path).path
    if payload is None:
        body: dict[str, Any] = {}
    elif not isinstance(payload, dict):
        return _error_response(
            HTTPStatus.BAD_REQUEST,
            request_path,
            "invalid_request",
            "request body must be a JSON object",
        )
    else:
        body = payload
    request_headers = _normalize_headers(headers)
    version_error = _validate_api_version(body)
    if version_error is not None:
        return version_error

    try:
        idempotency_result = _handle_idempotency_preflight(
            service,
            method=method,
            path=request_path,
            payload=body,
            headers=request_headers,
        )
    except ValueError as exc:
        return _error_response(HTTPStatus.BAD_REQUEST, request_path, "invalid_request", str(exc))
    if idempotency_result is not None:
        return idempotency_result

    if method == "POST" and request_path == "/v1/events":
        task_id = str(body.get("task_id", "")).strip()
        if not task_id:
            return _finalize_idempotent_response(
                service,
                method=method,
                path=request_path,
                payload=body,
                headers=request_headers,
                response=_error_response(HTTPStatus.BAD_REQUEST, request_path, "invalid_request", "task_id is required"),
            )
        if "events" in body and not isinstance(body["events"], list):
            return _finalize_idempotent_response(
                service,
                method=method,
                path=request_path,
                payload=body,
                headers=request_headers,
                response=_error_response(HTTPStatus.BAD_REQUEST, request_path, "invalid_request", "events must be a list"),
            )
        try:
            expected_task_version = _parse_if_match_task_version(request_headers, task_id)
            events = [_task_event_from_payload(item) for item in body.get("events", [])]
            task = service.append_events(task_id, events, expected_task_version=expected_task_version)
        except TaskVersionConflictError as exc:
            return _finalize_idempotent_response(
                service,
                method=method,
                path=request_path,
                payload=body,
                headers=request_headers,
                response=_error_response(HTTPStatus.PRECONDITION_FAILED, request_path, "precondition_failed", str(exc)),
            )
        except ValueError as exc:
            return _finalize_idempotent_response(
                service,
                method=method,
                path=request_path,
                payload=body,
                headers=request_headers,
                response=_error_response(HTTPStatus.BAD_REQUEST, request_path, "invalid_request", str(exc)),
            )
        except TaskNotFoundError:
            return _finalize_idempotent_response(
                service,
                method=method,
                path=request_path,
                payload=body,
                headers=request_headers,
                response=_error_response(
                    HTTPStatus.NOT_FOUND,
                    request_path,
                    "task_not_found",
                    f"task not found: {task_id}",
                ),
            )
        except TaskStateCompatibilityError as exc:
            return _finalize_idempotent_response(
                service,
                method=method,
                path=request_path,
                payload=body,
                headers=request_headers,
                response=_error_response(HTTPStatus.CONFLICT, request_path, "incompatible_task_state", str(exc)),
            )
        return _finalize_idempotent_response(
            service,
            method=method,
            path=request_path,
            payload=body,
            headers=request_headers,
            response=_success_response(
                HTTPStatus.OK,
                request_path,
                {"task": to_dict(task), "appended_event_count": len(events)},
            ),
        )

    if method == "PUT":
        match = TASK_STATE_PATTERN.match(request_path)
        if match:
            task_id = match.group("task_id")
            if "expected_items" in body and not isinstance(body["expected_items"], list):
                return _finalize_idempotent_response(
                    service,
                    method=method,
                    path=request_path,
                    payload=body,
                    headers=request_headers,
                    response=_error_response(
                        HTTPStatus.BAD_REQUEST,
                        request_path,
                        "invalid_request",
                        "expected_items must be a list",
                    ),
                )
            try:
                expected_task_version = _parse_if_match_task_version(request_headers, task_id)
                task = service.upsert_task_state(
                    task_id,
                    title=_optional_string(body, "title"),
                    domain=_optional_string(body, "domain"),
                    goal=_optional_string(body, "goal"),
                    interruption_point=_optional_string(body, "interruption_point"),
                    expected_items=[_expected_item_from_payload(item) for item in body.get("expected_items", [])]
                    if "expected_items" in body
                    else None,
                    expected_task_version=expected_task_version,
                )
            except TaskVersionConflictError as exc:
                return _finalize_idempotent_response(
                    service,
                    method=method,
                    path=request_path,
                    payload=body,
                    headers=request_headers,
                    response=_error_response(HTTPStatus.PRECONDITION_FAILED, request_path, "precondition_failed", str(exc)),
                )
            except ValueError as exc:
                return _finalize_idempotent_response(
                    service,
                    method=method,
                    path=request_path,
                    payload=body,
                    headers=request_headers,
                    response=_error_response(HTTPStatus.BAD_REQUEST, request_path, "invalid_request", str(exc)),
                )
            except TaskStateCompatibilityError as exc:
                return _finalize_idempotent_response(
                    service,
                    method=method,
                    path=request_path,
                    payload=body,
                    headers=request_headers,
                    response=_error_response(HTTPStatus.CONFLICT, request_path, "incompatible_task_state", str(exc)),
                )
            return _finalize_idempotent_response(
                service,
                method=method,
                path=request_path,
                payload=body,
                headers=request_headers,
                response=_success_response(HTTPStatus.OK, request_path, {"task": to_dict(task)}),
            )

    if method == "GET":
        match = RESUME_PACKET_PATTERN.match(request_path)
        if match:
            task_id = match.group("task_id")
            try:
                packet = service.get_resume_packet(task_id)
            except TaskNotFoundError:
                return _error_response(HTTPStatus.NOT_FOUND, request_path, "task_not_found", f"task not found: {task_id}")
            except TaskStateCompatibilityError as exc:
                return _error_response(HTTPStatus.CONFLICT, request_path, "incompatible_task_state", str(exc))
            return _success_response(HTTPStatus.OK, request_path, to_dict(packet))

    if method == "POST":
        match = RETRIEVE_PATTERN.match(request_path)
        if match:
            task_id = match.group("task_id")
            try:
                view = service.retrieve_task_memory(task_id)
            except TaskNotFoundError:
                return _error_response(HTTPStatus.NOT_FOUND, request_path, "task_not_found", f"task not found: {task_id}")
            except TaskStateCompatibilityError as exc:
                return _error_response(HTTPStatus.CONFLICT, request_path, "incompatible_task_state", str(exc))
            return _success_response(HTTPStatus.OK, request_path, to_dict(view))

    return _error_response(HTTPStatus.NOT_FOUND, request_path, "not_found", f"unknown endpoint: {request_path}")


def _build_handler(service: LocalMemoryService) -> type[BaseHTTPRequestHandler]:
    class MemoryVaultHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            try:
                payload = self._read_json_body()
                status, response = handle_http_request(
                    service,
                    method="POST",
                    path=self.path,
                    payload=payload,
                    headers=dict(self.headers.items()),
                )
            except (InvalidJsonBodyError, ValueError) as exc:
                status, response = _error_response(
                    HTTPStatus.BAD_REQUEST,
                    urlparse(self.path).path,
                    "invalid_request",
                    str(exc),
                )
            self._send_json(status, response)

        def do_PUT(self) -> None:  # noqa: N802
            try:
                payload = self._read_json_body()
                status, response = handle_http_request(
                    service,
                    method="PUT",
                    path=self.path,
                    payload=payload,
                    headers=dict(self.headers.items()),
                )
            except (InvalidJsonBodyError, ValueError) as exc:
                status, response = _error_response(
                    HTTPStatus.BAD_REQUEST,
                    urlparse(self.path).path,
                    "invalid_request",
                    str(exc),
                )
            self._send_json(status, response)

        def do_GET(self) -> None:  # noqa: N802
            status, response = handle_http_request(
                service,
                method="GET",
                path=self.path,
                headers=dict(self.headers.items()),
            )
            self._send_json(status, response)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return None

        def _read_json_body(self) -> dict[str, Any]:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0:
                return {}
            raw_body = self.rfile.read(content_length)
            try:
                return json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise InvalidJsonBodyError("request body must be valid JSON") from exc

        def _send_json(self, status: HTTPStatus, payload: Any) -> None:
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return MemoryVaultHandler


def _validate_api_version(payload: dict[str, Any]) -> tuple[HTTPStatus, Any] | None:
    if "api_version" not in payload:
        return None
    if str(payload["api_version"]) != HTTP_API_VERSION:
        return _error_response(
            HTTPStatus.BAD_REQUEST,
            "",
            "unsupported_api_version",
            f"api_version must be {HTTP_API_VERSION}",
        )
    return None


def _success_response(status: HTTPStatus, endpoint: str, data: Any) -> tuple[HTTPStatus, Any]:
    return status, {
        "ok": True,
        "api_version": HTTP_API_VERSION,
        "endpoint": endpoint,
        "data": data,
    }


def _error_response(status: HTTPStatus, endpoint: str, code: str, message: str) -> tuple[HTTPStatus, Any]:
    return status, {
        "ok": False,
        "api_version": HTTP_API_VERSION,
        "endpoint": endpoint,
        "error": {
            "code": code,
            "message": message,
        },
    }


def _optional_string(payload: dict[str, Any], key: str) -> str | None:
    if key not in payload:
        return None
    return str(payload[key])


def _normalize_headers(headers: dict[str, str] | None) -> dict[str, str]:
    if headers is None:
        return {}
    return {str(key).lower(): str(value) for key, value in headers.items()}


def _handle_idempotency_preflight(
    service: LocalMemoryService,
    *,
    method: str,
    path: str,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> tuple[HTTPStatus, Any] | None:
    idempotency_key = _idempotency_key_for_write(method=method, path=path, headers=headers)
    if idempotency_key is None:
        return None

    fingerprint = service.build_idempotency_fingerprint(
        method=method,
        path=path,
        payload=payload,
        headers=headers,
    )
    try:
        existing = service.ensure_idempotency_match(idempotency_key, fingerprint)
    except IdempotencyConflictError as exc:
        return _error_response(HTTPStatus.CONFLICT, path, "idempotency_conflict", str(exc))
    except TaskStateCompatibilityError as exc:
        return _error_response(HTTPStatus.CONFLICT, path, "incompatible_task_state", str(exc))

    if existing is None:
        return None
    return HTTPStatus(existing.status_code), existing.response_payload


def _finalize_idempotent_response(
    service: LocalMemoryService,
    *,
    method: str,
    path: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    response: tuple[HTTPStatus, Any],
) -> tuple[HTTPStatus, Any]:
    idempotency_key = _idempotency_key_for_write(method=method, path=path, headers=headers)
    if idempotency_key is None:
        return response

    status, response_payload = response
    if not isinstance(response_payload, dict):
        return response

    fingerprint = service.build_idempotency_fingerprint(
        method=method,
        path=path,
        payload=payload,
        headers=headers,
    )
    service.save_idempotency_record(
        key=idempotency_key,
        request_fingerprint=fingerprint,
        status_code=int(status),
        response_payload=response_payload,
    )
    return response


def _idempotency_key_for_write(*, method: str, path: str, headers: dict[str, str]) -> str | None:
    is_write = (method == "POST" and path == "/v1/events") or (method == "PUT" and TASK_STATE_PATTERN.match(path))
    if not is_write:
        return None
    raw_key = headers.get("idempotency-key")
    if raw_key is None:
        return None
    key = raw_key.strip()
    if key == "":
        raise ValueError("Idempotency-Key must not be empty")
    return key


def _parse_if_match_task_version(headers: dict[str, str], task_id: str) -> int | None:
    if_match = headers.get("if-match")
    if if_match is None or if_match.strip() == "":
        return None

    value = if_match.strip()
    if value == "*":
        raise ValueError("If-Match wildcard is not supported for task writes")

    try:
        expected_task_version = int(value.strip('"'))
    except ValueError as exc:
        raise ValueError(
            f"If-Match must be the current task_version for {task_id}"
        ) from exc

    if expected_task_version < 1:
        raise ValueError("If-Match must be >= 1")
    return expected_task_version


def _task_event_from_payload(payload: dict[str, Any]) -> TaskEvent:
    if not isinstance(payload, dict):
        raise ValueError("each event must be an object")
    missing = [field_name for field_name in ("sequence", "actor", "text") if field_name not in payload]
    if missing:
        raise ValueError(f"each event must include: {', '.join(missing)}")
    source_refs = payload.get("source_refs", [])
    if not isinstance(source_refs, list):
        raise ValueError("event source_refs must be a list")
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("event metadata must be an object")
    return TaskEvent(
        sequence=int(payload["sequence"]),
        actor=str(payload["actor"]),
        text=str(payload["text"]),
        source_refs=[str(item) for item in source_refs],
        metadata=dict(metadata),
    )


def _expected_item_from_payload(payload: dict[str, Any]) -> ExpectedItem:
    if not isinstance(payload, dict):
        raise ValueError("each expected item must be an object")
    missing = [field_name for field_name in ("name", "category") if field_name not in payload]
    if missing:
        raise ValueError(f"each expected item must include: {', '.join(missing)}")
    keywords = payload.get("keywords", [])
    if not isinstance(keywords, list):
        raise ValueError("expected item keywords must be a list")
    return ExpectedItem(
        name=str(payload["name"]),
        category=str(payload["category"]),
        keywords=[str(item) for item in keywords],
    )
