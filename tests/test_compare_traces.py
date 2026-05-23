from lean_hybrid_reasoner.experiments.compare import compare_trace_sets, summarize_for_compare


def test_compare_trace_sets_reports_delta():
    left = [{"theorem_name": "a", "solved": False, "status": "failed", "tactics_attempted": 2, "accepted_tactics": 0, "branches_explored": 1, "trace": []}]
    right = [{"theorem_name": "a", "solved": True, "status": "solved", "tactics_attempted": 2, "accepted_tactics": 2, "branches_explored": 1, "trace": []}]
    payload = compare_trace_sets(left, right)
    assert payload["delta_right_minus_left"]["completion_rate"] == 1.0
    assert payload["right"]["by_failure_category"]["solved"] == 1


def test_summarize_for_compare_handles_empty():
    payload = summarize_for_compare([])
    assert payload["runs"] == 0
    assert payload["completion_rate"] == 0.0
