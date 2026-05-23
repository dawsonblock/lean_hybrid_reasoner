from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

TRACE_SCHEMA_VERSION = "0.6"


class TraceEventV06(BaseModel):
    model_config = ConfigDict(extra="allow")

    trace_schema_version: str = TRACE_SCHEMA_VERSION
    run_id: str
    event_type: str
    theorem: str
    timestamp: str | None = None
    branch_id: str | None = None
    state_key: str | None = None
    tactic: str | None = None
    accepted: bool | None = None
    solved: bool | None = None
    error: str | None = None
    failure_category: str | None = None
    backend: str | None = None
    config_snapshot_id: str | None = None
    raw_event: dict[str, Any] = Field(default_factory=dict)


class TraceRunRecordV06(BaseModel):
    model_config = ConfigDict(extra="allow")

    trace_schema_version: str = TRACE_SCHEMA_VERSION
    run_id: str
    theorem_name: str
    solved: bool
    status: str
    trace: list[dict[str, Any]] = Field(default_factory=list)


def _normalize_event_type(event: dict[str, Any]) -> str:
    if event.get("event_type"):
        return str(event["event_type"])
    if event.get("event"):
        return str(event["event"])
    return "unknown"


def canonicalize_trace_event(
    *,
    event: dict[str, Any],
    theorem_name: str,
    run_id: str,
    backend: str | None,
    config_snapshot_id: str | None,
) -> dict[str, Any]:
    event_type = _normalize_event_type(event)
    metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
    normalized_tactic = event.get("tactic")
    if normalized_tactic is None and event_type == "repair_tactic":
        normalized_tactic = event.get("repair_tactic")

    payload: dict[str, Any] = {
        **event,
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "run_id": run_id,
        # Keep legacy `event` for compatibility with analytics/failure classifier.
        "event": event_type,
        "event_type": event_type,
        "theorem": event.get("theorem") or theorem_name,
        "timestamp": event.get("timestamp"),
        "branch_id": event.get("branch_id"),
        "state_key": event.get("state_key"),
        "tactic": normalized_tactic,
        "accepted": event.get("accepted"),
        "solved": event.get("solved"),
        "error": event.get("error"),
        "failure_category": event.get("failure_category"),
        "backend": event.get("backend") or metadata.get("backend") or backend,
        "config_snapshot_id": event.get("config_snapshot_id") or config_snapshot_id,
        "raw_event": event,
    }
    return TraceEventV06.model_validate(payload).model_dump(mode="json")


def canonicalize_trace_events(
    *,
    trace: list[dict[str, Any]],
    theorem_name: str,
    run_id: str,
    backend: str | None = None,
    config_snapshot_id: str | None = None,
) -> list[dict[str, Any]]:
    return [
        canonicalize_trace_event(
            event=event,
            theorem_name=theorem_name,
            run_id=run_id,
            backend=backend,
            config_snapshot_id=config_snapshot_id,
        )
        for event in trace
    ]
