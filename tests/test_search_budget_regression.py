from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.budgets import SearchBudget
from lean_hybrid_reasoner.search.engine import ProofSearchEngine


def test_regression_max_total_tactics_enforced():
    engine = ProofSearchEngine(MockLeanBackend())
    result = engine.run(
        "impossible_example",
        SearchBudget(max_depth=16, max_branches=64, max_total_tactics=1),
    )
    assert result.tactics_attempted <= 1
    assert result.status in {"budget_exceeded", "failed", "timeout"}


def test_regression_tactic_memory_can_be_disabled():
    engine = ProofSearchEngine(MockLeanBackend())
    result = engine.run(
        "impossible_example",
        SearchBudget(
            max_depth=6,
            max_branches=16,
            max_total_tactics=32,
            enable_tactic_memory=False,
        ),
    )
    assert all(e.get("event") != "suppress_tactic" for e in result.trace)
