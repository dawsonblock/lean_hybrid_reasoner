from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from lean_hybrid_reasoner.traces.schema import (
    TRACE_SCHEMA_VERSION,
    TraceEventV06,
    TraceRunRecordV06,
)


def _validate_event(
    event: dict[str, Any], line_no: int, event_index: int, strict: bool
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    try:
        TraceEventV06.model_validate(event)
    except ValidationError as exc:
        errors.append(
            {
                "line": line_no,
                "event_index": event_index,
                "message": f"invalid trace event: {exc.errors()}",
            }
        )
        return errors

    if strict and event.get("trace_schema_version") != TRACE_SCHEMA_VERSION:
        errors.append(
            {
                "line": line_no,
                "event_index": event_index,
                "message": f"event trace_schema_version must be {TRACE_SCHEMA_VERSION}",
            }
        )
    return errors


def validate_trace_record(
    record: dict[str, Any], line_no: int, strict: bool = False
) -> tuple[bool, bool, list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    legacy_detected = record.get("trace_schema_version") != TRACE_SCHEMA_VERSION

    try:
        TraceRunRecordV06.model_validate(record)
    except ValidationError as exc:
        if strict:
            errors.append(
                {"line": line_no, "message": f"invalid run record: {exc.errors()}"}
            )
            return False, legacy_detected, errors

        # Legacy compatibility path (v0.1-v0.5): validate minimal run shape.
        trace = record.get("trace")
        if not isinstance(trace, list):
            return (
                False,
                legacy_detected,
                [{"line": line_no, "message": "legacy record must contain trace list"}],
            )
        if "theorem_name" not in record and "theorem" not in record:
            return (
                False,
                legacy_detected,
                [
                    {
                        "line": line_no,
                        "message": "legacy record missing theorem_name/theorem",
                    }
                ],
            )
        if "status" not in record and "solved" not in record:
            return (
                False,
                legacy_detected,
                [{"line": line_no, "message": "legacy record missing status/solved"}],
            )

    trace = record.get("trace")
    if not isinstance(trace, list):
        return (
            False,
            legacy_detected,
            [{"line": line_no, "message": "trace must be a list"}],
        )

    for idx, event in enumerate(trace):
        if not isinstance(event, dict):
            errors.append(
                {
                    "line": line_no,
                    "event_index": idx,
                    "message": "trace event must be an object",
                }
            )
            continue
        if not strict and "event" in event and "event_type" not in event:
            # v0.5 compatibility path
            continue
        errors.extend(
            _validate_event(event, line_no=line_no, event_index=idx, strict=strict)
        )

    if strict and record.get("trace_schema_version") != TRACE_SCHEMA_VERSION:
        errors.append(
            {
                "line": line_no,
                "message": f"trace_schema_version must be {TRACE_SCHEMA_VERSION}",
            }
        )

    return len(errors) == 0, legacy_detected, errors


def validate_trace_file(
    input_path: str | Path, *, strict: bool = False
) -> dict[str, Any]:
    path = Path(input_path)
    if not path.exists():
        return {
            "ok": False,
            "input": str(path),
            "trace_schema_version": TRACE_SCHEMA_VERSION,
            "strict": strict,
            "records_total": 0,
            "records_valid": 0,
            "records_invalid": 1,
            "legacy_records": 0,
            "errors": [{"line": 0, "message": f"trace file not found: {path}"}],
        }

    total = 0
    valid = 0
    invalid = 0
    legacy = 0
    errors: list[dict[str, Any]] = []

    for line_no, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        total += 1
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            invalid += 1
            errors.append({"line": line_no, "message": f"invalid JSON: {exc}"})
            continue

        is_valid, legacy_detected, line_errors = validate_trace_record(
            record, line_no=line_no, strict=strict
        )
        if legacy_detected:
            legacy += 1
        if is_valid:
            valid += 1
        else:
            invalid += 1
            errors.extend(line_errors)

    payload = {
        "ok": invalid == 0,
        "input": str(path),
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "strict": strict,
        "records_total": total,
        "records_valid": valid,
        "records_invalid": invalid,
        "legacy_records": legacy,
        "errors": errors,
    }
    if legacy and not strict:
        payload["note"] = (
            "Legacy traces detected. Run migrate-traces to normalize to v0.6."
        )
    return payload
