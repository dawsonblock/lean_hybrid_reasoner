from __future__ import annotations

from lean_hybrid_reasoner.evals.run_eval import run_starter_eval
from lean_hybrid_reasoner.search.budgets import SearchBudget
from lean_hybrid_reasoner.search.engine import ProofSearchEngine


SWEEP_PROFILES: dict[str, SearchBudget] = {
    "tiny": SearchBudget(max_depth=4, max_branches=8, max_total_tactics=32, max_seconds=5.0),
    "starter": SearchBudget(max_depth=16, max_branches=64, max_total_tactics=512, max_seconds=20.0),
    "wide": SearchBudget(max_depth=16, max_branches=256, max_total_tactics=2048, max_seconds=60.0),
    "deep": SearchBudget(max_depth=48, max_branches=128, max_total_tactics=2048, max_seconds=60.0),
}


def run_budget_sweep(engine: ProofSearchEngine, profiles: dict[str, SearchBudget] | None = None) -> dict:
    output = {}
    for name, budget in (profiles or SWEEP_PROFILES).items():
        # Use fresh started_at timestamps for each profile.
        fresh_budget = SearchBudget(**{k: v for k, v in budget.model_dump().items() if k != "started_at"})
        results, metrics = run_starter_eval(
            engine,
            max_depth=fresh_budget.max_depth,
            max_branches=fresh_budget.max_branches,
            budget_template=fresh_budget,
        )
        output[name] = {
            "budget": fresh_budget.model_dump(),
            "metrics": metrics.model_dump(),
            "results": [r.model_dump() for r in results],
        }
    return output
