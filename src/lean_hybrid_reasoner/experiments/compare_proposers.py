from __future__ import annotations

from statistics import median
from typing import Any

from lean_hybrid_reasoner.evals.run_eval import run_starter_eval
from lean_hybrid_reasoner.search.budgets import named_budget


def _summarize(results: list[Any], name: str) -> dict[str, Any]:
    total = len(results)
    solved = sum(1 for r in results if r.solved)
    attempted = sum(r.tactics_attempted for r in results)
    accepted = sum(r.accepted_tactics for r in results)
    solved_steps = [len(r.proof) for r in results if r.solved]
    return {
        "name": name,
        "solved": solved,
        "total": total,
        "completion_rate": solved / total if total else 0.0,
        "tactic_acceptance_rate": accepted / attempted if attempted else 0.0,
        "median_steps_to_qed": float(median(solved_steps)) if solved_steps else 0.0,
    }


def compare_proposers(
    *,
    left_name: str,
    right_name: str,
    left_engine: Any,
    right_engine: Any,
    budget_profile: str = "starter",
) -> dict[str, Any]:
    budget = named_budget(budget_profile)
    left_results, _ = run_starter_eval(
        left_engine,
        max_depth=budget.max_depth,
        max_branches=budget.max_branches,
        budget_template=budget,
    )
    right_results, _ = run_starter_eval(
        right_engine,
        max_depth=budget.max_depth,
        max_branches=budget.max_branches,
        budget_template=budget,
    )

    left = _summarize(left_results, left_name)
    right = _summarize(right_results, right_name)
    winner = "tie"
    if left["completion_rate"] > right["completion_rate"]:
        winner = left_name
    elif right["completion_rate"] > left["completion_rate"]:
        winner = right_name

    return {
        "left": left,
        "right": right,
        "winner": winner,
    }
