from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.evals.budget_sweep import run_budget_sweep


def test_budget_sweep_runs_profiles():
    engine = ProofSearchEngine(MockLeanBackend())
    payload = run_budget_sweep(engine)
    assert "tiny" in payload
    assert "starter" in payload
    assert "metrics" in payload["starter"]
