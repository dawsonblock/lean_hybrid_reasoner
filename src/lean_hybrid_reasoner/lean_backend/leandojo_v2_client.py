from __future__ import annotations

from pathlib import Path

from lean_hybrid_reasoner.schemas.proof_state import LeanProofState
from lean_hybrid_reasoner.schemas.tactic import LeanExecutionResult


class IntegrationUnavailable(RuntimeError):
    """Raised when LeanDojo-v2 runtime is not configured in this environment."""


class LeanDojoV2Client:
    """Adapter seam for LeanDojo-v2 backend integration.

    This class preserves the current backend contract used by `ProofSearchEngine`
    while deferring environment-specific LeanDojo-v2 setup to a later phase.

    Planned responsibilities in full integration mode:
    - load traced Lean repositories/theorems
    - build initial proof states from structured theorem data
    - execute tactics against a stateful LeanDojo/Pantograph session
    """

    def __init__(
        self,
        *,
        project_root: str | Path | None = None,
        traced_data_dir: str | Path | None = None,
        repository: str | None = None,
    ):
        self.project_root = Path(project_root).resolve() if project_root else None
        self.traced_data_dir = (
            Path(traced_data_dir).resolve() if traced_data_dir else None
        )
        self.repository = repository

        # Keep this as an explicit seam until LeanDojo-v2 dependency wiring and
        # runtime selection are introduced.
        raise IntegrationUnavailable(
            "LeanDojoV2Client is a staged adapter seam and is not runtime-wired yet. "
            "Use backend='mock' or backend='lean_cli' for now. "
            "See docs/integrations/lean_dojo_ecosystem.md for rollout order."
        )

    def list_theorems(self) -> list[str]:
        raise IntegrationUnavailable("LeanDojo-v2 adapter is not active in this phase.")

    def load_theorem(self, theorem_name: str) -> LeanProofState:
        raise IntegrationUnavailable("LeanDojo-v2 adapter is not active in this phase.")

    def execute_tactic(self, state: LeanProofState, tactic: str) -> LeanExecutionResult:
        raise IntegrationUnavailable("LeanDojo-v2 adapter is not active in this phase.")
