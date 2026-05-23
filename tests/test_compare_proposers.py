from __future__ import annotations

import json

from typer.testing import CliRunner

from lean_hybrid_reasoner.cli import app

runner = CliRunner()


def test_compare_proposers_heuristic_vs_heuristic_json():
    result = runner.invoke(
        app,
        [
            "compare-proposers",
            "--left",
            "heuristic",
            "--right",
            "heuristic",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "left" in payload
    assert "right" in payload
    assert "completion_rate" in payload["left"]
    assert "tactic_acceptance_rate" in payload["right"]


def test_compare_proposers_dspy_unavailable_clean_error():
    result = runner.invoke(
        app,
        ["compare-proposers", "--left", "heuristic", "--right", "dspy"],
    )
    assert result.exit_code == 2
    assert "falling back to heuristic proposer" not in result.stdout
    assert 'Install with: pip install -e ".[llm]"' in result.stdout
