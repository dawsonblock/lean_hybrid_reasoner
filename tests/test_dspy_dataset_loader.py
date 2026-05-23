from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from lean_hybrid_reasoner.dspy_modules.dataset import (
    load_repair_examples_file,
    load_repair_examples,
    load_tactic_examples_file,
    load_tactic_examples,
    to_dspy_examples,
)


def _write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_load_tactic_examples_filters_invalid(tmp_path: Path):
    pack = tmp_path / "pack"
    _write_jsonl(
        pack / "train.jsonl",
        [
            {
                "task": "suggest_tactic",
                "theorem_name": "t1",
                "goal": "n + 0 = n",
                "proof_state_prompt": "Goal: n + 0 = n",
                "retrieved_premises": [],
                "tactic": "```lean\nsimp\n```",
                "accepted": True,
                "run_index": 0,
                "event_index": 1,
            },
            {
                "task": "suggest_tactic",
                "theorem_name": "t2",
                "goal": "p -> p",
                "proof_state_prompt": "Goal: p -> p",
                "retrieved_premises": [],
                "tactic": "Here is the proof",
                "accepted": True,
            },
            {
                "task": "suggest_tactic",
                "theorem_name": "",
                "goal": "",
                "proof_state_prompt": "",
                "retrieved_premises": [],
                "tactic": "simp",
                "accepted": True,
            },
        ],
    )
    _write_jsonl(pack / "dev.jsonl", [])

    examples = load_tactic_examples(pack)
    assert len(examples) == 1
    assert examples[0].target_tactic == "simp"
    assert examples[0].source_trace_id == "run_0_event_1"


def test_load_repair_examples_extracts_failed_tactic(tmp_path: Path):
    pack = tmp_path / "pack"
    _write_jsonl(
        pack / "train.jsonl",
        [
            {
                "task": "repair_tactic",
                "theorem_name": "t1",
                "goal": "p /\\ q",
                "proof_state_prompt": "Goal: p /\\ q",
                "retrieved_premises": [],
                "failed_tactic": "exact h",
                "tactic": "constructor",
                "accepted": True,
            }
        ],
    )
    _write_jsonl(pack / "dev.jsonl", [])

    examples = load_repair_examples(pack)
    assert len(examples) == 1
    assert examples[0].failed_tactics == ["exact h"]
    assert examples[0].quality == "repair_success"


def test_to_dspy_examples_fails_cleanly_when_dspy_missing(tmp_path: Path, monkeypatch):
    pack = tmp_path / "pack"
    _write_jsonl(
        pack / "train.jsonl",
        [
            {
                "task": "suggest_tactic",
                "theorem_name": "t1",
                "goal": "n + 0 = n",
                "proof_state_prompt": "Goal: n + 0 = n",
                "retrieved_premises": [],
                "tactic": "simp",
                "accepted": True,
            }
        ],
    )
    _write_jsonl(pack / "dev.jsonl", [])
    examples = load_tactic_examples(pack)

    monkeypatch.setitem(sys.modules, "dspy", None)
    with pytest.raises(RuntimeError, match="Install with"):
        to_dspy_examples(examples)


def test_load_tactic_examples_file_does_not_read_sibling_dev(tmp_path: Path):
    pack = tmp_path / "pack"
    _write_jsonl(
        pack / "train.jsonl",
        [
            {
                "task": "suggest_tactic",
                "theorem_name": "train_only",
                "goal": "n + 0 = n",
                "proof_state_prompt": "Goal: n + 0 = n",
                "retrieved_premises": [],
                "tactic": "simp",
                "accepted": True,
            }
        ],
    )
    _write_jsonl(
        pack / "dev.jsonl",
        [
            {
                "task": "suggest_tactic",
                "theorem_name": "dev_only",
                "goal": "p -> p",
                "proof_state_prompt": "Goal: p -> p",
                "retrieved_premises": [],
                "tactic": "intro h",
                "accepted": True,
            }
        ],
    )

    examples = load_tactic_examples_file(pack / "train.jsonl")
    assert len(examples) == 1
    assert examples[0].theorem_name == "train_only"


def test_load_repair_examples_file_does_not_read_sibling_train(tmp_path: Path):
    pack = tmp_path / "pack"
    _write_jsonl(
        pack / "train.jsonl",
        [
            {
                "task": "repair_tactic",
                "theorem_name": "train_only",
                "goal": "q /\\ p",
                "proof_state_prompt": "Goal: q /\\ p",
                "retrieved_premises": [],
                "failed_tactic": "exact h",
                "tactic": "constructor",
                "accepted": True,
            }
        ],
    )
    _write_jsonl(
        pack / "dev.jsonl",
        [
            {
                "task": "repair_tactic",
                "theorem_name": "dev_only",
                "goal": "q /\\ p",
                "proof_state_prompt": "Goal: q /\\ p",
                "retrieved_premises": [],
                "failed_tactic": "exact h",
                "tactic": "constructor",
                "accepted": True,
            }
        ],
    )

    examples = load_repair_examples_file(pack / "dev.jsonl")
    assert len(examples) == 1
    assert examples[0].theorem_name == "dev_only"
