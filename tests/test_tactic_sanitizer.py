from lean_hybrid_reasoner.tactics.sanitizer import sanitize_tactic


def test_strip_code_fence():
    result = sanitize_tactic("```lean\nsimp\n```")
    assert result.valid is True
    assert result.cleaned == "simp"


def test_strip_prefix_and_quotes():
    result = sanitize_tactic('"The best tactic is: intro h"')
    assert result.valid is True
    assert result.cleaned == "intro h"


def test_strip_markdown_bullet():
    result = sanitize_tactic("- exact h")
    assert result.valid is True
    assert result.cleaned == "exact h"


def test_reject_natural_language():
    result = sanitize_tactic(
        "You should introduce the hypothesis and then prove both directions."
    )
    assert result.valid is False
    assert result.reason == "natural_language"


def test_reject_too_long():
    result = sanitize_tactic("a" * 300, max_length=240)
    assert result.valid is False
    assert result.reason == "too_long"


def test_reject_sorry_and_admit_by_default():
    sorry = sanitize_tactic("sorry")
    admit = sanitize_tactic("admit")
    assert sorry.valid is False
    assert sorry.reason == "contains_sorry"
    assert admit.valid is False
    assert admit.reason == "contains_admit"


def test_reject_multiple_tactic_suggestions():
    result = sanitize_tactic("simp\nrfl\nexact h")
    assert result.valid is False
    assert result.reason == "multiple_suggestions"


def test_permissive_mode_accepts_common_non_strict_tactics():
    result = sanitize_tactic("simp_all", mode="permissive")
    assert result.valid is True
    assert result.cleaned == "simp_all"


def test_strict_mode_rejects_permissive_only_tactic():
    result = sanitize_tactic("simp_all", mode="strict")
    assert result.valid is False
    assert result.reason == "natural_language"
