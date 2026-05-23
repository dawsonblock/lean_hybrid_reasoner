from __future__ import annotations

from pathlib import Path

from lean_hybrid_reasoner.cli import make_backend
from lean_hybrid_reasoner.lean_backend.leandojo_v2_client import LeanDojoV2Client
from lean_hybrid_reasoner.lean_backend.lean_cli_backend import LeanCliBackend
from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend


def test_backend_selection_mock(monkeypatch):
    monkeypatch.setenv("LHR_BACKEND", "mock")
    backend = make_backend()
    assert isinstance(backend, MockLeanBackend)


def test_backend_selection_leandojo_alias(monkeypatch):
    monkeypatch.setenv("LHR_BACKEND", "leandojo_v2")
    backend = make_backend()
    assert isinstance(backend, LeanDojoV2Client)

    monkeypatch.setenv("LHR_BACKEND", "leandojo")
    backend2 = make_backend()
    assert isinstance(backend2, LeanDojoV2Client)


def test_backend_selection_lean_cli(monkeypatch, tmp_path: Path):
    lean_file = tmp_path / "Demo.lean"
    lean_file.write_text(
        "theorem demo (n : Nat) : n + 0 = n := by\n  simp\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LHR_BACKEND", "lean_cli")
    monkeypatch.setenv("LHR_LEAN_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("LHR_LEAN_FILE", "Demo.lean")
    backend = make_backend()
    assert isinstance(backend, LeanCliBackend)
