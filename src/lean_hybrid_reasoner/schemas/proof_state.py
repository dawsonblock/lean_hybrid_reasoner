from __future__ import annotations

from pydantic import BaseModel, Field


def _truncate_middle(text: str, max_chars: int) -> str:
    """Keep both ends of long proof-state text.

    Lean states can grow quickly. For LLM prompting, the newest context is often at
    the end, while theorem identity and early hypotheses at the beginning remain
    useful. Middle truncation preserves both.
    """
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    keep_left = max_chars // 2
    keep_right = max_chars - keep_left
    omitted = len(text) - max_chars
    return f"{text[:keep_left]}\n... <truncated {omitted} chars> ...\n{text[-keep_right:]}"


class LeanProofState(BaseModel):
    theorem_name: str
    theorem_statement: str
    current_goal: str
    hypotheses: list[str] = Field(default_factory=list)
    proof_prefix: list[str] = Field(default_factory=list)
    open_goals: list[str] = Field(default_factory=list)
    retrieved_premises: list[str] = Field(default_factory=list)
    depth: int = 0
    branch_id: str = "root"
    parent_branch_id: str | None = None

    def as_prompt_text(
        self,
        *,
        max_section_chars: int = 3_000,
        max_total_chars: int = 12_000,
    ) -> str:
        """Render a bounded prompt representation of the proof state.

        This is intentionally deterministic so traces are reproducible and LLM
        inputs do not silently exceed context limits as proof branches grow.
        """
        hyps = "\n".join(self.hypotheses) if self.hypotheses else "(none)"
        goals = "\n".join(self.open_goals) if self.open_goals else self.current_goal
        prefix = "\n".join(self.proof_prefix) if self.proof_prefix else "(empty)"
        premises = "\n".join(self.retrieved_premises) if self.retrieved_premises else "(none)"

        sections = [
            ("Theorem", self.theorem_name),
            ("Statement", self.theorem_statement),
            ("Hypotheses", _truncate_middle(hyps, max_section_chars)),
            ("Goals", _truncate_middle(goals, max_section_chars)),
            ("Proof prefix", _truncate_middle(prefix, max_section_chars)),
            ("Retrieved premises", _truncate_middle(premises, max_section_chars)),
        ]
        rendered = "\n".join(f"{name}:\n{text}" for name, text in sections)
        return _truncate_middle(rendered, max_total_chars)

    def compact_key(self) -> str:
        """Stable key for duplicate/stagnant state detection."""
        goals = "||".join(g.strip() for g in self.open_goals or [self.current_goal])
        hyps = "||".join(sorted(h.strip() for h in self.hypotheses))
        return f"{self.theorem_name}::{goals}::{hyps}"
