from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from lean_hybrid_reasoner.tactics.sanitizer import sanitize_tactic


class DspyTacticExample(BaseModel):
    theorem_name: str
    theorem_statement: str
    proof_state: str
    retrieved_premises: list[str] = Field(default_factory=list)
    failed_tactics: list[str] = Field(default_factory=list)
    target_tactic: str
    source_trace_id: str | None = None
    quality: str


def _resolve_pack_paths(path: Path) -> tuple[Path, Path]:
    if path.is_dir():
        return path / "train.jsonl", path / "dev.jsonl"
    if path.name == "train.jsonl":
        return path, path.with_name("dev.jsonl")
    if path.name == "dev.jsonl":
        return path.with_name("train.jsonl"), path
    raise FileNotFoundError(
        f"Expected dataset pack directory or train/dev jsonl path: {path}"
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _quality_for_row(row: dict[str, Any], *, repair: bool) -> str:
    if repair and row.get("accepted"):
        return "repair_success"
    if row.get("solved"):
        return "solved"
    if row.get("accepted"):
        return "accepted"
    return "rejected"


def _normalize_rows(
    rows: list[dict[str, Any]], *, repair: bool
) -> list[DspyTacticExample]:
    examples: list[DspyTacticExample] = []
    for row in rows:
        if repair and row.get("task") != "repair_tactic":
            continue
        if not repair and row.get("task") != "suggest_tactic":
            continue

        proof_state = str(row.get("proof_state_prompt") or "").strip()
        target = str(row.get("tactic") or "").strip()
        theorem_name = str(row.get("theorem_name") or "").strip()
        theorem_statement = str(
            row.get("theorem_statement") or row.get("goal") or ""
        ).strip()

        if not proof_state or not target or not theorem_name:
            continue

        sanitized_target = sanitize_tactic(target)
        if not sanitized_target.valid:
            continue

        failed_tactics: list[str] = []
        if repair:
            failed = str(row.get("failed_tactic") or "").strip()
            if failed:
                failed_tactics.append(failed)

        quality = str(row.get("quality") or _quality_for_row(row, repair=repair))
        examples.append(
            DspyTacticExample(
                theorem_name=theorem_name,
                theorem_statement=theorem_statement,
                proof_state=proof_state,
                retrieved_premises=list(row.get("retrieved_premises") or []),
                failed_tactics=list(dict.fromkeys(failed_tactics)),
                target_tactic=sanitized_target.cleaned,
                source_trace_id=(
                    f"run_{row.get('run_index')}_event_{row.get('event_index')}"
                    if row.get("run_index") is not None
                    and row.get("event_index") is not None
                    else None
                ),
                quality=quality,
            )
        )
    return examples


def _load_examples(path: Path, *, repair: bool) -> list[DspyTacticExample]:
    train_path, dev_path = _resolve_pack_paths(path)
    rows = [*_read_jsonl(train_path), *_read_jsonl(dev_path)]
    return _normalize_rows(rows, repair=repair)


def load_tactic_examples(path: Path) -> list[DspyTacticExample]:
    return _load_examples(path, repair=False)


def load_repair_examples(path: Path) -> list[DspyTacticExample]:
    return _load_examples(path, repair=True)


def to_dspy_examples(examples: list[DspyTacticExample]) -> list[Any]:
    try:
        import dspy
    except Exception as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError(
            'DSPy is not installed. Install with: pip install -e ".[llm]"'
        ) from exc
    if dspy is None or not hasattr(dspy, "Example"):
        raise RuntimeError(
            'DSPy is not installed. Install with: pip install -e ".[llm]"'
        )

    out: list[Any] = []
    for example in examples:
        payload = {
            "theorem_name": example.theorem_name,
            "theorem_statement": example.theorem_statement,
            "proof_state": example.proof_state,
            "retrieved_premises": example.retrieved_premises,
            "failed_tactics": example.failed_tactics,
            "target_tactic": example.target_tactic,
            "quality": example.quality,
            "source_trace_id": example.source_trace_id,
        }
        item = dspy.Example(**payload)
        if hasattr(item, "with_inputs"):
            item = item.with_inputs(
                "theorem_statement",
                "proof_state",
                "retrieved_premises",
                "failed_tactics",
            )
        out.append(item)
    return out
