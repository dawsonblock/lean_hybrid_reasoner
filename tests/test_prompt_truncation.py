from lean_hybrid_reasoner.schemas.proof_state import LeanProofState


def test_prompt_text_is_bounded():
    state = LeanProofState(
        theorem_name="big",
        theorem_statement="theorem big : True := by",
        current_goal="True",
        hypotheses=[f"h{i} : SomeVeryLongTypeWithData{i}" for i in range(500)],
        proof_prefix=["simp"] * 500,
        open_goals=["True"],
        retrieved_premises=[f"lemma_{i}: statement" for i in range(500)],
    )
    text = state.as_prompt_text(max_section_chars=200, max_total_chars=1000)
    assert len(text) <= 1050
    assert "truncated" in text
