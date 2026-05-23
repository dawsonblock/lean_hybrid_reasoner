from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from lean_hybrid_reasoner.schemas.proof_state import LeanProofState
from lean_hybrid_reasoner.search.budgets import SearchBudget
from lean_hybrid_reasoner.tactics.sanitizer import sanitize_tactic


class DspyMetricResult(BaseModel):
    score: float
    proof_completion: float
    tactic_acceptance: float
    repair_success: float
    branch_efficiency: float
    token_efficiency: float
    penalties: dict[str, float] = Field(default_factory=dict)


_PENALTY_VALUES = {
    "invalid_tactic_format": 0.25,
    "repeated_failed_tactic": 0.20,
    "too_long": 0.15,
    "natural_language_output": 0.25,
    "empty_output": 0.50,
    "backend_error": 0.10,
}


def _penalty_total(penalties: dict[str, float]) -> float:
    return sum(max(v, 0.0) for v in penalties.values())


def build_metric_result(
    *,
    proof_completion: float,
    tactic_acceptance: float,
    repair_success: float,
    branch_efficiency: float,
    token_efficiency: float,
    penalties: dict[str, float] | None = None,
) -> DspyMetricResult:
    penalties = penalties or {}
    score = (
        0.50 * proof_completion
        + 0.25 * tactic_acceptance
        + 0.10 * repair_success
        + 0.10 * branch_efficiency
        + 0.05 * token_efficiency
        - _penalty_total(penalties)
    )
    return DspyMetricResult(
        score=max(score, -1.0),
        proof_completion=proof_completion,
        tactic_acceptance=tactic_acceptance,
        repair_success=repair_success,
        branch_efficiency=branch_efficiency,
        token_efficiency=token_efficiency,
        penalties=penalties,
    )


def tactic_match_or_accept_metric(example: Any, prediction: Any) -> float:
    target = str(
        getattr(example, "target_tactic", None) or example.get("target_tactic") or ""
    ).strip()
    raw = str(
        getattr(prediction, "target_tactic", None)
        or prediction.get("target_tactic")
        or prediction.get("tactic")
        or prediction
    )
    sanitized = sanitize_tactic(raw)
    if not sanitized.valid:
        return 0.0
    if sanitized.cleaned == target and target:
        return 1.0
    return 0.7


def verifier_success_metric(
    example: Any,
    prediction: Any,
    backend: Any,
    engine_config: SearchBudget | None = None,
) -> float:
    theorem_name = str(
        getattr(example, "theorem_name", None) or example.get("theorem_name") or ""
    )
    raw = str(
        getattr(prediction, "target_tactic", None)
        or prediction.get("target_tactic")
        or prediction.get("tactic")
        or prediction
    )

    sanitized = sanitize_tactic(raw)
    if not sanitized.valid:
        reason = sanitized.reason or "invalid_tactic_format"
        key = reason
        if reason == "natural_language":
            key = "natural_language_output"
        elif reason == "empty_output":
            key = "empty_output"
        elif reason == "too_long":
            key = "too_long"
        penalties = {
            key: _PENALTY_VALUES.get(key, _PENALTY_VALUES["invalid_tactic_format"])
        }
        return build_metric_result(
            proof_completion=0.0,
            tactic_acceptance=0.0,
            repair_success=0.0,
            branch_efficiency=0.0,
            token_efficiency=1.0,
            penalties=penalties,
        ).score

    if theorem_name:
        state = backend.load_theorem(theorem_name)
    else:
        statement = str(
            getattr(example, "theorem_statement", None)
            or example.get("theorem_statement")
            or ""
        )
        goal = str(
            getattr(example, "proof_state", None) or example.get("proof_state") or ""
        )
        state = LeanProofState(
            theorem_name="ad_hoc",
            theorem_statement=statement,
            current_goal=goal,
            open_goals=[goal] if goal else [],
        )

    result = backend.execute_tactic(state, sanitized.cleaned)
    if not result.accepted:
        return build_metric_result(
            proof_completion=0.0,
            tactic_acceptance=0.0,
            repair_success=0.0,
            branch_efficiency=0.0,
            token_efficiency=1.0,
            penalties={"backend_error": _PENALTY_VALUES["backend_error"]},
        ).score

    completion = 1.0 if result.solved else 0.5
    return build_metric_result(
        proof_completion=completion,
        tactic_acceptance=1.0,
        repair_success=0.0,
        branch_efficiency=1.0,
        token_efficiency=1.0,
        penalties={},
    ).score
