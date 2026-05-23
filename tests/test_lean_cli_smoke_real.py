from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from lean_hybrid_reasoner.lean_backend.lean_cli_backend import LeanCliBackend

pytestmark = pytest.mark.lean


@pytest.mark.lean
def test_lean_cli_backend_smoke_real(tmp_path: Path):
    if shutil.which("lean") is None and shutil.which("lake") is None:
        pytest.skip("lean/lake not available")

    lean_file = tmp_path / "Demo.lean"
    lean_file.write_text(
        "theorem demo (n : Nat) : n + 0 = n := by\n  simp\n",
        encoding="utf-8",
    )

    backend = LeanCliBackend(project_root=tmp_path, lean_file=lean_file)
    state = backend.load_theorem("demo")
    result = backend.execute_tactic(state, "simp")

    assert result.accepted is True
