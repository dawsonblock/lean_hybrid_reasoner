from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.budgets import SearchBudget
from lean_hybrid_reasoner.search.engine import ProofSearchEngine


def test_tactic_budget_is_enforced():
    engine = ProofSearchEngine(MockLeanBackend())
    result = engine.run("impossible_example", SearchBudget(max_depth=16, max_branches=64, max_total_tactics=1))
    assert result.solved is False
    assert result.status in {"budget_exceeded", "failed"}
    assert result.tactics_attempted <= 1
