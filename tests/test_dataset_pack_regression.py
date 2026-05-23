import json

from pathlib import Path

from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.traces.trace_store import TraceStore
from lean_hybrid_reasoner.training.dataset_pack import build_dataset_pack


def test_regression_dataset_pack_is_deterministic(tmp_path: Path):
    trace_path = tmp_path / "traces.jsonl"
    engine = ProofSearchEngine(MockLeanBackend(), trace_store=TraceStore(trace_path))
    engine.run("and_comm_example")

    out_a = tmp_path / "pack_a"
    out_b = tmp_path / "pack_b"
    build_dataset_pack(
        trace_path, out_a, include_failures=True, min_quality="any", dev_ratio=0.2
    )
    build_dataset_pack(
        trace_path, out_b, include_failures=True, min_quality="any", dev_ratio=0.2
    )

    assert (out_a / "train.jsonl").read_text(encoding="utf-8") == (
        out_b / "train.jsonl"
    ).read_text(encoding="utf-8")
    assert (out_a / "dev.jsonl").read_text(encoding="utf-8") == (
        out_b / "dev.jsonl"
    ).read_text(encoding="utf-8")


def test_regression_dataset_pack_manifest_has_quality_summary(tmp_path: Path):
    trace_path = tmp_path / "traces.jsonl"
    engine = ProofSearchEngine(MockLeanBackend(), trace_store=TraceStore(trace_path))
    engine.run("and_comm_example")

    output = tmp_path / "pack"
    build_dataset_pack(
        trace_path, output, include_failures=True, min_quality="accepted"
    )
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "0.6"
    assert manifest["quality_filter"]["min_quality"] == "accepted"
    assert manifest["examples_before_filter"] >= manifest["total_examples"]
