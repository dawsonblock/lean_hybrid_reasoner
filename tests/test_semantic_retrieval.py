from lean_hybrid_reasoner.retrieval.semantic_index import HashingSemanticPremiseIndex
from lean_hybrid_reasoner.retrieval.premise_retriever import PremiseRetriever
from lean_hybrid_reasoner.schemas.proof_state import LeanProofState


def test_hashing_semantic_retrieval_finds_add_zero():
    index = HashingSemanticPremiseIndex.starter()
    hits = index.search("prove n + 0 = n", top_k=3)
    assert any(h.name == "Nat.add_zero" for h in hits)


def test_premise_retriever_mode_semantic():
    retriever = PremiseRetriever.from_mode("semantic", top_k=3)
    state = LeanProofState(
        theorem_name="x",
        theorem_statement="theorem x (n : Nat) : n + 0 = n := by",
        current_goal="n + 0 = n",
        hypotheses=["n : Nat"],
        open_goals=["n + 0 = n"],
    )
    premises = retriever.retrieve(state)
    assert any("Nat.add_zero" in p for p in premises)
