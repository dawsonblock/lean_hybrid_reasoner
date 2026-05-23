from __future__ import annotations

from typing import Protocol
from lean_hybrid_reasoner.schemas.proof_state import LeanProofState
from lean_hybrid_reasoner.schemas.tactic import LeanExecutionResult


class LeanBackend(Protocol):
    def list_theorems(self) -> list[str]: ...

    def initial_state(self, theorem_name: str) -> LeanProofState: ...

    def load_theorem(self, theorem_name: str) -> LeanProofState: ...

    def execute_tactic(
        self, state: LeanProofState, tactic: str
    ) -> LeanExecutionResult: ...
