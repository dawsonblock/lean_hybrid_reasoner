from __future__ import annotations

from copy import deepcopy

from lean_hybrid_reasoner.schemas.proof_state import LeanProofState
from lean_hybrid_reasoner.schemas.tactic import LeanExecutionResult


THEOREMS: dict[str, dict] = {
    "add_zero_example": {
        "statement": "theorem add_zero_example (n : Nat) : n + 0 = n := by",
        "goal": "n + 0 = n",
        "hypotheses": ["n : Nat"],
        "solutions": [["simp"], ["rfl"]],
    },
    "zero_add_example": {
        "statement": "theorem zero_add_example (n : Nat) : 0 + n = n := by",
        "goal": "0 + n = n",
        "hypotheses": ["n : Nat"],
        "solutions": [["simp"], ["rfl"]],
    },
    "and_comm_example": {
        "statement": "theorem and_comm_example (p q : Prop) : p ∧ q → q ∧ p := by",
        "goal": "p ∧ q → q ∧ p",
        "hypotheses": ["p q : Prop"],
        "solutions": [["intro h", "exact And.intro h.right h.left"]],
    },
    "impossible_example": {
        "statement": "theorem impossible_example (p : Prop) : p := by",
        "goal": "p",
        "hypotheses": ["p : Prop"],
        "solutions": [],
    },
}


class MockLeanBackend:
    """Deterministic Lean-like backend for testing the control loop.

    It does not verify Lean. It simulates a few small proof states so branch search,
    budget limits, traces, and metrics can be developed without a Lean install.
    """

    def __init__(self, theorems: dict[str, dict] | None = None):
        self.theorems = deepcopy(theorems or THEOREMS)

    def list_theorems(self) -> list[str]:
        return sorted(self.theorems.keys())

    def load_theorem(self, theorem_name: str) -> LeanProofState:
        if theorem_name not in self.theorems:
            raise KeyError(f"Unknown theorem: {theorem_name}")
        spec = self.theorems[theorem_name]
        return LeanProofState(
            theorem_name=theorem_name,
            theorem_statement=spec["statement"],
            current_goal=spec["goal"],
            hypotheses=list(spec.get("hypotheses", [])),
            open_goals=[spec["goal"]],
            proof_prefix=[],
            depth=0,
            branch_id="root",
        )

    def execute_tactic(self, state: LeanProofState, tactic: str) -> LeanExecutionResult:
        theorem = self.theorems[state.theorem_name]
        prefix = [*state.proof_prefix, tactic]

        # Exact successful prefix from solution list.
        for solution in theorem.get("solutions", []):
            if prefix == solution:
                return LeanExecutionResult(
                    accepted=True,
                    solved=True,
                    tactic=tactic,
                    new_goals=[],
                    proof_state_text="no goals",
                    new_hypotheses=list(state.hypotheses),
                )
            if solution[: len(prefix)] == prefix:
                return self._partial_state(state, tactic, prefix)

        # General tactic simulations.
        goal = state.current_goal
        normalized = tactic.strip()

        if normalized in {"simp", "rfl"} and ("+ 0" in goal or "0 +" in goal):
            return LeanExecutionResult(
                accepted=True,
                solved=True,
                tactic=tactic,
                new_goals=[],
                proof_state_text="no goals",
                new_hypotheses=list(state.hypotheses),
            )

        if normalized.startswith("intro") and "→" in goal:
            parts = normalized.split()
            name = parts[1] if len(parts) > 1 else "h"
            consequent = goal.split("→", 1)[1].strip()
            antecedent = goal.split("→", 1)[0].strip()
            return LeanExecutionResult(
                accepted=True,
                solved=False,
                tactic=tactic,
                new_goals=[consequent],
                proof_state_text=f"1 goal\n{name} : {antecedent}\n⊢ {consequent}",
                new_hypotheses=[*state.hypotheses, f"{name} : {antecedent}"],
            )

        if normalized == "assumption" and any(h.split(":", 1)[-1].strip() == goal for h in state.hypotheses):
            return LeanExecutionResult(
                accepted=True,
                solved=True,
                tactic=tactic,
                new_goals=[],
                proof_state_text="no goals",
                new_hypotheses=list(state.hypotheses),
            )

        return LeanExecutionResult(
            accepted=False,
            solved=False,
            tactic=tactic,
            error_message=f"mock Lean error: tactic '{tactic}' failed for goal '{goal}'",
            new_goals=list(state.open_goals),
            proof_state_text=state.as_prompt_text(),
            new_hypotheses=list(state.hypotheses),
        )

    def _partial_state(self, state: LeanProofState, tactic: str, prefix: list[str]) -> LeanExecutionResult:
        # This handles the first step of and_comm_example.
        if state.theorem_name == "and_comm_example" and prefix == ["intro h"]:
            return LeanExecutionResult(
                accepted=True,
                solved=False,
                tactic=tactic,
                new_goals=["q ∧ p"],
                proof_state_text="1 goal\nh : p ∧ q\n⊢ q ∧ p",
                new_hypotheses=[*state.hypotheses, "h : p ∧ q"],
            )

        return LeanExecutionResult(
            accepted=True,
            solved=False,
            tactic=tactic,
            new_goals=list(state.open_goals),
            proof_state_text=state.as_prompt_text(),
            new_hypotheses=list(state.hypotheses),
        )
