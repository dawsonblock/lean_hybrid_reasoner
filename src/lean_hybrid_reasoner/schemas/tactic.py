from __future__ import annotations

from pydantic import BaseModel, Field


class TacticCandidate(BaseModel):
    tactic: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    rationale: str = ""
    expected_effect: str = ""
    required_premises: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class LeanExecutionResult(BaseModel):
    accepted: bool
    solved: bool
    tactic: str
    error_message: str | None = None
    new_goals: list[str] = Field(default_factory=list)
    proof_state_text: str | None = None
    new_hypotheses: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
