from __future__ import annotations

from dataclasses import dataclass
import re

_POS_RE = re.compile(r":(\d+):(\d+):\s+error:")


@dataclass(frozen=True)
class ParsedLeanError:
    category: str
    message: str
    retryable: bool
    line: int | None = None
    column: int | None = None
    suggestion: str | None = None


def parse_lean_error(message: str | None) -> ParsedLeanError:
    if not message:
        return ParsedLeanError(category="none", message="", retryable=False)

    msg = message.lower()
    pos = _POS_RE.search(message)
    line = int(pos.group(1)) if pos else None
    column = int(pos.group(2)) if pos else None

    if "timeout" in msg or "heartbeat" in msg:
        return ParsedLeanError(
            "timeout",
            message,
            True,
            line=line,
            column=column,
            suggestion="Increase LHR_LEAN_TIMEOUT or narrow tactic candidates.",
        )
    if "unknown identifier" in msg or "unknown constant" in msg:
        return ParsedLeanError(
            "unknown_identifier",
            message,
            True,
            line=line,
            column=column,
            suggestion="Check imports or use a fully qualified identifier.",
        )
    if "type mismatch" in msg:
        return ParsedLeanError(
            "type_mismatch",
            message,
            True,
            line=line,
            column=column,
            suggestion="Adjust tactic to match current goal type.",
        )
    if "unsolved goals" in msg:
        return ParsedLeanError(
            "unsolved_goals",
            message,
            True,
            line=line,
            column=column,
            suggestion="Try splitting goals or applying an introduction tactic first.",
        )
    if "import" in msg and ("error" in msg or "unknown package" in msg):
        return ParsedLeanError(
            "import_error",
            message,
            False,
            line=line,
            column=column,
            suggestion="Check imports and project dependencies.",
        )
    if "environment" in msg and "error" in msg:
        return ParsedLeanError(
            "environment_error",
            message,
            False,
            line=line,
            column=column,
            suggestion="Run `hybrid-proof doctor` and verify Lean/Lake environment.",
        )
    if "tactic" in msg and "failed" in msg:
        return ParsedLeanError(
            "tactic_failed",
            message,
            True,
            line=line,
            column=column,
            suggestion="Try a simpler fallback tactic or repair candidate.",
        )
    if "no goals to be solved" in msg:
        return ParsedLeanError(
            "tactic_failed", message, False, line=line, column=column
        )
    if "invalid" in msg or "syntax" in msg:
        return ParsedLeanError(
            "syntax_error",
            message,
            True,
            line=line,
            column=column,
            suggestion="Check tactic syntax and parentheses.",
        )

    return ParsedLeanError("unknown", message, True, line=line, column=column)
