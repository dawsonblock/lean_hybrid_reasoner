from __future__ import annotations

from typer.testing import CliRunner

from lean_hybrid_reasoner.cli import app
from lean_hybrid_reasoner.diagnostics.doctor import run_doctor
from lean_hybrid_reasoner.settings import Settings

runner = CliRunner()


def test_doctor_reports_ecosystem_status_without_crash(tmp_path):
    settings = Settings(
        backend="leandojo_v2",
        trace_path=tmp_path / "traces.jsonl",
        leandojo_repo="demo/repo",
        leandojo_commit="abc123",
    )
    payload = run_doctor(settings)
    assert "backend_availability" in payload
    assert "leandojo_v2" in payload["backend_availability"]
    assert "ecosystem" in payload
    assert "LeanDojo-v2" in payload["ecosystem"]
    assert "LeanCopilot" in payload["ecosystem"]
    assert "LeanAgent" in payload["ecosystem"]


def test_doctor_includes_leandojo_adapter_check(tmp_path):
    settings = Settings(backend="mock", trace_path=tmp_path / "traces.jsonl")
    payload = run_doctor(settings)
    names = {c["name"] for c in payload["checks"]}
    assert "leandojo_v2_adapter_import" in names


def test_doctor_flags_leandojo_backend_selection(tmp_path):
    settings = Settings(backend="leandojo_v2", trace_path=tmp_path / "traces.jsonl")
    payload = run_doctor(settings)
    names = {c["name"] for c in payload["checks"]}
    assert "leandojo_backend_selected" in names


def test_doctor_cli_shows_warn_label_for_warnings(monkeypatch):
    monkeypatch.setenv("LHR_BACKEND", "mock")
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "WARN [warning]" in result.stdout
