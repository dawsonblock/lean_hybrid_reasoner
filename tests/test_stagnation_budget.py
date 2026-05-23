from copy import deepcopy
from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend, THEOREMS
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.search.budgets import SearchBudget


def test_stagnation_budget_field_exists_and_search_still_solves():
    engine = ProofSearchEngine(MockLeanBackend(deepcopy(THEOREMS)))
    result = engine.run("and_comm_example", SearchBudget(max_depth=8, max_branches=16, max_stagnant_steps=1))
    assert result.solved is True
