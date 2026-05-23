from __future__ import annotations

from typing import Any

from lean_hybrid_reasoner.lean_backend.base import LeanBackend


def replay_proof(
    backend: LeanBackend,
    theorem_name: str,
    proof: list[str],
    *,
    verify_with_lean: bool = False,
) -> dict[str, Any]:
    """Replay a recorded proof prefix against the selected backend.

    This is intentionally backend-agnostic. It is useful for checking whether a
    trace remains valid after changing the backend, Lean file, heuristic rules,
    or Lean version.
    """
    state = backend.load_theorem(theorem_name)
    events: list[dict[str, Any]] = []

    for idx, tactic in enumerate(proof, start=1):
        result = backend.execute_tactic(state, tactic)
        events.append(
            {
                "step": idx,
                "tactic": tactic,
                "accepted": result.accepted,
                "solved": result.solved,
                "error": result.error_message,
                "new_goals": result.new_goals,
                "metadata": result.metadata,
            }
        )
        if not result.accepted:
            return {
                "theorem_name": theorem_name,
                "valid": False,
                "solved": False,
                "failed_step": idx,
                "events": events,
                "verification": None,
            }
        if result.solved:
            verification = (
                _verify_with_backend(backend, theorem_name, proof)
                if verify_with_lean
                else None
            )
            return {
                "theorem_name": theorem_name,
                "valid": True,
                "solved": True,
                "failed_step": None,
                "events": events,
                "verification": verification,
            }
        state = state.model_copy(
            update={
                "proof_prefix": [*state.proof_prefix, tactic],
                "current_goal": (
                    result.new_goals[0] if result.new_goals else state.current_goal
                ),
                "open_goals": result.new_goals,
                "hypotheses": result.new_hypotheses,
                "depth": state.depth + 1,
            }
        )

    return {
        "theorem_name": theorem_name,
        "valid": True,
        "solved": False,
        "failed_step": None,
        "events": events,
        "verification": None,
    }


def _verify_with_backend(
    backend: LeanBackend, theorem_name: str, proof: list[str]
) -> dict[str, Any]:
    if hasattr(backend, "verify_proof"):
        payload = backend.verify_proof(theorem_name, proof)  # type: ignore[attr-defined]
        if isinstance(payload, dict):
            return payload
    return {
        "verified": False,
        "skipped": True,
        "reason": "Selected backend does not support verify_proof.",
    }
