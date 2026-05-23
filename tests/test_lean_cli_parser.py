from pathlib import Path

from lean_hybrid_reasoner.lean_backend.lean_cli_backend import LeanCliBackend


def test_lean_cli_backend_lists_and_loads_theorem(tmp_path: Path):
    project = tmp_path
    lean_file = project / "Demo.lean"
    lean_file.write_text("theorem demo (n : Nat) : n + 0 = n := by\n  simp\n", encoding="utf-8")
    backend = LeanCliBackend(project, lean_file)
    assert backend.list_theorems() == ["demo"]
    state = backend.load_theorem("demo")
    assert state.theorem_name == "demo"
    assert state.current_goal == "n + 0 = n"
    assert "n : Nat" in state.hypotheses
