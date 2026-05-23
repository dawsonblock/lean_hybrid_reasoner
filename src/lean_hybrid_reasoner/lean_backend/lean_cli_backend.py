from __future__ import annotations

import re
from pathlib import Path

from lean_hybrid_reasoner.lean_backend.error_parser import parse_lean_error
from lean_hybrid_reasoner.lean_backend.lean_parser import (
    LeanDeclaration,
    parse_lean_declarations,
)
from lean_hybrid_reasoner.lean_backend.sandbox import LeanSandbox
from lean_hybrid_reasoner.schemas.proof_state import LeanProofState
from lean_hybrid_reasoner.schemas.tactic import LeanExecutionResult

_GOAL_RE = re.compile(r"⊢\s*(.+)")


class LeanCliBackend:
    """Best-effort real Lean backend using the local `lake env lean` executable.

    This is not a replacement for LeanDojo-v2's richer proof-state API. It gives
    the repository a practical real-Lean transition path: build a temporary Lean
    file, append a proof prefix plus one candidate tactic, run the Lean kernel,
    and classify the result. It works best for small local Lean files.
    """

    def __init__(
        self,
        project_root: str | Path,
        lean_file: str | Path,
        timeout_seconds: float = 20.0,
    ):
        self.timeout_seconds = timeout_seconds
        self.project_root = Path(project_root).resolve()
        self.lean_file = Path(lean_file)
        if not self.lean_file.is_absolute():
            self.lean_file = (self.project_root / self.lean_file).resolve()
        if not self.lean_file.exists():
            raise FileNotFoundError(f"Lean file not found: {self.lean_file}")
        self._text = self.lean_file.read_text(encoding="utf-8")
        self._lines = self._text.splitlines()
        self._declarations = parse_lean_declarations(self._text, self.lean_file)
        self._sandbox = LeanSandbox.from_environment(timeout_seconds=timeout_seconds)

    def list_theorems(self) -> list[str]:
        return [d.qualified_name for d in self._declarations]

    def list_theorem_infos(self) -> list[dict[str, str | int | None]]:
        return [
            {
                "name": d.qualified_name,
                "file": str(Path(d.file).name),
                "line": d.line,
                "kind": d.kind,
                "statement": d.statement,
                "namespace": d.namespace,
            }
            for d in self._declarations
        ]

    def load_theorem(self, theorem_name: str) -> LeanProofState:
        decl = self._find_declaration(theorem_name)
        return LeanProofState(
            theorem_name=decl.qualified_name,
            theorem_statement=decl.head_for_proof,
            current_goal=decl.statement,
            hypotheses=list(decl.hypotheses),
            open_goals=[decl.statement],
            proof_prefix=[],
            depth=0,
            branch_id="root",
        )

    def initial_state(self, theorem_name: str) -> LeanProofState:
        return self.load_theorem(theorem_name)

    def execute_tactic(self, state: LeanProofState, tactic: str) -> LeanExecutionResult:
        source = self._build_temp_source(state, tactic)
        completed = self._run_lean(source)
        output = (completed.stdout or "") + "\n" + (completed.stderr or "")
        parsed = parse_lean_error(output)

        if completed.returncode == 0:
            return LeanExecutionResult(
                accepted=True,
                solved=True,
                tactic=tactic,
                new_goals=[],
                proof_state_text="no goals",
                new_hypotheses=list(state.hypotheses),
                metadata={
                    "backend": "lean_cli",
                    "returncode": completed.returncode,
                    "timeout_seconds": self.timeout_seconds,
                },
            )

        if parsed.category == "unsolved_goals":
            goals, hyps = self._parse_unsolved_state(output)
            return LeanExecutionResult(
                accepted=True,
                solved=False,
                tactic=tactic,
                error_message=output.strip(),
                new_goals=goals or list(state.open_goals),
                proof_state_text=output.strip(),
                new_hypotheses=hyps or list(state.hypotheses),
                metadata={
                    "backend": "lean_cli",
                    "returncode": completed.returncode,
                    "category": parsed.category,
                    "timeout_seconds": self.timeout_seconds,
                },
            )

        return LeanExecutionResult(
            accepted=False,
            solved=False,
            tactic=tactic,
            error_message=output.strip(),
            new_goals=list(state.open_goals),
            proof_state_text=output.strip() or state.as_prompt_text(),
            new_hypotheses=list(state.hypotheses),
            metadata={
                "backend": "lean_cli",
                "returncode": completed.returncode,
                "category": parsed.category,
                "timeout_seconds": self.timeout_seconds,
            },
        )

    def verify_proof(self, theorem_name: str, proof: list[str]) -> dict[str, object]:
        state = self.load_theorem(theorem_name)
        source = self._build_full_proof_source(state, proof)
        completed = self._run_lean(source)
        return {
            "verified": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": (completed.stdout or "").strip(),
            "stderr": (completed.stderr or "").strip(),
        }

    def _find_declaration(self, theorem_name: str) -> LeanDeclaration:
        for decl in self._declarations:
            if decl.qualified_name == theorem_name or decl.local_name == theorem_name:
                return decl
        raise KeyError(f"Unknown theorem: {theorem_name}")

    def _build_temp_source(self, state: LeanProofState, tactic: str) -> str:
        decl = self._find_declaration(state.theorem_name)
        prefix_source = "\n".join(self._lines[: decl.start_index])
        theorem_head = decl.head_for_proof
        proof_lines = [f"  {t}" for t in [*state.proof_prefix, tactic] if t.strip()]
        return "\n".join([prefix_source, theorem_head, *proof_lines, ""]).strip() + "\n"

    def _run_lean(self, source: str):
        return self._sandbox.run(
            project_root=self.project_root,
            source_file=self.lean_file,
            source_text=source,
        )

    def _build_full_proof_source(self, state: LeanProofState, proof: list[str]) -> str:
        decl = self._find_declaration(state.theorem_name)
        prefix_source = "\n".join(self._lines[: decl.start_index])
        theorem_head = decl.head_for_proof
        proof_lines = [f"  {t}" for t in proof if t.strip()]
        return "\n".join([prefix_source, theorem_head, *proof_lines, ""]).strip() + "\n"

    @staticmethod
    def _parse_unsolved_state(output: str) -> tuple[list[str], list[str]]:
        goals = [m.group(1).strip() for m in _GOAL_RE.finditer(output)]
        hyps: list[str] = []
        for raw in output.splitlines():
            line = raw.strip()
            if " : " in line and not line.startswith("error") and "⊢" not in line:
                hyps.append(line)
        return goals, hyps
