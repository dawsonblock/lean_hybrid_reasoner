from __future__ import annotations

from lean_hybrid_reasoner.evals.theorem_sets import STARTER_THEOREMS
from lean_hybrid_reasoner.evals.metrics import compute_metrics
from lean_hybrid_reasoner.search.budgets import SearchBudget
from lean_hybrid_reasoner.search.engine import ProofSearchEngine


def run_starter_eval(
    engine: ProofSearchEngine,
    max_depth: int = 16,
    max_branches: int = 64,
    budget_template: SearchBudget | None = None,
):
    results = []
    for example in STARTER_THEOREMS:
        if budget_template is None:
            budget = SearchBudget(max_depth=max_depth, max_branches=max_branches)
        else:
            budget_data = budget_template.model_dump(exclude={"started_at"})
            budget_data["max_depth"] = max_depth
            budget_data["max_branches"] = max_branches
            budget = SearchBudget(**budget_data)
        result = engine.run(example.theorem_name, budget)
        results.append(result)
    return results, compute_metrics(results)
