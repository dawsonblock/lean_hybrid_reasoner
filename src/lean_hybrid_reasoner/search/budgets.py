from __future__ import annotations

import time
from pydantic import BaseModel, Field


class SearchBudget(BaseModel):
    max_depth: int = 16
    max_branches: int = 64
    max_tactics_per_state: int = 8
    max_repair_attempts: int = 2
    max_total_tactics: int = 512
    max_seconds: float = 20.0
    max_stagnant_steps: int = 3
    enable_tactic_memory: bool = True
    tactic_memory_failure_threshold: int = 2
    started_at: float = Field(default_factory=time.monotonic)

    def timed_out(self) -> bool:
        return (time.monotonic() - self.started_at) >= self.max_seconds

    def depth_exceeded(self, depth: int) -> bool:
        return depth > self.max_depth

    def branches_exceeded(self, explored: int) -> bool:
        return explored >= self.max_branches

    def tactics_exceeded(self, attempted: int) -> bool:
        return attempted >= self.max_total_tactics

    def stagnant_exceeded(self, stagnant_steps: int) -> bool:
        return stagnant_steps > self.max_stagnant_steps


def named_budget(profile: str) -> SearchBudget:
    profile = profile.lower().strip()
    if profile == "tiny":
        return SearchBudget(
            max_depth=4, max_branches=8, max_total_tactics=32, max_seconds=5.0
        )
    if profile == "starter":
        return SearchBudget(
            max_depth=16, max_branches=64, max_total_tactics=512, max_seconds=20.0
        )
    if profile == "wide":
        return SearchBudget(
            max_depth=16, max_branches=256, max_total_tactics=2048, max_seconds=60.0
        )
    if profile == "deep":
        return SearchBudget(
            max_depth=48, max_branches=128, max_total_tactics=2048, max_seconds=60.0
        )
    if profile == "aggressive":
        return SearchBudget(
            max_depth=64, max_branches=512, max_total_tactics=8192, max_seconds=180.0
        )
    raise ValueError(f"Unknown budget profile: {profile}")
