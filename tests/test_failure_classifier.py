from lean_hybrid_reasoner.diagnostics.failure_classifier import classify_failure, classify_records


def test_classifier_labels_solved():
    result = classify_failure({"theorem_name": "t", "solved": True, "status": "solved"})
    assert result["category"] == "solved"


def test_classifier_labels_tactic_budget():
    result = classify_failure({"solved": False, "status": "budget_exceeded", "error": "tactic budget exceeded", "trace": []})
    assert result["category"] == "tactic_budget_exceeded"


def test_classifier_summarizes_records():
    payload = classify_records([
        {"theorem_name": "a", "solved": True, "status": "solved"},
        {"theorem_name": "b", "solved": False, "status": "timeout", "error": "time budget exceeded"},
    ])
    assert payload["by_category"]["solved"] == 1
    assert payload["by_category"]["timeout"] == 1
