from __future__ import annotations

from lean_hybrid_reasoner.schemas.proof_state import LeanProofState
from lean_hybrid_reasoner.schemas.tactic import LeanExecutionResult


class IntegrationUnavailable(RuntimeError):
    pass


class LeanDojoClient:
    """Adapter seam for LeanDojo-v2 / LeanCopilot.

    Keep this class as the stable interface for the future high-fidelity backend.
    The upgraded zip also includes `LeanCliBackend`, which can call a local Lean
    executable for small files. LeanDojo-v2 should replace this class when its
    local environment is installed because it can expose exact proof states,
    repository tracing, and premise metadata more reliably than subprocess text
    parsing.
    """

    def __init__(self, project_root: str | None = None):
        self.project_root = project_root
        raise IntegrationUnavailable(
            "LeanDojoClient is intentionally not bundled because LeanDojo-v2 setup is environment-specific. "
            "Use backend='mock' for deterministic tests or backend='lean_cli' for local Lean subprocess checks."
        )

    def list_theorems(self) -> list[str]:
        raise IntegrationUnavailable("Not implemented")

    def load_theorem(self, theorem_name: str) -> LeanProofState:
        raise IntegrationUnavailable("Not implemented")

    def execute_tactic(self, state: LeanProofState, tactic: str) -> LeanExecutionResult:
        raise IntegrationUnavailable("Not implemented")
