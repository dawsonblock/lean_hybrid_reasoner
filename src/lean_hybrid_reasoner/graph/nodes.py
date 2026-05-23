from __future__ import annotations

from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.search.budgets import SearchBudget


def run_search_node(state: dict, engine: ProofSearchEngine, budget: SearchBudget | None = None) -> dict:
    result = engine.run(state["theorem_name"], budget=budget)
    return {**state, "result": result.model_dump(), "trace": result.trace}
