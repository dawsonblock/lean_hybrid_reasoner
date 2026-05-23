from __future__ import annotations

from lean_hybrid_reasoner.graph.nodes import run_search_node
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.search.budgets import SearchBudget


class SimpleProofGraph:
    """Small runnable graph facade.

    This keeps the repository usable without forcing LangGraph at install time.
    Replace this facade with a real StateGraph once you wire persistent checkpoints.
    """

    def __init__(self, engine: ProofSearchEngine, budget: SearchBudget | None = None):
        self.engine = engine
        self.budget = budget

    def invoke(self, state: dict) -> dict:
        return run_search_node(state, self.engine, self.budget)


def build_graph(engine: ProofSearchEngine, budget: SearchBudget | None = None):
    try:
        from langgraph.graph import StateGraph, START, END  # type: ignore
        from lean_hybrid_reasoner.graph.state import ProofGraphState

        graph = StateGraph(ProofGraphState)
        graph.add_node("run_search", lambda s: run_search_node(s, engine, budget))
        graph.add_edge(START, "run_search")
        graph.add_edge("run_search", END)
        return graph.compile()
    except Exception:
        return SimpleProofGraph(engine, budget)
