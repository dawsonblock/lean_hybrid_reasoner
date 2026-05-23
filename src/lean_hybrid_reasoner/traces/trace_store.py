from __future__ import annotations

import json
from pathlib import Path
from lean_hybrid_reasoner.schemas.result import ProofRunResult


class TraceStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, result: ProofRunResult) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result.model_dump(), ensure_ascii=False) + "\n")
