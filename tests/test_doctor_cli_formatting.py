from __future__ import annotations

from typer.testing import CliRunner

import lean_hybrid_reasoner.cli as cli_module


runner = CliRunner()


def test_doctor_cli_renders_ok_warn_fail_labels(monkeypatch):
    def _fake_run_doctor(_settings):
        return {
            "ok": False,
            "backend": "mock",
            "backend_availability": {
                "mock": {"available": True, "reason": "built in"},
            },
            "checks": [
                {
                    "name": "required_ok",
                    "ok": True,
                    "detail": "fine",
                    "severity": "error",
                },
                {
                    "name": "optional_missing",
                    "ok": False,
                    "detail": "missing optional tool",
                    "severity": "warning",
                },
                {
                    "name": "required_failure",
                    "ok": False,
                    "detail": "hard failure",
                    "severity": "error",
                },
            ],
            "ecosystem": {},
            "required_failures": 1,
            "warnings": 1,
            "next_action": "Fix required failures first.",
        }

    monkeypatch.setattr(cli_module, "run_doctor", _fake_run_doctor)

    result = runner.invoke(cli_module.app, ["doctor"])
    assert result.exit_code == 0
    assert "OK [info] required_ok: fine" in result.stdout
    assert "WARN [warning] optional_missing: missing optional tool" in result.stdout
    assert "FAIL [error] required_failure: hard failure" in result.stdout
