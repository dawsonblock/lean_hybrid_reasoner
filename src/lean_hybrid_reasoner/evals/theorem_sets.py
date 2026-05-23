from __future__ import annotations

from pydantic import BaseModel


class TheoremExample(BaseModel):
    theorem_name: str
    expected_solved: bool
    complexity: int = 1


STARTER_THEOREMS = [
    TheoremExample(theorem_name="add_zero_example", expected_solved=True, complexity=1),
    TheoremExample(theorem_name="zero_add_example", expected_solved=True, complexity=1),
    TheoremExample(theorem_name="and_comm_example", expected_solved=True, complexity=2),
    TheoremExample(theorem_name="impossible_example", expected_solved=False, complexity=1),
]
