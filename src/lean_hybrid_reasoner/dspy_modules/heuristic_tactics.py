from __future__ import annotations

from lean_hybrid_reasoner.schemas.proof_state import LeanProofState
from lean_hybrid_reasoner.schemas.tactic import TacticCandidate
from lean_hybrid_reasoner.lean_backend.error_parser import parse_lean_error


class HeuristicTacticProposer:
    """Deterministic tactic proposer used before DSPy/LLM integration."""

    def propose(self, state: LeanProofState, max_candidates: int = 8) -> list[TacticCandidate]:
        goal = state.current_goal
        hyps = "\n".join(state.hypotheses)
        candidates: list[TacticCandidate] = []

        if "→" in goal:
            candidates.append(TacticCandidate(tactic="intro h", confidence=0.9, rationale="Introduce implication premise."))

        if "+ 0" in goal or "0 +" in goal:
            candidates.extend([
                TacticCandidate(tactic="simp", confidence=0.95, rationale="Simplify Nat addition identity."),
                TacticCandidate(tactic="rfl", confidence=0.55, rationale="Try reflexivity after reduction."),
            ])

        if "q ∧ p" in goal and "h : p ∧ q" in hyps:
            candidates.append(
                TacticCandidate(
                    tactic="exact And.intro h.right h.left",
                    confidence=0.95,
                    rationale="Construct conjunction in swapped order from h.",
                    required_premises=["And.intro", "And.right", "And.left"],
                )
            )

        candidates.extend([
            TacticCandidate(tactic="assumption", confidence=0.3, rationale="Try matching hypothesis."),
            TacticCandidate(tactic="simp", confidence=0.25, rationale="General simplification fallback."),
        ])

        # De-duplicate while preserving order and highest confidence.
        seen: set[str] = set()
        unique: list[TacticCandidate] = []
        for c in sorted(candidates, key=lambda x: x.confidence, reverse=True):
            if c.tactic not in seen:
                seen.add(c.tactic)
                unique.append(c)
        return unique[:max_candidates]


class HeuristicTacticRepairer:
    def repair(self, state: LeanProofState, failed_tactic: str, error_message: str | None) -> list[TacticCandidate]:
        parsed = parse_lean_error(error_message)
        if parsed.category == "unknown_identifier":
            return [TacticCandidate(tactic="simp", confidence=0.4, rationale="Fallback after unknown identifier.", metadata={"source": "repair"})]
        if parsed.category in {"type_mismatch", "unsolved_goals", "other"}:
            return [c.model_copy(update={"metadata": {**c.metadata, "source": "repair"}}) for c in HeuristicTacticProposer().propose(state, max_candidates=4)]
        return []
