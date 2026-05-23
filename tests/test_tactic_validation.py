from lean_hybrid_reasoner.tactics.validation import is_probably_tactic


def test_accept_common_tactics():
    assert is_probably_tactic("simp") is True
    assert is_probably_tactic("intro h") is True
    assert is_probably_tactic("exact And.intro h.right h.left") is True
    assert is_probably_tactic("rw [Nat.add_assoc]") is True


def test_reject_natural_language_patterns():
    assert is_probably_tactic("Here is the proof") is False
    assert is_probably_tactic("I would use simp") is False
    assert is_probably_tactic("First, we introduce h.") is False
