from __future__ import annotations

from typing import TypedDict, Any


class ProofGraphState(TypedDict, total=False):
    theorem_name: str
    current_goal: str
    proof_prefix: list[str]
    branch_id: str
    retrieved_premises: list[str]
    tactic_candidates: list[dict]
    execution_result: dict
    trace: list[dict[str, Any]]
