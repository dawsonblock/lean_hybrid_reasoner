import json

from pathlib import Path

from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.traces.trace_store import TraceStore
from lean_hybrid_reasoner.traces.validate import validate_trace_file


def test_validate_traces_accepts_v06_engine_output(tmp_path: Path):
    trace_path = tmp_path / "traces.jsonl"
    engine = ProofSearchEngine(MockLeanBackend(), trace_store=TraceStore(trace_path))
    engine.run("and_comm_example")

    payload = validate_trace_file(trace_path, strict=True)
    assert payload["ok"] is True
    assert payload["records_valid"] == 1
    assert payload["legacy_records"] == 0


def test_validate_traces_detects_legacy_records(tmp_path: Path):
    trace_path = tmp_path / "legacy.jsonl"
    record = {
        "theorem_name": "demo",
        "solved": True,
        "status": "solved",
        "trace": [{"event": "start", "theorem": "demo"}],
    }
    trace_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    payload = validate_trace_file(trace_path, strict=False)
    assert payload["ok"] is True
    assert payload["legacy_records"] == 1
    assert payload["records_valid"] == 1
