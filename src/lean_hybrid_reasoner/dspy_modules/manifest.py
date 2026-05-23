from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from lean_hybrid_reasoner.cli_errors import InvalidCompiledProgramError


class CompiledProgramManifest(BaseModel):
    artifact_type: Literal["proposer", "repairer", "ranker"]
    created_at: str
    package_version: str
    dspy_version: str | None = None
    model: str | None = None
    optimizer: str
    train_dataset: str
    dev_dataset: str | None = None
    train_examples: int
    dev_examples: int
    metric_name: str
    scores: dict[str, float]
    config_snapshot: dict[str, Any]


def validate_compiled_program_dir(path: Path) -> CompiledProgramManifest:
    manifest_path = path / "manifest.json"
    if not manifest_path.exists():
        raise InvalidCompiledProgramError(f"Missing compiled manifest: {manifest_path}")

    manifest = CompiledProgramManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )

    metrics_path = path / "metrics.json"
    if not metrics_path.exists():
        raise InvalidCompiledProgramError(f"Missing compiled metrics: {metrics_path}")

    program_json = path / "program.json"
    dspy_program_dir = path / "dspy_program"
    if not program_json.exists() and not dspy_program_dir.exists():
        raise InvalidCompiledProgramError(
            f"Missing compiled program payload in {path} (expected program.json or dspy_program/)"
        )

    return manifest


def write_compiled_artifact(
    *,
    output_dir: Path,
    manifest: CompiledProgramManifest,
    metrics: dict[str, Any],
    program_payload: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "program.json").write_text(
        json.dumps(program_payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
