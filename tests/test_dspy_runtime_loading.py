from __future__ import annotations

from pathlib import Path

import pytest

from lean_hybrid_reasoner.cli_errors import InvalidCompiledProgramError
from lean_hybrid_reasoner.dspy_modules.manifest import CompiledProgramManifest, write_compiled_artifact
from lean_hybrid_reasoner.dspy_modules.dspy_tactics import DSPyTacticProposer


def test_from_compiled_dir_without_dspy_program_raises_invalid_payload(tmp_path: Path):
    manifest = CompiledProgramManifest(
        artifact_type="proposer",
        created_at="2026-01-01T00:00:00Z",
        package_version="0.8.0",
        optimizer="bootstrap",
        train_dataset="train.jsonl",
        dev_dataset="dev.jsonl",
        train_examples=1,
        dev_examples=1,
        metric_name="sanitized",
        scores={"score": 0.5},
        config_snapshot={},
    )
    write_compiled_artifact(
        output_dir=tmp_path,
        manifest=manifest,
        metrics={"score": 0.5},
        program_payload={"placeholder": True},
    )

    with pytest.raises((InvalidCompiledProgramError, RuntimeError)):
        DSPyTacticProposer.from_compiled(tmp_path)
