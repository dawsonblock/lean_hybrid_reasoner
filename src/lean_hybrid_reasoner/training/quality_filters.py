from __future__ import annotations

from typing import Any

VALID_MIN_QUALITY = {"any", "accepted", "solved", "repair_success"}

_QUALITY_RANK = {
    "any": 0,
    "accepted": 1,
    "solved": 2,
    "repair_success": 3,
}


def _example_quality(example: dict[str, Any]) -> str:
    quality = str(example.get("quality") or "").strip().lower()
    if quality in _QUALITY_RANK:
        return quality
    if example.get("task") == "repair_tactic" and bool(example.get("accepted")):
        return "repair_success"
    if bool(example.get("solved")):
        return "solved"
    if bool(example.get("accepted")):
        return "accepted"
    return "any"


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
    min_rank = _QUALITY_RANK[level]
    for example in examples:
        quality_rank = _QUALITY_RANK[_example_quality(example)]
        if quality_rank >= min_rank:
            filtered.append(example)

    dropped = len(examples) - len(filtered)
    return filtered, {"min_quality": level, "kept": len(filtered), "dropped": dropped}
