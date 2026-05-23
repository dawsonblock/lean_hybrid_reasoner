from lean_hybrid_reasoner.experiments.experiment_grid import run_experiment_grid
from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.retrieval.premise_retriever import PremiseRetriever
from lean_hybrid_reasoner.search.engine import ProofSearchEngine


def test_experiment_grid_runs_profiles_and_retrievers():
    def factory(profile, mode):
        return ProofSearchEngine(MockLeanBackend(), retriever=PremiseRetriever.from_mode(mode))

    payload = run_experiment_grid(factory, budget_profiles=["tiny"], retrieval_modes=["bm25", "semantic"])
    assert set(payload) == {"bm25", "semantic"}
    assert "tiny" in payload["bm25"]
    assert "metrics" in payload["semantic"]["tiny"]
