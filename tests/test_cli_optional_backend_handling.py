from __future__ import annotations

from typer.testing import CliRunner

from lean_hybrid_reasoner.cli import app

runner = CliRunner()


def test_list_theorems_handles_leandojo_unavailable_without_traceback(monkeypatch):
    monkeypatch.setenv("LHR_BACKEND", "leandojo_v2")
    monkeypatch.delenv("LHR_LEANDOJO_REPO", raising=False)
    result = runner.invoke(app, ["list-theorems"])
    assert result.exit_code == 2
    assert "LeanDojo-v2 backend unavailable." in result.stdout
    assert "Traceback" not in result.stdout


def test_run_handles_leandojo_unavailable_without_traceback(monkeypatch):
    monkeypatch.setenv("LHR_BACKEND", "leandojo_v2")
    monkeypatch.delenv("LHR_LEANDOJO_REPO", raising=False)
    result = runner.invoke(app, ["run", "--theorem", "and_comm_example"])
    assert result.exit_code == 2
    assert "LeanDojo-v2 backend unavailable." in result.stdout
    assert "Traceback" not in result.stdout
