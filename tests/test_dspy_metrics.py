from __future__ import annotations

from lean_hybrid_reasoner.dspy_modules.metrics import (
    tactic_match_or_accept_metric,
    verifier_success_metric,
)
from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend


def test_tactic_match_or_accept_metric_exact_match_scores_one():
    example = {"target_tactic": "simp"}
    prediction = {"tactic": "simp"}
    assert tactic_match_or_accept_metric(example, prediction) == 1.0


def test_tactic_match_or_accept_metric_valid_non_match_scores_partial():
    example = {"target_tactic": "simp"}
    prediction = {"tactic": "rfl"}
    assert tactic_match_or_accept_metric(example, prediction) == 0.7


def test_tactic_match_or_accept_metric_invalid_scores_zero():
    example = {"target_tactic": "simp"}
    prediction = {"tactic": "Here is the proof"}
    assert tactic_match_or_accept_metric(example, prediction) == 0.0


def test_verifier_success_metric_rewards_accepted_and_solved():
    backend = MockLeanBackend()
    example = {"theorem_name": "add_zero_example"}
    score = verifier_success_metric(example, {"tactic": "simp"}, backend)
    assert score > 0.5


def test_verifier_success_metric_penalizes_invalid_output():
    backend = MockLeanBackend()
    example = {"theorem_name": "add_zero_example"}
    score = verifier_success_metric(example, {"tactic": "Because this works"}, backend)
    assert score <= 0.0
