from __future__ import annotations

try:
    import dspy  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    dspy = None


if dspy is not None:  # pragma: no cover - optional integration definitions
    class SuggestTactic(dspy.Signature):
        """Suggest next Lean tactic candidates from a theorem, proof state, and retrieved premises."""
        theorem_statement: str = dspy.InputField()
        proof_state: str = dspy.InputField()
        retrieved_premises: list[str] = dspy.InputField()
        tactic_candidates: list[str] = dspy.OutputField()

    class RepairTactic(dspy.Signature):
        """Repair a failed Lean tactic using the current proof state and Lean error."""
        theorem_statement: str = dspy.InputField()
        proof_state: str = dspy.InputField()
        failed_tactic: str = dspy.InputField()
        lean_error: str = dspy.InputField()
        repaired_tactic: str = dspy.OutputField()

    class RankTactics(dspy.Signature):
        """Rank Lean tactics by expected verifier success."""
        proof_state: str = dspy.InputField()
        tactic_candidates: list[str] = dspy.InputField()
        ranked_tactics: list[str] = dspy.OutputField()

    class SelectPremises(dspy.Signature):
        """Select relevant Lean premises for the current proof state."""
        theorem_statement: str = dspy.InputField()
        proof_state: str = dspy.InputField()
        candidate_premises: list[str] = dspy.InputField()
        selected_premises: list[str] = dspy.OutputField()
else:
    SuggestTactic = RepairTactic = RankTactics = SelectPremises = None
