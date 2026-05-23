from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.search.budgets import SearchBudget
from lean_hybrid_reasoner.schemas.tactic import TacticCandidate


def test_search_solves_and_comm():
    engine = ProofSearchEngine(MockLeanBackend())
    result = engine.run("and_comm_example", SearchBudget(max_depth=8, max_branches=16))
    assert result.solved is True
    assert result.proof == ["intro h", "exact And.intro h.right h.left"]


def test_search_fails_impossible():
    engine = ProofSearchEngine(MockLeanBackend())
    result = engine.run("impossible_example", SearchBudget(max_depth=4, max_branches=8))
    assert result.solved is False
    assert result.status in {"failed", "budget_exceeded", "timeout"}


class _BadThenGoodProposer:
    def propose(self, _state, max_candidates: int = 8):
        candidates = [
            TacticCandidate(tactic="Here is the proof", confidence=1.0),
            TacticCandidate(tactic="simp", confidence=0.9),
        ]
        return candidates[:max_candidates]


def test_invalid_tactic_is_rejected_before_backend_execution():
    engine = ProofSearchEngine(MockLeanBackend(), proposer=_BadThenGoodProposer())
    result = engine.run("add_zero_example", SearchBudget(max_depth=4, max_branches=8))
    assert result.solved is True
    assert result.proof == ["simp"]
    rejected = [
        event
        for event in result.trace
        if event.get("event") == "tactic_rejected"
        and event.get("tactic_event_type") == "tactic_attempt"
        and event.get("reason") == "natural_language"
    ]
    assert rejected
    assert rejected[0]["reason"] == "natural_language"
