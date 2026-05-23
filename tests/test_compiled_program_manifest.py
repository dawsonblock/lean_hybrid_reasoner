from __future__ import annotations

from pathlib import Path

import pytest

from lean_hybrid_reasoner.cli_errors import InvalidCompiledProgramError
from lean_hybrid_reasoner.dspy_modules.manifest import (
    CompiledProgramManifest,
    validate_compiled_program_dir,
    write_compiled_artifact,
)


def test_validate_compiled_program_dir_success(tmp_path: Path):
    manifest = CompiledProgramManifest(
        artifact_type="proposer",
        created_at="2026-01-01T00:00:00Z",
        package_version="0.8.0",
        optimizer="bootstrap",
        train_dataset="train.jsonl",
        dev_dataset="dev.jsonl",
        train_examples=10,
        dev_examples=2,
        metric_name="sanitized",
        scores={"score": 0.5},
        config_snapshot={"seed": 1},
    )
    write_compiled_artifact(
        output_dir=tmp_path,
        manifest=manifest,
        metrics={"score": 0.5},
        program_payload={"kind": "placeholder"},
    )

    loaded = validate_compiled_program_dir(tmp_path)
    assert loaded.artifact_type == "proposer"


def test_validate_compiled_program_dir_missing_manifest(tmp_path: Path):
    with pytest.raises(InvalidCompiledProgramError):
        validate_compiled_program_dir(tmp_path)
