from __future__ import annotations

import importlib.util

from lean_hybrid_reasoner.schemas.proof_state import LeanProofState
from lean_hybrid_reasoner.schemas.tactic import LeanExecutionResult


class LeanDojoV2Unavailable(RuntimeError):
    """Raised when LeanDojo-v2 runtime is not configured or installed."""


class LeanDojoV2Client:
    """Adapter seam for LeanDojo-v2 backend integration.

    This class preserves the current backend contract used by `ProofSearchEngine`
    while deferring environment-specific LeanDojo-v2 setup to a later phase.

    Planned responsibilities in full integration mode:
    - load traced Lean repositories/theorems
    - build initial proof states from structured theorem data
    - execute tactics against a stateful LeanDojo/Pantograph session
    """

    # Keep the adapter explicitly fail-fast until real LeanDojo-v2 calls are wired.
    _RUNTIME_WIRED = False

    def __init__(
        self,
        repo: str | None = None,
        commit: str | None = None,
        theorem_filter: str | None = None,
    ):
        self.repo = repo
        self.commit = commit
        self.theorem_filter = theorem_filter
        self._dependency_available = self._detect_dependency_available()

    @staticmethod
    def _detect_dependency_available() -> bool:
        # LeanDojo-v2 package/module names can vary by environment;
        # require a LeanDojo namespace to avoid false positives from unrelated deps.
        candidates = ["lean_dojo", "leandojo"]
        return any(importlib.util.find_spec(name) is not None for name in candidates)

    def _configured(self) -> bool:
        return bool(self.repo)

    def dependency_status(self) -> dict[str, object]:
        if not self._dependency_available:
            return {
                "available": False,
                "reason": "dependency not installed",
                "action": "install/configure LeanDojo-v2 separately and set LHR_BACKEND=leandojo_v2",
            }
        if not self._configured():
            return {
                "available": False,
                "reason": "adapter not configured (LHR_LEANDOJO_REPO missing)",
                "action": "set LHR_LEANDOJO_REPO and optional LHR_LEANDOJO_COMMIT/LHR_LEANDOJO_THEOREM_FILTER",
            }
        if not self._RUNTIME_WIRED:
            return {
                "available": False,
                "reason": "adapter wiring not implemented yet",
                "action": "wire LeanDojo-v2 API calls in leandojo_v2_client before enabling this backend",
            }
        return {
            "available": True,
            "reason": "dependency detected and adapter configured",
            "action": "backend ready",
        }

    def _ensure_available(self) -> None:
        status = self.dependency_status()
        if bool(status.get("available")):
            return
        raise LeanDojoV2Unavailable(
            f"LeanDojo-v2 backend unavailable: {status['reason']}. {status['action']}"
        )

    def list_theorems(self) -> list[str]:
        self._ensure_available()
        # Placeholder: wire traced theorem index loading here once runtime is wired.
        return []

    def load_theorem(self, theorem_name: str) -> LeanProofState:
        self._ensure_available()
        # Placeholder: replace with traced theorem/proof-state extraction.
        return LeanProofState(
            theorem_name=theorem_name,
            theorem_statement=f"theorem {theorem_name} : True := by",
            current_goal="True",
            hypotheses=[],
            open_goals=["True"],
            proof_prefix=[],
            depth=0,
            branch_id="root",
        )

    def initial_state(self, theorem_name: str) -> LeanProofState:
        return self.load_theorem(theorem_name)

    def execute_tactic(self, state: LeanProofState, tactic: str) -> LeanExecutionResult:
        self._ensure_available()
        # Placeholder: replace with stateful LeanDojo/Pantograph tactic execution.
        return LeanExecutionResult(
            accepted=False,
            solved=False,
            tactic=tactic,
            error_message=(
                "LeanDojo-v2 adapter placeholder: tactic execution wiring is not implemented yet."
            ),
            new_goals=list(state.open_goals),
            proof_state_text=state.as_prompt_text(),
            new_hypotheses=list(state.hypotheses),
            metadata={
                "backend": "leandojo_v2",
                "repo": self.repo,
                "commit": self.commit,
                "theorem_filter": self.theorem_filter,
                "placeholder": True,
            },
        )


# Backward-compatible alias used by early v0.7 planning notes.
IntegrationUnavailable = LeanDojoV2Unavailable
