from __future__ import annotations

from typing import Any

VALID_MIN_QUALITY = {"any", "accepted", "solved"}


def apply_quality_filter(
    examples: list[dict[str, Any]],
    *,
    min_quality: str = "any",
) -> tuple[list[dict[str, Any]], dict[str, int | str]]:
    level = min_quality.strip().lower()
    if level not in VALID_MIN_QUALITY:
        raise ValueError(
            f"Unsupported min_quality={min_quality!r}. Supported: {sorted(VALID_MIN_QUALITY)}"
        )

    if level == "any":
        return list(examples), {
            "min_quality": level,
            "kept": len(examples),
            "dropped": 0,
        }

    filtered: list[dict[str, Any]] = []
    for example in examples:
        accepted = bool(example.get("accepted"))
        solved = bool(example.get("solved"))
        if level == "accepted" and accepted:
            filtered.append(example)
        elif level == "solved" and solved:
            filtered.append(example)

    dropped = len(examples) - len(filtered)
    return filtered, {"min_quality": level, "kept": len(filtered), "dropped": dropped}
