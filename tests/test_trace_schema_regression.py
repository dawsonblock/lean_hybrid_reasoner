import json

from pathlib import Path

from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.traces.dashboard import load_trace_records
from lean_hybrid_reasoner.traces.migrate import migrate_trace_file
from lean_hybrid_reasoner.traces.trace_store import TraceStore
from lean_hybrid_reasoner.traces.validate import validate_trace_file


def test_regression_trace_output_is_v06_compatible(tmp_path: Path):
    trace_path = tmp_path / "traces.jsonl"
    engine = ProofSearchEngine(MockLeanBackend(), trace_store=TraceStore(trace_path))
    engine.run("add_zero_example")
    records = load_trace_records(trace_path)
    assert records[0]["trace_schema_version"] == "0.6"
    assert records[0]["run_id"].startswith("run_")
    assert all("event_type" in ev for ev in records[0]["trace"])


def test_regression_legacy_trace_migration_then_strict_validate(tmp_path: Path):
    legacy_path = tmp_path / "legacy.jsonl"
    migrated_path = tmp_path / "migrated.jsonl"
    legacy_record = {
        "theorem_name": "legacy_demo",
        "solved": True,
        "status": "solved",
        "trace": [{"event": "start", "theorem": "legacy_demo"}],
    }
    legacy_path.write_text(json.dumps(legacy_record) + "\n", encoding="utf-8")

    payload = migrate_trace_file(legacy_path, migrated_path)
    assert payload["ok"] is True
    strict_payload = validate_trace_file(migrated_path, strict=True)
    assert strict_payload["ok"] is True
