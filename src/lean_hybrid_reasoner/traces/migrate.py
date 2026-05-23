from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lean_hybrid_reasoner.traces.schema import (
    TRACE_SCHEMA_VERSION,
    TraceRunRecordV06,
    canonicalize_trace_events,
)


def migrate_trace_record(record: dict[str, Any], run_index: int = 0) -> dict[str, Any]:
    theorem_name = str(
        record.get("theorem_name") or record.get("theorem") or "unknown_theorem"
    )
    run_id = str(record.get("run_id") or f"run_{run_index:06d}")
    trace = record.get("trace")
    if not isinstance(trace, list):
        trace = []

    migrated = {
        **record,
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "run_id": run_id,
        "theorem_name": theorem_name,
        "trace": canonicalize_trace_events(
            trace=trace,
            theorem_name=theorem_name,
            run_id=run_id,
            backend=record.get("backend"),
            config_snapshot_id=record.get("config_snapshot_id"),
        ),
    }
    if "status" not in migrated:
        migrated["status"] = "solved" if bool(migrated.get("solved")) else "failed"
    if "solved" not in migrated:
        migrated["solved"] = migrated.get("status") == "solved"

    # Validate migrated shape while allowing extra keys.
    return TraceRunRecordV06.model_validate(migrated).model_dump(mode="json")


def migrate_trace_file(
    input_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    in_path = Path(input_path)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    migrated_count = 0
    invalid_count = 0
    errors: list[dict[str, Any]] = []

    with in_path.open("r", encoding="utf-8") as src, out_path.open(
        "w", encoding="utf-8"
    ) as dst:
        for line_no, line in enumerate(src, start=1):
            if not line.strip():
                continue
            total += 1
            try:
                record = json.loads(line)
                migrated = migrate_trace_record(record, run_index=line_no)
                dst.write(json.dumps(migrated, ensure_ascii=False) + "\n")
                migrated_count += 1
            except Exception as exc:
                invalid_count += 1
                errors.append({"line": line_no, "error": str(exc)})

    return {
        "ok": invalid_count == 0,
        "input": str(in_path),
        "output": str(out_path),
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "records_total": total,
        "records_migrated": migrated_count,
        "records_invalid": invalid_count,
        "errors": errors,
    }
