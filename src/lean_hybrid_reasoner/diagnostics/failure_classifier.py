from __future__ import annotations

from collections import Counter
from typing import Any


def classify_failure(record: dict[str, Any]) -> dict[str, Any]:
    """Classify a proof run into a stable failure category.

    This is intentionally heuristic and trace-based. It is used for experiment
    reports and triage, not as a proof result. Lean/kernel acceptance remains
    the authority for correctness.
    """
    if bool(record.get("solved")):
        return {
            "category": "solved",
            "severity": "none",
            "reason": "Proof completed.",
            "action": "Keep as a positive training/evaluation example.",
        }

    status = str(record.get("status", "unknown"))
    error = str(record.get("error") or "")
    trace = record.get("trace") or []
    dead_reasons = Counter(
        e.get("reason", "unknown") for e in trace if e.get("event") == "dead_branch"
    )
    prune_reasons = Counter(
        e.get("reason", "unknown") for e in trace if e.get("event") == "prune_branch"
    )
    tactic_errors = [
        str(e.get("error"))
        for e in trace
        if e.get("event") in {"execute_tactic", "repair_tactic"} and e.get("error")
    ]
    candidate_events = [e for e in trace if e.get("event") == "expand_branch"]

    if status == "timeout" or "time budget" in error.lower():
        return {
            "category": "timeout",
            "severity": "budget",
            "reason": error or "The run exceeded the wall-clock budget.",
            "action": "Increase max_seconds or reduce branching by improving tactic ranking.",
        }
    if "tactic budget" in error.lower():
        return {
            "category": "tactic_budget_exceeded",
            "severity": "budget",
            "reason": error,
            "action": "Increase max_total_tactics or reduce low-value tactic candidates.",
        }
    if "branch budget" in error.lower():
        return {
            "category": "branch_budget_exceeded",
            "severity": "budget",
            "reason": error,
            "action": "Increase max_branches or improve branch scoring/pruning.",
        }
    if status == "budget_exceeded":
        return {
            "category": "budget_exceeded",
            "severity": "budget",
            "reason": error or "A search budget was exceeded.",
            "action": "Run budget-sweep to identify the limiting budget knob.",
        }
    if dead_reasons.get("depth_exceeded", 0):
        return {
            "category": "depth_exceeded",
            "severity": "search",
            "reason": "A branch hit max_depth before QED.",
            "action": "Increase max_depth only if traces show accepted tactics making real progress.",
        }
    if dead_reasons.get("stagnation_exceeded", 0):
        return {
            "category": "stagnation_exceeded",
            "severity": "search",
            "reason": "Accepted tactics stopped changing the proof state.",
            "action": "Penalize repeated non-progress tactics or improve the repair/proposer modules.",
        }
    if prune_reasons and sum(prune_reasons.values()) >= max(
        1, int(record.get("branches_explored", 0))
    ):
        return {
            "category": "duplicate_state_loop",
            "severity": "search",
            "reason": "Most explored branches collapsed into already-seen states.",
            "action": "Improve candidate diversity and avoid tactics that return to equivalent states.",
        }
    if candidate_events and all(
        not e.get("candidate_tactics") for e in candidate_events
    ):
        return {
            "category": "no_candidates",
            "severity": "proposer",
            "reason": "The proposer did not emit tactic candidates.",
            "action": "Fix proposer output normalization or fallback heuristic candidates.",
        }
    if tactic_errors:
        common = Counter(tactic_errors).most_common(1)[0][0]
        return {
            "category": "tactic_errors",
            "severity": "proposer",
            "reason": common[:240],
            "action": "Improve tactic proposal/repair using this Lean error as feedback data.",
        }
    if status == "failed":
        return {
            "category": "frontier_exhausted",
            "severity": "search",
            "reason": error or "The frontier was exhausted without a proof.",
            "action": "Improve tactic generation/ranking before increasing broad budgets.",
        }
    return {
        "category": "unknown_failure",
        "severity": "unknown",
        "reason": error or f"Unclassified status: {status}",
        "action": "Inspect trace-dot and trace-analytics for branch-level evidence.",
    }


def classify_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    classified = [
        {
            **classify_failure(r),
            "theorem_name": r.get("theorem_name"),
            "status": r.get("status"),
        }
        for r in records
    ]
    by_category = Counter(item["category"] for item in classified)
    by_severity = Counter(item["severity"] for item in classified)
    by_theorem: dict[str, dict[str, Any]] = {}
    for item in classified:
        theorem = str(item.get("theorem_name") or "unknown")
        if theorem not in by_theorem:
            by_theorem[theorem] = {"runs": 0, "by_category": {}}
        by_theorem[theorem]["runs"] += 1
        theorem_cats: dict[str, int] = by_theorem[theorem]["by_category"]
        category = str(item["category"])
        theorem_cats[category] = theorem_cats.get(category, 0) + 1
    return {
        "runs": len(records),
        "by_category": dict(by_category),
        "by_severity": dict(by_severity),
        "by_theorem": by_theorem,
        "records": classified,
    }
