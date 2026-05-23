from lean_hybrid_reasoner.retrieval.premise_index import PremiseIndex


def test_retrieval_finds_add_zero():
    index = PremiseIndex.starter()
    hits = index.search("n + 0 = n")
    assert any(h.name == "Nat.add_zero" for h in hits)
