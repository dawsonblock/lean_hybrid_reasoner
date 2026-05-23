from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from lean_hybrid_reasoner.cli import app

runner = CliRunner()


def test_ecosystem_status_runs_without_network(monkeypatch):
    monkeypatch.setenv("LHR_BACKEND", "mock")
    result = runner.invoke(app, ["ecosystem-status"])
    assert result.exit_code == 0
    assert "LeanDojo-v2" in result.stdout
    assert "LeanCopilot" in result.stdout
    assert "LeanAgent" in result.stdout


def test_ecosystem_status_json_includes_docs_status(monkeypatch):
    monkeypatch.setenv("LHR_BACKEND", "mock")
    result = runner.invoke(app, ["ecosystem-status", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["LeanCopilot"]["status"] in {"docs present", "docs missing"}
    assert payload["LeanAgent"]["status"] in {"docs present", "docs missing"}


def test_ecosystem_docs_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs" / "integrations" / "lean_dojo_ecosystem.md").exists()
    assert (root / "docs" / "integrations" / "leancopilot_bridge.md").exists()
    assert (root / "docs" / "integrations" / "leanagent_lifelong_learning.md").exists()
