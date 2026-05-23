from lean_hybrid_reasoner.dspy_modules.dspy_tactics import _normalise_tactic_list


def test_normalise_dspy_list_output():
    out = _normalise_tactic_list(["simp", {"tactic": "rfl", "confidence": 0.8}], max_candidates=4, source="test")
    assert [x.tactic for x in out] == ["simp", "rfl"]
    assert out[1].confidence == 0.8


def test_normalise_dspy_json_output():
    raw = '[{"tactic": "intro h", "confidence": 0.9}]'
    out = _normalise_tactic_list(raw, max_candidates=4, source="test")
    assert out[0].tactic == "intro h"
    assert out[0].metadata["source"] == "test"
