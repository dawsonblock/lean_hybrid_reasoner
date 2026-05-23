from __future__ import annotations

import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from lean_hybrid_reasoner.cli import app

runner = CliRunner()


def _write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_train_dspy_proposer_without_dspy_gives_install_hint(
    tmp_path: Path, monkeypatch
):
    pack = tmp_path / "pack"
    _write_jsonl(
        pack / "train.jsonl",
        [
            {
                "task": "suggest_tactic",
                "theorem_name": "add_zero_example",
                "goal": "n + 0 = n",
                "proof_state_prompt": "Goal: n + 0 = n",
                "retrieved_premises": [],
                "tactic": "simp",
                "accepted": True,
            }
        ],
    )
    _write_jsonl(pack / "dev.jsonl", [])

    monkeypatch.setitem(sys.modules, "dspy", None)
    result = runner.invoke(app, ["train-dspy-proposer", "--dataset", str(pack)])
    assert result.exit_code == 2
    assert 'Install with: pip install -e ".[llm]"' in result.stdout
    assert "Traceback" not in result.stdout


def test_train_dspy_handles_missing_dataset_cleanly(tmp_path: Path):
    missing = tmp_path / "does_not_exist"
    result = runner.invoke(app, ["train-dspy-proposer", "--dataset", str(missing)])
    assert result.exit_code == 2
    assert "Dataset path not found" in result.stdout


def test_train_dspy_repairer_empty_examples_has_actionable_message(tmp_path: Path):
    pack = tmp_path / "pack"
    _write_jsonl(
        pack / "train.jsonl",
        [
            {
                "task": "suggest_tactic",
                "theorem_name": "add_zero_example",
                "goal": "n + 0 = n",
                "proof_state_prompt": "Goal: n + 0 = n",
                "retrieved_premises": [],
                "tactic": "simp",
                "accepted": True,
            }
        ],
    )
    _write_jsonl(pack / "dev.jsonl", [])

    result = runner.invoke(app, ["train-dspy-repairer", "--dataset", str(pack)])
    assert result.exit_code == 2
    assert "No valid repair examples found" in result.stdout
    assert "--include-failures" in result.stdout
