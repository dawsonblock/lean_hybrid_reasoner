from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ProofBranch(BaseModel):
    branch_id: str
    theorem_name: str
    proof_prefix: list[str] = Field(default_factory=list)
    current_goal: str
    hypotheses: list[str] = Field(default_factory=list)
    open_goals: list[str] = Field(default_factory=list)
    score: float = 0.0
    depth: int = 0
    failures: list[str] = Field(default_factory=list)
    stagnant_steps: int = 0
    status: Literal["active", "solved", "dead", "timeout"] = "active"
    parent_branch_id: str | None = None
