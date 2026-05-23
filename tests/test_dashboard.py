from pathlib import Path

from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.traces.trace_store import TraceStore
from lean_hybrid_reasoner.traces.dashboard import summarize_trace_file, render_html_dashboard


def test_dashboard_outputs_html(tmp_path: Path):
    trace_path = tmp_path / "traces.jsonl"
    engine = ProofSearchEngine(MockLeanBackend(), trace_store=TraceStore(trace_path))
    engine.run("add_zero_example")

    summary = summarize_trace_file(trace_path)
    assert summary["runs"] == 1
    assert summary["solved"] == 1

    html_path = render_html_dashboard(trace_path, tmp_path / "dashboard.html")
    assert html_path.exists()
    assert "add_zero_example" in html_path.read_text(encoding="utf-8")
