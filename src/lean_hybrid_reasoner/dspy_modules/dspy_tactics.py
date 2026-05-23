from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lean_hybrid_reasoner.cli_errors import InvalidCompiledProgramError
from lean_hybrid_reasoner.dspy_modules.manifest import validate_compiled_program_dir
from lean_hybrid_reasoner.schemas.proof_state import LeanProofState
from lean_hybrid_reasoner.schemas.tactic import TacticCandidate
from lean_hybrid_reasoner.tactics.sanitizer import sanitize_tactic


class DSPyUnavailable(RuntimeError):
    pass


def _normalize_candidate_items(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if hasattr(raw, "model_dump"):
        raw = raw.model_dump()
    if isinstance(raw, dict):
        raw = (
            raw.get("tactics")
            or raw.get("tactic_candidates")
            or raw.get("items")
            or [raw]
        )
    if isinstance(raw, str):
        stripped = raw.strip()
        if stripped.startswith("[") or stripped.startswith("{"):
            try:
                decoded = json.loads(stripped)
                return _normalize_candidate_items(decoded)
            except Exception:
                pass
        out: list[Any] = []
        for line in stripped.splitlines():
            line = line.strip()
            if not line:
                continue
            if line[0].isdigit() and "." in line:
                line = line.split(".", 1)[1].strip()
            out.append(line.strip("- \t"))
        return out
    if isinstance(raw, list):
        out: list[Any] = []
        for item in raw:
            if isinstance(item, dict):
                out.append(item)
            else:
                out.append(str(item).strip())
        return [x for x in out if x and (not isinstance(x, str) or x.strip())]
    return [str(raw).strip()]


def normalize_tactic_candidates(raw: Any) -> list[str]:
    items = _normalize_candidate_items(raw)
    out: list[str] = []
    for item in items:
        if isinstance(item, dict):
            out.append(str(item.get("tactic") or item.get("text") or "").strip())
        else:
            out.append(str(item).strip())
    return [x for x in out if x]


def _normalise_tactic_list(
    raw: Any, *, max_candidates: int, source: str
) -> list[TacticCandidate]:
    """Convert common DSPy output shapes into tactic candidates.

    DSPy programs may return a list, newline-separated string, JSON string, or a
    Pydantic-like object. This function keeps the adapter tolerant while still
    returning the narrow internal contract used by the search engine.
    """
    if raw is None:
        return []

    if hasattr(raw, "model_dump"):
        raw = raw.model_dump()

    raw = _normalize_candidate_items(raw)

    out: list[TacticCandidate] = []
    seen: set[str] = set()
    for item in raw:
        if hasattr(item, "model_dump"):
            item = item.model_dump()
        if isinstance(item, dict):
            raw_tactic = str(item.get("tactic") or item.get("text") or "").strip()
            confidence = float(item.get("confidence", 0.5))
            rationale = str(item.get("rationale", f"{source} tactic"))
            premises = list(item.get("required_premises", []))
        else:
            raw_tactic = str(item).strip()
            confidence = 0.5
            rationale = f"{source} tactic"
            premises = []
        sanitized = sanitize_tactic(raw_tactic)
        if not sanitized.valid:
            continue
        tactic = sanitized.cleaned
        if tactic in seen:
            continue
        seen.add(tactic)
        out.append(
            TacticCandidate(
                tactic=tactic,
                confidence=max(0.0, min(confidence, 1.0)),
                rationale=rationale,
                required_premises=premises,
                metadata={
                    "source": source,
                    "raw_tactic": raw_tactic,
                    "tactic_sanitized": tactic != raw_tactic,
                    "tactic_sanitizer_warnings": sanitized.warnings,
                },
            )
        )
    return out[:max_candidates]


class DSPyTacticProposer:
    """Optional DSPy-backed tactic proposer.

    The adapter is lazy-imported so the package remains runnable without DSPy.
    Pass a compiled DSPy program, or use `from_compiled(path)` to load one when
    your local DSPy setup supports serialization.
    """

    def __init__(self, program=None):
        try:
            import dspy  # noqa: F401
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise DSPyUnavailable(
                "Install with `pip install -e .[llm]` to use DSPyTacticProposer."
            ) from exc
        self.program = program

    @classmethod
    def from_compiled(
        cls, path: str | Path
    ) -> "DSPyTacticProposer":  # pragma: no cover - optional dependency path
        try:
            import dspy
        except Exception as exc:
            raise DSPyUnavailable(
                "Install with `pip install -e .[llm]` to load compiled DSPy programs."
            ) from exc
        load_path = Path(path)
        if load_path.is_dir():
            validate_compiled_program_dir(load_path)
            if (load_path / "dspy_program").exists():
                load_path = load_path / "dspy_program"
            elif (load_path / "program.json").exists():
                raise InvalidCompiledProgramError(
                    "Compiled proposer artifact does not contain a DSPy-serializable program payload."
                )
        program = dspy.load(str(load_path))
        return cls(program=program)

    def propose(
        self, state: LeanProofState, max_candidates: int = 8
    ) -> list[TacticCandidate]:
        if self.program is None:
            raise DSPyUnavailable("No compiled DSPy tactic program was supplied.")
        prediction = self.program(
            theorem_statement=state.theorem_statement,
            proof_state=state.as_prompt_text(),
            retrieved_premises=state.retrieved_premises,
        )
        raw = getattr(prediction, "tactic_candidates", prediction)
        return _normalise_tactic_list(
            raw, max_candidates=max_candidates, source="dspy_proposer"
        )


class DSPyTacticRepairer:
    """Optional DSPy-backed repairer.

    It implements the same `.repair(state, failed_tactic, error_message)` contract
    as `HeuristicTacticRepairer`, so it can be swapped into `ProofSearchEngine`
    without changing the search loop.
    """

    def __init__(self, program=None):
        try:
            import dspy  # noqa: F401
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise DSPyUnavailable(
                "Install with `pip install -e .[llm]` to use DSPyTacticRepairer."
            ) from exc
        self.program = program

    @classmethod
    def from_compiled(
        cls, path: str | Path
    ) -> "DSPyTacticRepairer":  # pragma: no cover - optional dependency path
        try:
            import dspy
        except Exception as exc:
            raise DSPyUnavailable(
                "Install with `pip install -e .[llm]` to load compiled DSPy programs."
            ) from exc
        load_path = Path(path)
        if load_path.is_dir():
            validate_compiled_program_dir(load_path)
            if (load_path / "dspy_program").exists():
                load_path = load_path / "dspy_program"
            elif (load_path / "program.json").exists():
                raise InvalidCompiledProgramError(
                    "Compiled repairer artifact does not contain a DSPy-serializable program payload."
                )
        program = dspy.load(str(load_path))
        return cls(program=program)

    def repair(
        self, state: LeanProofState, failed_tactic: str, error_message: str | None
    ) -> list[TacticCandidate]:
        if self.program is None:
            raise DSPyUnavailable("No compiled DSPy repair program was supplied.")
        prediction = self.program(
            theorem_statement=state.theorem_statement,
            proof_state=state.as_prompt_text(),
            failed_tactic=failed_tactic,
            lean_error=error_message or "",
        )
        raw = getattr(prediction, "repaired_tactic", prediction)
        repaired = _normalise_tactic_list(raw, max_candidates=4, source="dspy_repairer")
        return [
            c
            for c in repaired
            if c.tactic.strip() and c.tactic.strip() != failed_tactic.strip()
        ]
