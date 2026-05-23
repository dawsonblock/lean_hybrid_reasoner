from __future__ import annotations

from typing import Any
from uuid import uuid4

from lean_hybrid_reasoner.lean_backend.base import LeanBackend
from lean_hybrid_reasoner.retrieval.premise_retriever import PremiseRetriever
from lean_hybrid_reasoner.dspy_modules.heuristic_tactics import (
    HeuristicTacticProposer,
    HeuristicTacticRepairer,
)
from lean_hybrid_reasoner.schemas.branch import ProofBranch
from lean_hybrid_reasoner.schemas.proof_state import LeanProofState
from lean_hybrid_reasoner.schemas.result import ProofRunResult
from lean_hybrid_reasoner.schemas.tactic import LeanExecutionResult, TacticCandidate
from lean_hybrid_reasoner.search.budgets import SearchBudget
from lean_hybrid_reasoner.search.frontier import ProofFrontier
from lean_hybrid_reasoner.search.scoring import score_branch, score_candidate
from lean_hybrid_reasoner.search.tactic_memory import TacticMemory
from lean_hybrid_reasoner.tactics.sanitizer import sanitize_tactic
from lean_hybrid_reasoner.traces.schema import canonicalize_trace_events
from lean_hybrid_reasoner.traces.trace_store import TraceStore


