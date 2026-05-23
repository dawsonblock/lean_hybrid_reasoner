from __future__ import annotations

import json
from pathlib import Path

from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.traces.trace_store import TraceStore
from lean_hybrid_reasoner.training.dataset_pack import build_dataset_pack


def test_pack_dataset_target_proposer_and_repairer(tmp_path: Path):
    trace_path = tmp_path / "traces.jsonl"
    engine = ProofSearchEngine(MockLeanBackend(), trace_store=TraceStore(trace_path))
    engine.run("and_comm_example")

    proposer_pack = tmp_path / "proposer"
    repair_pack = tmp_path / "repair"
    m1 = build_dataset_pack(trace_path, proposer_pack, target="proposer")
    m2 = build_dataset_pack(
        trace_path,
        repair_pack,
        target="repairer",
        include_failures=True,
        include_repairs=True,
    )

    assert m1["target"] == "proposer"
    assert m2["target"] == "repairer"


def test_pack_dataset_with_sanitizer_metadata(tmp_path: Path):
    trace_path = tmp_path / "traces.jsonl"
    engine = ProofSearchEngine(MockLeanBackend(), trace_store=TraceStore(trace_path))
    engine.run("and_comm_example")

    output = tmp_path / "pack"
    build_dataset_pack(
        trace_path,
        output,
        include_sanitizer_metadata=True,
        exclude_invalid_tactics=False,
    )

    first = (output / "train.jsonl").read_text(encoding="utf-8").splitlines()[0]
    row = json.loads(first)
    assert "sanitizer" in row
