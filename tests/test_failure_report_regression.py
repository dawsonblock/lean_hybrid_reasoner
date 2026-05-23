from lean_hybrid_reasoner.diagnostics.failure_classifier import classify_records


def test_regression_failure_report_by_category_counts():
    payload = classify_records(
        [
            {"theorem_name": "a", "solved": True, "status": "solved", "trace": []},
            {
                "theorem_name": "b",
                "solved": False,
                "status": "timeout",
                "error": "time budget exceeded",
                "trace": [],
            },
            {
                "theorem_name": "b",
                "solved": False,
                "status": "failed",
                "error": "frontier exhausted",
                "trace": [],
            },
        ]
    )
    assert payload["runs"] == 3
    assert payload["by_category"]["solved"] == 1
    assert payload["by_category"].get("timeout", 0) >= 1


def test_regression_failure_report_includes_theorem_grouping():
    payload = classify_records(
        [
            {"theorem_name": "alpha", "solved": False, "status": "failed", "trace": []},
            {"theorem_name": "alpha", "solved": True, "status": "solved", "trace": []},
            {
                "theorem_name": "beta",
                "solved": False,
                "status": "timeout",
                "error": "time budget exceeded",
                "trace": [],
            },
        ]
    )
    assert "by_theorem" in payload
    assert payload["by_theorem"]["alpha"]["runs"] == 2
    assert payload["by_theorem"]["beta"]["runs"] == 1
