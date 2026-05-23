from __future__ import annotations

import re
from typing import Literal

_NEGATIVE_PATTERNS = [
    r"\bhere is\b",
    r"\bi would\b",
    r"\bwe (can|should|will)\b",
    r"\bfirst,\b",
    r"\bbecause\b",
    r"\bthe best tactic is\b",
]

_POSITIVE_PATTERNS = [
    r"^simp(?:\s|$)",
    r"^rfl$",
    r"^trivial$",
    r"^assumption$",
    r"^intro(?:\s+\S+)?$",
    r"^intros(?:\s+\S+)*$",
    r"^exact\s+.+$",
    r"^apply\s+.+$",
    r"^constructor$",
    r"^omega$",
    r"^linarith$",
    r"^ring$",
    r"^aesop(?:\s|$)",
    r"^rw\s+.+$",
    r"^have\s+.+$",
    r"^cases\s+.+$",
    r"^induction\s+.+$",
]

_PERMISSIVE_EXTRA_PATTERNS = [
    r"^simp_all(?:\s|$)",
    r"^norm_num(?:\s|$)",
    r"^nlinarith(?:\s|$)",
    r"^tauto(?:\s|$)",
    r"^omega\s+at\s+.+$",
    r"^subst\s+.+$",
    r"^rcases\s+.+$",
    r"^obtain\s+.+$",
    r"^rename_i(?:\s+.+)?$",
    r"^refine\s+.+$",
    r"^calc(?:\s|$)",
    r"^all_goals\s+.+$",
    r"^constructor\s*<;>\s*.+$",
    r"^exact\s+fun\s+.+=>\s+.+$",
    r"^·\s*.+$",
]


def is_probably_tactic(text: str, *, mode: Literal["strict", "permissive"] = "strict") -> bool:
    candidate = (text or "").strip()
    if not candidate:
        return False

    if "\n" in candidate:
        return False

    lower = candidate.lower()
    if any(re.search(p, lower) for p in _NEGATIVE_PATTERNS):
        return False

    # Simple sentence-like natural language guard.
    if lower.endswith(".") and len(candidate.split()) > 4:
        return False

    patterns = _POSITIVE_PATTERNS
    if mode == "permissive":
        patterns = [*patterns, *_PERMISSIVE_EXTRA_PATTERNS]
    return any(re.match(p, candidate) for p in patterns)
