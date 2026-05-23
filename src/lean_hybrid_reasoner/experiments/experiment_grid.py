from __future__ import annotations

from typing import Callable, Any

from lean_hybrid_reasoner.evals.run_eval import run_starter_eval
from lean_hybrid_reasoner.search.budgets import named_budget


def run_experiment_grid(engine_factory: Callable[[str, str], Any], *, budget_profiles: list[str], retrieval_modes: list[str]) -> dict[str, Any]:
    """Run starter eval across budget/retrieval combinations.

    The engine_factory receives (budget_profile, retrieval_mode). The CLI uses
    this to rebuild an engine with a different retriever per grid cell.
    """
    output: dict[str, Any] = {}
    for retrieval_mode in retrieval_modes:
        output[retrieval_mode] = {}
        for profile in budget_profiles:
            engine = engine_factory(profile, retrieval_mode)
            budget = named_budget(profile)
            results, metrics = run_starter_eval(engine, budget_template=budget)
            output[retrieval_mode][profile] = {
                "metrics": metrics.model_dump(),
                "results": [r.model_dump() for r in results],
            }
    return output
