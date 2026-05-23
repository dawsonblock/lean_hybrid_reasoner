from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.search.budgets import SearchBudget


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
