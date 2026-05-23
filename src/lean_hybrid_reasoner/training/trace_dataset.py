from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from lean_hybrid_reasoner.traces.dashboard import load_trace_records


def _state_prompt_from_expand(expand: dict[str, Any]) -> str:
    premises = expand.get("premises") or []
    premise_text = "\n".join(str(p) for p in premises) if premises else "(none)"
    candidates = expand.get("candidate_tactics") or []
    candidate_text = "\n".join(str(c.get("tactic", c)) for c in candidates) if candidates else "(none)"
    return (
        f"Goal:\n{expand.get('goal', '')}\n\n"
        f"Depth: {expand.get('depth', 0)}\n"
        f"Stagnant steps: {expand.get('stagnant_steps', 0)}\n\n"
        f"Retrieved premises:\n{premise_text}\n\n"
        f"Candidate tactics already considered by baseline:\n{candidate_text}"
    )


def extract_training_examples(
    records: Iterable[dict[str, Any]],
    *,
    include_failures: bool = False,
    include_repairs: bool = True,
) -> list[dict[str, Any]]:
    """Extract DSPy/fine-tuning style examples from proof traces.

    The exporter intentionally uses only data already present in trace records.
    It does not claim to reconstruct the full Lean state. For high-quality model
    training, the LeanDojo backend should later add exact state snapshots to each
    trace event. This function still provides useful bootstrap data for tactic
    suggestion and error-conditioned repair.
    """
    examples: list[dict[str, Any]] = []

    for run_idx, record in enumerate(records):
        theorem = record.get("theorem_name")
        branch_context: dict[str, dict[str, Any]] = {}

        for event_idx, event in enumerate(record.get("trace", [])):
            event_name = event.get("event")
            branch_id = event.get("branch_id")

            if event_name == "expand_branch" and branch_id:
                branch_context[branch_id] = event
                continue

            if event_name == "execute_tactic" and branch_id:
                accepted = bool(event.get("accepted"))
                if not accepted and not include_failures:
                    continue
                expand = branch_context.get(branch_id, {})
                examples.append(
                    {
                        "task": "suggest_tactic",
                        "theorem_name": theorem,
                        "run_index": run_idx,
                        "event_index": event_idx,
                        "branch_id": branch_id,
                        "proof_state_prompt": _state_prompt_from_expand(expand),
                        "goal": expand.get("goal", ""),
                        "retrieved_premises": expand.get("premises", []),
                        "tactic": event.get("tactic", ""),
                        "accepted": accepted,
                        "solved": bool(event.get("solved")),
                        "error": event.get("error"),
                        "source": "execute_tactic",
                    }
                )
                continue

            if include_repairs and event_name == "repair_tactic" and branch_id:
                accepted = bool(event.get("accepted"))
                if not accepted and not include_failures:
                    continue
                expand = branch_context.get(branch_id, {})
                examples.append(
                    {
                        "task": "repair_tactic",
                        "theorem_name": theorem,
                        "run_index": run_idx,
                        "event_index": event_idx,
                        "branch_id": branch_id,
                        "proof_state_prompt": _state_prompt_from_expand(expand),
                        "goal": expand.get("goal", ""),
                        "retrieved_premises": expand.get("premises", []),
                        "failed_tactic": event.get("failed_tactic", ""),
                        "lean_error": event.get("error"),
                        "tactic": event.get("repair_tactic", ""),
                        "accepted": accepted,
                        "solved": bool(event.get("solved")),
                        "source": "repair_tactic",
                    }
                )

    return examples


def write_training_jsonl(
    trace_path: str | Path,
    output_path: str | Path,
    *,
    include_failures: bool = False,
    include_repairs: bool = True,
) -> Path:
    records = load_trace_records(trace_path)
    examples = extract_training_examples(records, include_failures=include_failures, include_repairs=include_repairs)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    return output


def summarize_training_examples(examples: Iterable[dict[str, Any]]) -> dict[str, Any]:
    examples = list(examples)
    by_task = Counter(e.get("task") for e in examples)
    accepted = sum(1 for e in examples if e.get("accepted"))
    solved = sum(1 for e in examples if e.get("solved"))
    by_theorem = Counter(e.get("theorem_name") for e in examples)
    return {
        "examples": len(examples),
        "accepted": accepted,
        "solved": solved,
        "accept_rate": accepted / len(examples) if examples else 0.0,
        "solve_rate": solved / len(examples) if examples else 0.0,
        "by_task": dict(by_task),
        "by_theorem": dict(by_theorem),
    }
