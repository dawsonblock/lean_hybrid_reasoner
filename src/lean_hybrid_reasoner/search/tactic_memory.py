from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TacticMemoryRecord:
    state_key: str
    failed_tactics: set[str] = field(default_factory=set)
    accepted_tactics: set[str] = field(default_factory=set)
    best_tactics: list[str] = field(default_factory=list)


class TacticMemory:
    def __init__(self, *, failure_threshold: int = 1):
        self.failure_threshold = max(1, failure_threshold)
        self._records: dict[str, TacticMemoryRecord] = {}
        self._failure_counts: dict[tuple[str, str], int] = {}

    def record_failure(self, state_key: str, tactic: str) -> None:
        normalized = " ".join(tactic.strip().split())
        if not normalized:
            return
        record = self._records.setdefault(
            state_key, TacticMemoryRecord(state_key=state_key)
        )
        record.failed_tactics.add(normalized)
        key = (state_key, normalized)
        self._failure_counts[key] = self._failure_counts.get(key, 0) + 1

    def record_success(self, state_key: str, tactic: str) -> None:
        normalized = " ".join(tactic.strip().split())
        if not normalized:
            return
        record = self._records.setdefault(
            state_key, TacticMemoryRecord(state_key=state_key)
        )
        record.accepted_tactics.add(normalized)
        if normalized in record.best_tactics:
            record.best_tactics.remove(normalized)
        record.best_tactics.insert(0, normalized)
        del record.best_tactics[5:]

    def should_suppress(self, state_key: str, tactic: str) -> bool:
        normalized = " ".join(tactic.strip().split())
        if not normalized:
            return False
        key = (state_key, normalized)
        return self._failure_counts.get(key, 0) >= self.failure_threshold
