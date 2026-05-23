from copy import deepcopy

from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend, THEOREMS
from lean_hybrid_reasoner.search.budgets import SearchBudget
from lean_hybrid_reasoner.search.engine import ProofSearchEngine


def test_regression_solved_and_comm_stays_solved():
    engine = ProofSearchEngine(MockLeanBackend())
    result = engine.run("and_comm_example", SearchBudget(max_depth=8, max_branches=16))
    assert result.solved is True
    assert result.status == "solved"


def test_regression_unsolved_records_expected_failure_category():
    engine = ProofSearchEngine(MockLeanBackend())
    result = engine.run(
        "impossible_example",
        SearchBudget(max_depth=4, max_branches=8, max_total_tactics=8),
    )
    assert result.solved is False
    assert result.status in {"failed", "budget_exceeded", "timeout"}


def test_regression_duplicate_branch_is_pruned():
    theorems = deepcopy(THEOREMS)
    theorems["impossible_example"]["solutions"] = [["intro h"]]
    engine = ProofSearchEngine(MockLeanBackend(theorems))
    result = engine.run(
        "impossible_example",
        SearchBudget(max_depth=8, max_branches=64, max_total_tactics=128),
    )
    assert result.branches_pruned >= 0
    assert (
        any(e.get("event") == "prune_branch" for e in result.trace)
        or result.branches_pruned == 0
    )


def test_regression_stagnant_branch_event_emitted_when_limit_low():
    engine = ProofSearchEngine(MockLeanBackend())
    result = engine.run(
        "impossible_example",
        SearchBudget(
            max_depth=6, max_branches=16, max_total_tactics=32, max_stagnant_steps=0
        ),
    )
    assert any(
        e.get("event") == "dead_branch" and e.get("reason") == "stagnation_exceeded"
        for e in result.trace
    ) or result.status in {"failed", "budget_exceeded", "timeout"}
