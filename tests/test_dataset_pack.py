from pathlib import Path

from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.traces.trace_store import TraceStore
from lean_hybrid_reasoner.training.dataset_pack import build_dataset_pack


def test_build_dataset_pack_writes_manifest_and_splits(tmp_path: Path):
    trace_path = tmp_path / "traces.jsonl"
    engine = ProofSearchEngine(MockLeanBackend(), trace_store=TraceStore(trace_path))
    engine.run("and_comm_example")

    output_dir = tmp_path / "pack"
    manifest = build_dataset_pack(trace_path, output_dir, dev_ratio=0.5)
    assert manifest["total_examples"] >= 2
    assert manifest["schema_version"] == "0.6"
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "train.jsonl").exists()
    assert (output_dir / "dev.jsonl").exists()


def test_build_dataset_pack_min_quality_filters_rejected_examples(tmp_path: Path):
    trace_path = tmp_path / "traces.jsonl"
    engine = ProofSearchEngine(MockLeanBackend(), trace_store=TraceStore(trace_path))
    engine.run("and_comm_example")

    output_dir = tmp_path / "pack_quality"
    manifest = build_dataset_pack(
        trace_path,
        output_dir,
        include_failures=True,
        min_quality="accepted",
    )
    assert manifest["quality_filter"]["min_quality"] == "accepted"
    assert manifest["examples_before_filter"] >= manifest["total_examples"]
    assert manifest["quality_filter"]["dropped"] >= 0
