from __future__ import annotations

from lean_hybrid_reasoner.schemas.result import ProofRunResult, SearchMetrics


def compute_metrics(results: list[ProofRunResult]) -> SearchMetrics:
    if not results:
        return SearchMetrics(
            proof_completion_rate=0.0,
            tactic_accept_rate=0.0,
            branch_efficiency=0.0,
            timeout_rate=0.0,
            repair_success_rate=0.0,
            premise_hit_rate=0.0,
            budget_failure_rate=0.0,
            median_steps_to_qed=0.0,
            score=0.0,
        )

    solved = sum(1 for r in results if r.solved)
    attempted = sum(r.tactics_attempted for r in results)
    accepted = sum(r.accepted_tactics for r in results)
    branches = sum(r.branches_explored for r in results)
    timeouts = sum(1 for r in results if r.status == "timeout")
    budget_failures = sum(1 for r in results if r.status in {"budget_exceeded", "timeout"})
    repair_attempts = sum(r.repair_attempts for r in results)
    repair_successes = sum(r.repair_successes for r in results)

    premise_hits = 0
    premise_checks = 0
    for result in results:
        final_proof = "\n".join(result.proof)
        for event in result.trace:
            if event.get("event") != "expand_branch":
                continue
            for premise in event.get("premises", []):
                premise_checks += 1
                name = premise.split(":", 1)[0].strip()
                if name and name in final_proof:
                    premise_hits += 1

    solved_lengths = sorted(len(r.proof) for r in results if r.solved)
    if solved_lengths:
        mid = len(solved_lengths) // 2
        median_steps_to_qed = float(solved_lengths[mid] if len(solved_lengths) % 2 else (solved_lengths[mid - 1] + solved_lengths[mid]) / 2)
    else:
        median_steps_to_qed = 0.0

    proof_completion_rate = solved / len(results)
    tactic_accept_rate = accepted / attempted if attempted else 0.0
    branch_efficiency = solved / branches if branches else 0.0
    timeout_rate = timeouts / len(results)
    repair_success_rate = repair_successes / repair_attempts if repair_attempts else 0.0
    premise_hit_rate = premise_hits / premise_checks if premise_checks else 0.0
    budget_failure_rate = budget_failures / len(results)

    score = (
        0.45 * proof_completion_rate
        + 0.20 * tactic_accept_rate
        + 0.15 * branch_efficiency
        + 0.10 * repair_success_rate
        + 0.10 * premise_hit_rate
        - 0.10 * budget_failure_rate
    )

    return SearchMetrics(
        proof_completion_rate=proof_completion_rate,
        tactic_accept_rate=tactic_accept_rate,
        branch_efficiency=branch_efficiency,
        timeout_rate=timeout_rate,
        repair_success_rate=repair_success_rate,
        premise_hit_rate=premise_hit_rate,
        budget_failure_rate=budget_failure_rate,
        median_steps_to_qed=median_steps_to_qed,
        score=max(0.0, score),
    )
