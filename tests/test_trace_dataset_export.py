from pathlib import Path

from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.traces.trace_store import TraceStore
from lean_hybrid_reasoner.traces.dashboard import load_trace_records
from lean_hybrid_reasoner.training.trace_dataset import extract_training_examples, summarize_training_examples, write_training_jsonl


def test_trace_dataset_extracts_successful_tactics(tmp_path: Path):
    trace_path = tmp_path / "traces.jsonl"
    engine = ProofSearchEngine(MockLeanBackend(), trace_store=TraceStore(trace_path))
    engine.run("and_comm_example")

    examples = extract_training_examples(load_trace_records(trace_path))
    assert any(e["task"] == "suggest_tactic" and e["accepted"] for e in examples)
    assert any(e["tactic"] == "intro h" for e in examples)
    summary = summarize_training_examples(examples)
    assert summary["examples"] >= 2
    assert summary["accept_rate"] > 0


def test_trace_dataset_writes_jsonl(tmp_path: Path):
    trace_path = tmp_path / "traces.jsonl"
    out = tmp_path / "examples.jsonl"
    engine = ProofSearchEngine(MockLeanBackend(), trace_store=TraceStore(trace_path))
    engine.run("add_zero_example")

    generated = write_training_jsonl(trace_path, out)
    assert generated == out
    assert out.exists()
    assert "suggest_tactic" in out.read_text(encoding="utf-8")
