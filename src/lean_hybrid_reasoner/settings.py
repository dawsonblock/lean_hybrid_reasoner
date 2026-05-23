from __future__ import annotations

import os
from pathlib import Path
from pydantic import BaseModel, Field


class Settings(BaseModel):
    backend: str = Field(default_factory=lambda: os.getenv("LHR_BACKEND", "mock"))
    leandojo_repo: str | None = Field(
        default_factory=lambda: os.getenv("LHR_LEANDOJO_REPO") or None
    )
    leandojo_commit: str | None = Field(
        default_factory=lambda: os.getenv("LHR_LEANDOJO_COMMIT") or None
    )
    leandojo_theorem_filter: str | None = Field(
        default_factory=lambda: os.getenv("LHR_LEANDOJO_THEOREM_FILTER") or None
    )
    leandojo_import_module: str | None = Field(
        default_factory=lambda: os.getenv("LHR_LEANDOJO_IMPORT_MODULE") or None
    )
    lean_project_root: Path = Field(
        default_factory=lambda: Path(
            os.getenv("LHR_LEAN_PROJECT_ROOT", "lean_projects/starter")
        )
    )
    lean_file: Path = Field(
        default_factory=lambda: Path(os.getenv("LHR_LEAN_FILE", "HybridStarter.lean"))
    )
    lean_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("LHR_LEAN_TIMEOUT", "20"))
    )
    keep_lean_temp: bool = Field(
        default_factory=lambda: os.getenv("LHR_KEEP_LEAN_TEMP", "0").lower()
        in {"1", "true", "yes", "on"}
    )
    lean_temp_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("LHR_LEAN_TEMP_DIR", ".runs/lean_temp"))
    )

    proposer: str = Field(
        default_factory=lambda: os.getenv("LHR_PROPOSER", "heuristic")
    )
    repairer: str = Field(
        default_factory=lambda: os.getenv("LHR_REPAIRER", "heuristic")
    )
    dspy_proposer_path: Path | None = Field(
        default_factory=lambda: (
            Path(os.getenv("LHR_DSPY_PROPOSER_PATH"))
            if os.getenv("LHR_DSPY_PROPOSER_PATH")
            else None
        )
    )
    dspy_repairer_path: Path | None = Field(
        default_factory=lambda: (
            Path(os.getenv("LHR_DSPY_REPAIRER_PATH"))
            if os.getenv("LHR_DSPY_REPAIRER_PATH")
            else None
        )
    )
    dspy_fallback: str = Field(
        default_factory=lambda: os.getenv("LHR_DSPY_FALLBACK", "heuristic")
    )

    max_depth: int = Field(
        default_factory=lambda: int(os.getenv("LHR_MAX_DEPTH", "16"))
    )
    max_branches: int = Field(
        default_factory=lambda: int(os.getenv("LHR_MAX_BRANCHES", "64"))
    )
    max_tactics_per_state: int = Field(
        default_factory=lambda: int(os.getenv("LHR_MAX_TACTICS", "8"))
    )
    max_repair_attempts: int = Field(
        default_factory=lambda: int(os.getenv("LHR_MAX_REPAIR_ATTEMPTS", "2"))
    )
    max_total_tactics: int = Field(
        default_factory=lambda: int(os.getenv("LHR_MAX_TOTAL_TACTICS", "512"))
    )
    max_seconds_per_theorem: float = Field(
        default_factory=lambda: float(os.getenv("LHR_MAX_SECONDS", "20"))
    )
    max_stagnant_steps: int = Field(
        default_factory=lambda: int(os.getenv("LHR_MAX_STAGNANT_STEPS", "3"))
    )

    trace_path: Path = Field(
        default_factory=lambda: Path(os.getenv("LHR_TRACE_PATH", ".runs/traces.jsonl"))
    )
    retrieval_top_k: int = Field(
        default_factory=lambda: int(os.getenv("LHR_RETRIEVAL_TOP_K", "8"))
    )
    retrieval_mode: str = Field(
        default_factory=lambda: os.getenv("LHR_RETRIEVAL_MODE", "bm25")
    )
    embedding_model: str = Field(
        default_factory=lambda: os.getenv(
            "LHR_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
    )


def load_settings() -> Settings:
    return Settings()
