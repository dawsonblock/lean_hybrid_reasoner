from __future__ import annotations

import heapq
from itertools import count
from lean_hybrid_reasoner.schemas.branch import ProofBranch


class ProofFrontier:
    def __init__(self):
        self._heap: list[tuple[float, int, ProofBranch]] = []
        self._counter = count()

    def push(self, branch: ProofBranch) -> None:
        heapq.heappush(self._heap, (-branch.score, next(self._counter), branch))

    def pop(self) -> ProofBranch:
        return heapq.heappop(self._heap)[2]

    def __len__(self) -> int:
        return len(self._heap)

    def empty(self) -> bool:
        return not self._heap
