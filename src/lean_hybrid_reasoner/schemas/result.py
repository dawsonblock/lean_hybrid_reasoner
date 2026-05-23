from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field


class ProofRunResult(BaseModel):
    trace_schema_version: str = "0.6"
    run_id: str = Field(default_factory=lambda: f"run_{uuid4().hex}")
    theorem_name: str
    solved: bool
    status: str
    proof: list[str] = Field(default_factory=list)
    branches_explored: int = 0
    branches_pruned: int = 0
    tactics_attempted: int = 0
    accepted_tactics: int = 0
    failed_tactics: int = 0
    repair_attempts: int = 0
    repair_successes: int = 0
    trace: list[dict] = Field(default_factory=list)
    error: str | None = None


class SearchMetrics(BaseModel):
    proof_completion_rate: float
    tactic_accept_rate: float
    branch_efficiency: float
    timeout_rate: float
    repair_success_rate: float = 0.0
    premise_hit_rate: float = 0.0
    budget_failure_rate: float = 0.0
    median_steps_to_qed: float = 0.0
    score: float
