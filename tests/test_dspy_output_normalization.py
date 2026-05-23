from __future__ import annotations

from lean_hybrid_reasoner.dspy_modules.dspy_tactics import normalize_tactic_candidates


def test_normalize_candidates_handles_numbered_list():
    raw = "1. simp\n2. rfl"
    assert normalize_tactic_candidates(raw) == ["simp", "rfl"]


def test_normalize_candidates_handles_json_dict_shapes():
    raw = {"tactic_candidates": [{"tactic": "intro h"}, {"text": "apply h"}]}
    assert normalize_tactic_candidates(raw) == ["intro h", "apply h"]
