from __future__ import annotations

from collections import Counter
from typing import Any

from lean_hybrid_reasoner.diagnostics.failure_classifier import classify_records
from lean_hybrid_reasoner.traces.analytics import analyze_records


def _ratio(n: float, d: float) -> float:
    return n / d if d else 0.0


def summarize_for_compare(records: list[dict[str, Any]]) -> dict[str, Any]:
    analytics = analyze_records(records)
    classifications = classify_records(records)
    runs = len(records)
    solved = sum(1 for r in records if r.get("solved"))
    tactics = sum(int(r.get("tactics_attempted", 0)) for r in records)
    accepted = sum(int(r.get("accepted_tactics", 0)) for r in records)
    branches = sum(int(r.get("branches_explored", 0)) for r in records)
    return {
        "runs": runs,
        "solved": solved,
        "completion_rate": _ratio(solved, runs),
        "tactic_accept_rate": _ratio(accepted, tactics),
        "avg_tactics_attempted": _ratio(tactics, runs),
        "avg_branches_explored": _ratio(branches, runs),
        "by_status": analytics.get("by_status", {}),
        "by_failure_category": classifications.get("by_category", {}),
    }


def compare_trace_sets(left: list[dict[str, Any]], right: list[dict[str, Any]], left_label: str = "left", right_label: str = "right") -> dict[str, Any]:
    left_summary = summarize_for_compare(left)
    right_summary = summarize_for_compare(right)
    keys = sorted(set(left_summary) | set(right_summary))
    deltas: dict[str, Any] = {}
    for key in keys:
        a = left_summary.get(key)
        b = right_summary.get(key)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            deltas[key] = b - a
    left_theorems = Counter(r.get("theorem_name") for r in left)
    right_theorems = Counter(r.get("theorem_name") for r in right)
    return {
        "left_label": left_label,
        "right_label": right_label,
        "left": left_summary,
        "right": right_summary,
        "delta_right_minus_left": deltas,
        "theorem_count_delta": dict(right_theorems - left_theorems),
        "missing_from_right": dict(left_theorems - right_theorems),
    }