class ProofSearchEngine:
    def __init__(
        self,
        backend: LeanBackend,
        proposer: Any | None = None,
        repairer: Any | None = None,
        retriever: PremiseRetriever | None = None,
        trace_store: TraceStore | None = None,
    ):
        self.backend = backend
        self.proposer = proposer or HeuristicTacticProposer()
        self.repairer = repairer or HeuristicTacticRepairer()
        self.retriever = retriever or PremiseRetriever()
        self.trace_store = trace_store

    def run(
        self, theorem_name: str, budget: SearchBudget | None = None
    ) -> ProofRunResult:
        budget = budget or SearchBudget()
        initial = self.backend.load_theorem(theorem_name)
        frontier = ProofFrontier()
        root = ProofBranch(
            branch_id="root",
            theorem_name=theorem_name,
            proof_prefix=[],
            current_goal=initial.current_goal,
            hypotheses=initial.hypotheses,
            open_goals=initial.open_goals,
            score=0.0,
            depth=0,
            stagnant_steps=0,
        )
        frontier.push(root)

        trace: list[dict] = [
            {"event": "start", "theorem": theorem_name, "budget": budget.model_dump()}
        ]
        branches_explored = 0
        branches_pruned = 0
        tactics_attempted = 0
        accepted_tactics = 0
        failed_tactics = 0
        repair_attempts = 0
        repair_successes = 0
        seen_states: set[str] = set()
        tactic_memory = TacticMemory(
            failure_threshold=budget.tactic_memory_failure_threshold
        )

        while not frontier.empty():
            if budget.timed_out():
                return self._finish(
                    theorem_name,
                    False,
                    "timeout",
                    [],
                    branches_explored,
                    branches_pruned,
                    tactics_attempted,
                    accepted_tactics,
                    failed_tactics,
                    repair_attempts,
                    repair_successes,
                    trace,
                    "time budget exceeded",
                )
            if budget.branches_exceeded(branches_explored):
                return self._finish(
                    theorem_name,
                    False,
                    "budget_exceeded",
                    [],
                    branches_explored,
                    branches_pruned,
                    tactics_attempted,
                    accepted_tactics,
                    failed_tactics,
                    repair_attempts,
                    repair_successes,
                    trace,
                    "branch budget exceeded",
                )
            if budget.tactics_exceeded(tactics_attempted):
                return self._finish(
                    theorem_name,
                    False,
                    "budget_exceeded",
                    [],
                    branches_explored,
                    branches_pruned,
                    tactics_attempted,
                    accepted_tactics,
                    failed_tactics,
                    repair_attempts,
                    repair_successes,
                    trace,
                    "tactic budget exceeded",
                )

            branch = frontier.pop()
            branches_explored += 1

            state = self._state_from_branch(initial, branch)
            state_key = state.compact_key()
            if state_key in seen_states:
                branches_pruned += 1
                trace.append(
                    {
                        "event": "prune_branch",
                        "reason": "duplicate_state",
                        "branch_id": branch.branch_id,
                        "depth": branch.depth,
                        "state_key": state_key,
                    }
                )
                continue
            seen_states.add(state_key)

            if budget.stagnant_exceeded(branch.stagnant_steps):
                branches_pruned += 1
                trace.append(
                    {
                        "event": "dead_branch",
                        "reason": "stagnation_exceeded",
                        "branch": branch.model_dump(),
                    }
                )
                continue

            premises = self.retriever.retrieve(state)
            state.retrieved_premises = premises

            if budget.depth_exceeded(branch.depth):
                branches_pruned += 1
                trace.append(
                    {
                        "event": "dead_branch",
                        "reason": "depth_exceeded",
                        "branch": branch.model_dump(),
                    }
                )
                continue

            candidates = self.proposer.propose(
                state, max_candidates=budget.max_tactics_per_state
            )
            candidates = self._dedupe_candidates(candidates)
            candidates.sort(key=score_candidate, reverse=True)

            trace.append(
                {
                    "event": "expand_branch",
                    "branch_id": branch.branch_id,
                    "parent_branch_id": branch.parent_branch_id,
                    "depth": branch.depth,
                    "stagnant_steps": branch.stagnant_steps,
                    "score": branch.score,
                    "goal": branch.current_goal,
                    "premises": premises,
                    "candidate_tactics": [c.model_dump() for c in candidates],
                }
            )

            for candidate in candidates[: budget.max_tactics_per_state]:
                if budget.timed_out() or budget.tactics_exceeded(tactics_attempted):
                    break
                sanitized = sanitize_tactic(candidate.tactic)
                if not sanitized.valid:
                    trace.append(
                        {
                            "event": "tactic_rejected",
                            "tactic_event_type": "tactic_attempt",
                            "branch_id": branch.branch_id,
                            "raw_tactic": candidate.tactic,
                            "tactic": sanitized.cleaned,
                            "tactic_sanitized": sanitized.cleaned != candidate.tactic,
                            "tactic_sanitizer_warnings": sanitized.warnings,
                            "reason": sanitized.reason,
                        }
                    )
                    continue
                candidate = candidate.model_copy(update={"tactic": sanitized.cleaned})
                if budget.enable_tactic_memory and tactic_memory.should_suppress(
                    state_key, candidate.tactic
                ):
                    trace.append(
                        {
                            "event": "suppress_tactic",
                            "branch_id": branch.branch_id,
                            "state_key": state_key,
                            "tactic": candidate.tactic,
                            "reason": "repeated_failure",
                        }
                    )
                    continue
                tactics_attempted += 1
                result = self.backend.execute_tactic(state, candidate.tactic)
                trace.append(
                    {
                        "event": "execute_tactic",
                        "tactic_event_type": "tactic_attempt",
                        "branch_id": branch.branch_id,
                        "tactic": candidate.tactic,
                        "raw_tactic": candidate.metadata.get(
                            "raw_tactic", candidate.tactic
                        ),
                        "tactic_sanitized": candidate.metadata.get(
                            "tactic_sanitized", False
                        ),
                        "tactic_sanitizer_warnings": candidate.metadata.get(
                            "tactic_sanitizer_warnings", []
                        ),
                        "accepted": result.accepted,
                        "solved": result.solved,
                        "error": result.error_message,
                        "new_goals": result.new_goals,
                        "metadata": result.metadata,
                    }
                )

                if result.accepted:
                    accepted_tactics += 1
                    if budget.enable_tactic_memory:
                        tactic_memory.record_success(state_key, candidate.tactic)
                    new_proof = [*branch.proof_prefix, candidate.tactic]
                    if result.solved:
                        return self._finish(
                            theorem_name,
                            True,
                            "solved",
                            new_proof,
                            branches_explored,
                            branches_pruned,
                            tactics_attempted,
                            accepted_tactics,
                            failed_tactics,
                            repair_attempts,
                            repair_successes,
                            trace,
                        )
                    self._push_child(frontier, branch, result, new_proof)
                    continue

                failed_tactics += 1
                if budget.enable_tactic_memory:
                    tactic_memory.record_failure(state_key, candidate.tactic)
                repairs = self.repairer.repair(
                    state, candidate.tactic, result.error_message
                )
                repairs = [
                    r
                    for r in self._dedupe_candidates(repairs)
                    if r.tactic.strip() != candidate.tactic.strip()
                ]
                for repair_candidate in repairs[: budget.max_repair_attempts]:
                    if budget.timed_out() or budget.tactics_exceeded(tactics_attempted):
                        break
                    repair_sanitized = sanitize_tactic(repair_candidate.tactic)
                    if not repair_sanitized.valid:
                        trace.append(
                            {
                                "event": "tactic_rejected",
                                "tactic_event_type": "tactic_attempt",
                                "branch_id": branch.branch_id,
                                "failed_tactic": candidate.tactic,
                                "raw_tactic": repair_candidate.tactic,
                                "tactic": repair_sanitized.cleaned,
                                "tactic_sanitized": repair_sanitized.cleaned
                                != repair_candidate.tactic,
                                "tactic_sanitizer_warnings": repair_sanitized.warnings,
                                "reason": repair_sanitized.reason,
                            }
                        )
                        continue
                    repair_candidate = repair_candidate.model_copy(
                        update={"tactic": repair_sanitized.cleaned}
                    )
                    repair_attempts += 1
                    tactics_attempted += 1
                    repaired_result = self.backend.execute_tactic(
                        state, repair_candidate.tactic
                    )
                    trace.append(
                        {
                            "event": "repair_tactic",
                            "tactic_event_type": "tactic_attempt",
                            "branch_id": branch.branch_id,
                            "failed_tactic": candidate.tactic,
                            "repair_tactic": repair_candidate.tactic,
                            "raw_tactic": repair_candidate.metadata.get(
                                "raw_tactic", repair_candidate.tactic
                            ),
                            "tactic_sanitized": repair_candidate.metadata.get(
                                "tactic_sanitized", False
                            ),
                            "tactic_sanitizer_warnings": repair_candidate.metadata.get(
                                "tactic_sanitizer_warnings", []
                            ),
                            "accepted": repaired_result.accepted,
                            "solved": repaired_result.solved,
                            "error": repaired_result.error_message,
                            "new_goals": repaired_result.new_goals,
                        }
                    )
                    if repaired_result.accepted:
                        accepted_tactics += 1
                        repair_successes += 1
                        if budget.enable_tactic_memory:
                            tactic_memory.record_success(
                                state_key, repair_candidate.tactic
                            )
                        new_proof = [*branch.proof_prefix, repair_candidate.tactic]
                        if repaired_result.solved:
                            return self._finish(
                                theorem_name,
                                True,
                                "solved",
                                new_proof,
                                branches_explored,
                                branches_pruned,
                                tactics_attempted,
                                accepted_tactics,
                                failed_tactics,
                                repair_attempts,
                                repair_successes,
                                trace,
                            )
                        self._push_child(frontier, branch, repaired_result, new_proof)
                    else:
                        failed_tactics += 1
                        if budget.enable_tactic_memory:
                            tactic_memory.record_failure(
                                state_key, repair_candidate.tactic
                            )

        return self._finish(
            theorem_name,
            False,
            "failed",
            [],
            branches_explored,
            branches_pruned,
            tactics_attempted,
            accepted_tactics,
            failed_tactics,
            repair_attempts,
            repair_successes,
            trace,
            "frontier exhausted",
        )

    def _push_child(
        self,
        frontier: ProofFrontier,
        branch: ProofBranch,
        result: LeanExecutionResult,
        new_proof: list[str],
    ) -> None:
        next_goal = result.new_goals[0] if result.new_goals else branch.current_goal
        old_goals = [g.strip() for g in (branch.open_goals or [branch.current_goal])]
        new_goals = [g.strip() for g in (result.new_goals or [next_goal])]
        stagnant_steps = branch.stagnant_steps + 1 if old_goals == new_goals else 0
        child = ProofBranch(
            branch_id=str(uuid4()),
            theorem_name=branch.theorem_name,
            proof_prefix=new_proof,
            current_goal=next_goal,
            hypotheses=result.new_hypotheses,
            open_goals=result.new_goals,
            score=score_branch(branch, result),
            depth=branch.depth + 1,
            stagnant_steps=stagnant_steps,
            parent_branch_id=branch.branch_id,
        )
        frontier.push(child)

    @staticmethod
    def _dedupe_candidates(candidates: list[TacticCandidate]) -> list[TacticCandidate]:
        seen: set[str] = set()
        out: list[TacticCandidate] = []
        for candidate in candidates:
            key = " ".join(candidate.tactic.strip().split())
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(candidate)
        return out

    def _state_from_branch(
        self, initial: LeanProofState, branch: ProofBranch
    ) -> LeanProofState:
        return LeanProofState(
            theorem_name=branch.theorem_name,
            theorem_statement=initial.theorem_statement,
            current_goal=branch.current_goal,
            hypotheses=list(branch.hypotheses),
            proof_prefix=list(branch.proof_prefix),
            open_goals=list(branch.open_goals),
            depth=branch.depth,
            branch_id=branch.branch_id,
            parent_branch_id=branch.parent_branch_id,
        )

    def _finish(
        self,
        theorem_name,
        solved,
        status,
        proof,
        branches,
        pruned,
        attempted,
        accepted,
        failed,
        repair_attempts,
        repair_successes,
        trace,
        error=None,
    ):
        run_id = f"run_{uuid4().hex}"
        backend_name = type(self.backend).__name__.replace("Backend", "").lower()
        canonical_trace = canonicalize_trace_events(
            trace=trace,
            theorem_name=theorem_name,
            run_id=run_id,
            backend=backend_name,
            config_snapshot_id=None,
        )
        result = ProofRunResult(
            run_id=run_id,
            theorem_name=theorem_name,
            solved=solved,
            status=status,
            proof=proof,
            branches_explored=branches,
            branches_pruned=pruned,
            tactics_attempted=attempted,
            accepted_tactics=accepted,
            failed_tactics=failed,
            repair_attempts=repair_attempts,
            repair_successes=repair_successes,
            trace=canonical_trace,
            error=error,
        )
        if self.trace_store is not None:
            self.trace_store.append(result)
        return result
