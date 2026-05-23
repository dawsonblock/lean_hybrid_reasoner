from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from lean_hybrid_reasoner.tactics.validation import is_probably_tactic


class TacticSanitizationResult(BaseModel):
    original: str
    cleaned: str
    valid: bool
    reason: str | None = None
    warnings: list[str] = Field(default_factory=list)


_PREFIX_RE = re.compile(r"^(tactic|use|try|suggestion)\s*:\s*", re.IGNORECASE)
_LEADIN_RE = re.compile(
    r"^(?:the\s+best\s+tactic\s+is|you\s+should\s+use)\s*:\s*",
    re.IGNORECASE,
)
_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s*")


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _strip_quotes(text: str) -> str:
    out = text.strip()
    quote_pairs = [('"', '"'), ("'", "'"), ("`", "`")]
    for left, right in quote_pairs:
        if out.startswith(left) and out.endswith(right) and len(out) >= 2:
            out = out[1:-1].strip()
    return out


def sanitize_tactic(
    text: str,
    max_length: int = 240,
    *,
    mode: Literal["strict", "permissive"] = "strict",
    allow_multiline: bool = False,
    allow_sorry: bool = False,
    allow_admit: bool = False,
) -> TacticSanitizationResult:
    original = text or ""
    warnings: list[str] = []

    cleaned = _strip_code_fence(original)
    cleaned = _strip_quotes(cleaned)
    cleaned = cleaned.strip()

    if not cleaned:
        return TacticSanitizationResult(
            original=original,
            cleaned="",
            valid=False,
            reason="empty_output",
            warnings=warnings,
        )

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    lines = [_BULLET_RE.sub("", line).strip() for line in lines]
    lines = [_PREFIX_RE.sub("", line).strip() for line in lines]
    lines = [_LEADIN_RE.sub("", line).strip() for line in lines]
    lines = [line for line in lines if line]

    if not lines:
        return TacticSanitizationResult(
            original=original,
            cleaned="",
            valid=False,
            reason="empty_output",
            warnings=warnings,
        )

    if not allow_multiline and len(lines) > 1:
        # Keep first line but warn. If lines appear unrelated, reject.
        if any(is_probably_tactic(line, mode=mode) for line in lines[1:]):
            return TacticSanitizationResult(
                original=original,
                cleaned=lines[0],
                valid=False,
                reason="multiple_suggestions",
                warnings=warnings,
            )
        warnings.append("truncated_multiline_output")

    cleaned = lines[0]

    if len(cleaned) > max_length:
        return TacticSanitizationResult(
            original=original,
            cleaned=cleaned,
            valid=False,
            reason="too_long",
            warnings=warnings,
        )

    lower = cleaned.lower()
    if not allow_sorry and "sorry" in lower:
        return TacticSanitizationResult(
            original=original,
            cleaned=cleaned,
            valid=False,
            reason="contains_sorry",
            warnings=warnings,
        )

    if not allow_admit and "admit" in lower:
        return TacticSanitizationResult(
            original=original,
            cleaned=cleaned,
            valid=False,
            reason="contains_admit",
            warnings=warnings,
        )

    if not is_probably_tactic(cleaned, mode=mode):
        return TacticSanitizationResult(
            original=original,
            cleaned=cleaned,
            valid=False,
            reason="natural_language",
            warnings=warnings,
        )

    return TacticSanitizationResult(
        original=original,
        cleaned=cleaned,
        valid=True,
        reason=None,
        warnings=warnings,
    )
