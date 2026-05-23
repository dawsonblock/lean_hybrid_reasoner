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


def test_permissive_mode_accepts_additional_common_lean_tactics():
    assert is_probably_tactic("simp_all", mode="permissive") is True
    assert is_probably_tactic("norm_num", mode="permissive") is True
    assert is_probably_tactic("refine And.intro ?_ ?_", mode="permissive") is True
    assert is_probably_tactic("all_goals simp", mode="permissive") is True


def test_strict_mode_keeps_existing_behavior_for_permissive_only_tactics():
    assert is_probably_tactic("simp_all", mode="strict") is False
    assert is_probably_tactic("all_goals simp", mode="strict") is False
