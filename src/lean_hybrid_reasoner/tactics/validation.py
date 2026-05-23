from __future__ import annotations

import re

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


def is_probably_tactic(text: str) -> bool:
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

    return any(re.match(p, candidate) for p in _POSITIVE_PATTERNS)
