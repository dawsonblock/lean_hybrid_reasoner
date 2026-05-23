from __future__ import annotations

from lean_hybrid_reasoner.schemas.branch import ProofBranch
from lean_hybrid_reasoner.schemas.tactic import LeanExecutionResult, TacticCandidate


def score_candidate(candidate: TacticCandidate) -> float:
    premise_bonus = min(len(candidate.required_premises), 3) * 0.05
    repair_bonus = 0.05 if candidate.metadata.get("source") == "repair" else 0.0
    return candidate.confidence + premise_bonus + repair_bonus


def score_branch(parent: ProofBranch, result: LeanExecutionResult) -> float:
    """Score child branches for best-first proof search.

    The key upgrade is explicit progress/stagnation control. Accepted tactics that
    do not reduce or change goals are not automatically good. They receive a
    stagnation penalty so the frontier does not drift through no-op branches.
    """
    old_goals = parent.open_goals or [parent.current_goal]
    new_goals = result.new_goals or []

    accepted_bonus = 2.0 if result.accepted else -2.0
    solved_bonus = 10.0 if result.solved else 0.0

    goal_delta = len(old_goals) - len(new_goals)
    fewer_goals_bonus = max(goal_delta, 0) * 1.0
    more_goals_penalty = max(-goal_delta, 0) * 0.75

    same_goal_penalty = 0.0
    if result.accepted and not result.solved:
        normalized_old = [g.strip() for g in old_goals]
        normalized_new = [g.strip() for g in new_goals]
        if normalized_new == normalized_old:
            same_goal_penalty = 1.5

    depth_penalty = (parent.depth + 1) * 0.12
    failure_penalty = len(parent.failures) * 0.25
    repeated_prefix_penalty = len(parent.proof_prefix) * 0.03

    return (
        parent.score
        + accepted_bonus
        + solved_bonus
        + fewer_goals_bonus
        - more_goals_penalty
        - same_goal_penalty
        - depth_penalty
        - failure_penalty
        - repeated_prefix_penalty
    )
