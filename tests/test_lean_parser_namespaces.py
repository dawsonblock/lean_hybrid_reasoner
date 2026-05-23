from pathlib import Path

from lean_hybrid_reasoner.lean_backend.lean_parser import parse_lean_declarations


def test_parse_lean_declarations_with_namespaces_and_kinds(tmp_path: Path):
    lean_file = tmp_path / "Namespaced.lean"
    lean_file.write_text(
        """
namespace MyProject
theorem foo (n : Nat) : True := by
  trivial
lemma bar : True := by
  trivial
example : True := by
  trivial
def baz : Nat := 1
end MyProject
""".strip() + "\n",
        encoding="utf-8",
    )

    decls = parse_lean_declarations(lean_file.read_text(encoding="utf-8"), lean_file)
    names = [d.qualified_name for d in decls]
    kinds = [d.kind for d in decls]

    assert "MyProject.foo" in names
    assert "MyProject.bar" in names
    assert "MyProject.baz" in names
    assert any(name.startswith("MyProject.example@L") for name in names)
    assert set(kinds) >= {"theorem", "lemma", "example", "def"}


def test_parse_lean_declarations_multiline_theorem(tmp_path: Path):
    lean_file = tmp_path / "Multiline.lean"
    lean_file.write_text(
        """
namespace A
theorem foo
  (p q : Prop)
  : p -> q -> p := by
  intro hp
  intro hq
  exact hp
end A
""".strip() + "\n",
        encoding="utf-8",
    )

    decls = parse_lean_declarations(lean_file.read_text(encoding="utf-8"), lean_file)
    assert decls[0].qualified_name == "A.foo"
    assert "p -> q -> p" in decls[0].statement
    assert "p q : Prop" in " ".join(decls[0].hypotheses)
