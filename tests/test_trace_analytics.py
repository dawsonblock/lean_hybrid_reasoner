from pathlib import Path

from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.traces.trace_store import TraceStore
from lean_hybrid_reasoner.traces.dashboard import load_trace_records
from lean_hybrid_reasoner.traces.analytics import analyze_records


def test_trace_analytics_reports_tactics(tmp_path: Path):
    trace_path = tmp_path / "traces.jsonl"
    engine = ProofSearchEngine(MockLeanBackend(), trace_store=TraceStore(trace_path))
    engine.run("and_comm_example")
    records = load_trace_records(trace_path)
    payload = analyze_records(records)
    assert payload["runs"] == 1
    assert payload["solved"] == 1
    assert payload["top_tactics"]
