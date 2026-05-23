from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from lean_hybrid_reasoner.diagnostics.failure_classifier import (
    classify_failure,
    classify_records,
)


def analyze_record(record: dict[str, Any]) -> dict[str, Any]:
    events = record.get("trace", [])
    event_counts = Counter(e.get("event", "unknown") for e in events)
    tactic_counts = Counter()
    error_counts = Counter()
    prune_reasons = Counter()
    dead_reasons = Counter()
    branches = set()

    for e in events:
        branch = e.get("branch_id")
        if branch:
            branches.add(branch)
        if e.get("event") == "execute_tactic":
            tactic_counts[e.get("tactic", "")] += 1
            if e.get("error"):
                error_counts[str(e.get("error"))[:120]] += 1
        elif e.get("event") == "repair_tactic":
            tactic_counts[e.get("repair_tactic", "")] += 1
            if e.get("error"):
                error_counts[str(e.get("error"))[:120]] += 1
        elif e.get("event") == "prune_branch":
            prune_reasons[e.get("reason", "unknown")] += 1
        elif e.get("event") == "dead_branch":
            dead_reasons[e.get("reason", "unknown")] += 1

    tactics_attempted = int(record.get("tactics_attempted", 0))
    accepted_tactics = int(record.get("accepted_tactics", 0))
    branches_explored = int(record.get("branches_explored", 0))

    failure = classify_failure(record)

    return {
        "theorem_name": record.get("theorem_name"),
        "status": record.get("status"),
        "solved": bool(record.get("solved")),
        "failure_category": failure["category"],
        "failure_action": failure["action"],
        "proof_length": len(record.get("proof", [])),
        "event_counts": dict(event_counts),
        "top_tactics": tactic_counts.most_common(10),
        "top_errors": error_counts.most_common(10),
        "prune_reasons": dict(prune_reasons),
        "dead_reasons": dict(dead_reasons),
        "unique_branches_seen": len(branches),
        "accept_rate": (
            accepted_tactics / tactics_attempted if tactics_attempted else 0.0
        ),
        "tactics_per_branch": (
            tactics_attempted / branches_explored if branches_explored else 0.0
        ),
        "budget_pressure": {
            "hit_depth_or_budget": record.get("status")
            in {"budget_exceeded", "timeout"},
            "branches_explored": branches_explored,
            "branches_pruned": int(record.get("branches_pruned", 0)),
            "tactics_attempted": tactics_attempted,
        },
    }


def analyze_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    per_run = [analyze_record(r) for r in records]
    by_status = Counter(r.get("status") for r in records)
    all_tactics = Counter()
    all_errors = Counter()
    all_dead = Counter()
    all_prune = Counter()
    by_theorem = defaultdict(list)

    for raw, run in zip(records, per_run):
        by_theorem[raw.get("theorem_name")].append(run)
        all_tactics.update(dict(run["top_tactics"]))
        all_errors.update(dict(run["top_errors"]))
        all_dead.update(run["dead_reasons"])
        all_prune.update(run["prune_reasons"])

    solved = sum(1 for r in records if r.get("solved"))
    failure_summary = classify_records(records)

    return {
        "runs": len(records),
        "solved": solved,
        "failed": len(records) - solved,
        "by_status": dict(by_status),
        "by_failure_category": failure_summary["by_category"],
        "top_tactics": all_tactics.most_common(15),
        "top_errors": all_errors.most_common(15),
        "dead_reasons": dict(all_dead),
        "prune_reasons": dict(all_prune),
        "avg_tactics_attempted": (
            sum(int(r.get("tactics_attempted", 0)) for r in records) / len(records)
            if records
            else 0.0
        ),
        "avg_branches_explored": (
            sum(int(r.get("branches_explored", 0)) for r in records) / len(records)
            if records
            else 0.0
        ),
        "per_run": per_run,
    }
