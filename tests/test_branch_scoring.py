from lean_hybrid_reasoner.schemas.branch import ProofBranch
from lean_hybrid_reasoner.schemas.tactic import LeanExecutionResult
from lean_hybrid_reasoner.search.scoring import score_branch


def test_solved_branch_scores_higher():
    branch = ProofBranch(branch_id="root", theorem_name="x", current_goal="goal")
    accepted = LeanExecutionResult(accepted=True, solved=False, tactic="intro h", new_goals=["g"])
    solved = LeanExecutionResult(accepted=True, solved=True, tactic="simp")
    assert score_branch(branch, solved) > score_branch(branch, accepted)
