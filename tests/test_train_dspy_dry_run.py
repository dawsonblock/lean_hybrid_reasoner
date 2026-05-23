from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from lean_hybrid_reasoner.cli import app

runner = CliRunner()


def _write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_train_dspy_proposer_dry_run_works_without_dspy(tmp_path: Path):
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

    result = runner.invoke(
        app,
        [
            "train-dspy-proposer",
            "--dataset",
            str(pack),
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert '"dry_run": true' in result.stdout.lower()


def test_train_dspy_repairer_dry_run_works_without_dspy(tmp_path: Path):
    pack = tmp_path / "pack"
    _write_jsonl(
        pack / "train.jsonl",
        [
            {
                "task": "repair_tactic",
                "theorem_name": "and_comm_example",
                "goal": "q ∧ p",
                "proof_state_prompt": "Goal: q ∧ p",
                "retrieved_premises": [],
                "failed_tactic": "exact h",
                "tactic": "constructor",
                "accepted": True,
            }
        ],
    )
    _write_jsonl(pack / "dev.jsonl", [])

    result = runner.invoke(
        app,
        [
            "train-dspy-repairer",
            "--dataset",
            str(pack),
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert '"dry_run": true' in result.stdout.lower()


def test_train_dspy_proposer_dry_run_file_inputs_do_not_leak_between_splits(
    tmp_path: Path,
):
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

    result = runner.invoke(
        app,
        [
            "train-dspy-proposer",
            "--dataset",
            str(pack / "train.jsonl"),
            "--devset",
            str(pack / "dev.jsonl"),
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["estimated_train_size"] == 1
    assert payload["estimated_dev_size"] == 1


def test_train_dspy_proposer_dry_run_dir_dataset_with_explicit_devset_uses_train_only(
    tmp_path: Path,
):
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

    result = runner.invoke(
        app,
        [
            "train-dspy-proposer",
            "--dataset",
            str(pack),
            "--devset",
            str(pack / "dev.jsonl"),
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["estimated_train_size"] == 1
    assert payload["estimated_dev_size"] == 1


def test_train_dspy_dry_run_verifier_alias_reports_warning(tmp_path: Path):
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

    result = runner.invoke(
        app,
        [
            "train-dspy-proposer",
            "--dataset",
            str(pack),
            "--metric",
            "verifier",
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "warnings" in payload
    assert "verifier_proxy" in payload["warnings"][0]
