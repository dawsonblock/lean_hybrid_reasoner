from __future__ import annotations

from collections import Counter
from math import sqrt
from pathlib import Path
from typing import Protocol

from lean_hybrid_reasoner.retrieval.premise_index import Premise, tokenize, PremiseIndex


class PremiseSearchIndex(Protocol):
    def search(self, query: str, top_k: int = 8) -> list[Premise]: ...


class HashingSemanticPremiseIndex:
    """Dependency-free semantic-ish fallback using signed hashing vectors.

    This is not a replacement for a Lean-aware embedding model. It gives the
    project a stable semantic-retrieval seam and testable cosine-ranking behavior
    without pulling FAISS or sentence-transformers into the default install.
    """

    def __init__(self, premises: list[Premise], dims: int = 256):
        self.premises = premises
        self.dims = dims
        self._vectors = [self._embed(p.name + " " + p.statement) for p in premises]

    @classmethod
    def starter(cls) -> "HashingSemanticPremiseIndex":
        return cls(PremiseIndex.starter().premises)

    @classmethod
    def from_lean_file(cls, path: str | Path) -> "HashingSemanticPremiseIndex":
        return cls(PremiseIndex.from_lean_file(path).premises)

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dims
        tokens = tokenize(text)
        counts = Counter(tokens)
        for token, count in counts.items():
            h = hash(token)
            idx = abs(h) % self.dims
            sign = 1.0 if h >= 0 else -1.0
            vec[idx] += sign * count
        norm = sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def search(self, query: str, top_k: int = 8) -> list[Premise]:
        q = self._embed(query)
        scored = [(self._cosine(q, v), p) for p, v in zip(self.premises, self._vectors)]
        scored = [(s, p) for s, p in scored if s > 0]
        scored.sort(key=lambda item: (item[0], item[1].name), reverse=True)
        return [p for _, p in scored[:top_k]]


class SentenceTransformerPremiseIndex:
    """Optional sentence-transformers + FAISS retrieval adapter.

    This is intentionally lazy-imported. Install the optional semantic extras and
    use `LHR_RETRIEVAL_MODE=sentence_transformers` to select this path.
    """

    def __init__(
        self,
        premises: list[Premise],
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            import numpy as np
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise RuntimeError(
                "Install semantic extras with `pip install -e .[semantic]` to use sentence-transformer retrieval."
            ) from exc
        self.premises = premises
        self.model_name = model_name
        self._np = np
        self._faiss = faiss
        self.model = SentenceTransformer(model_name)
        texts = [p.name + " " + p.statement for p in premises]
        vectors = self.model.encode(texts, normalize_embeddings=True)
        vectors = np.asarray(vectors, dtype="float32")
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    @classmethod
    def starter(
        cls, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> "SentenceTransformerPremiseIndex":
        return cls(PremiseIndex.starter().premises, model_name=model_name)

    @classmethod
    def from_lean_file(
        cls,
        path: str | Path,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> "SentenceTransformerPremiseIndex":
        return cls(PremiseIndex.from_lean_file(path).premises, model_name=model_name)

    def search(self, query: str, top_k: int = 8) -> list[Premise]:
        if not query.strip():
            return []
        q = self.model.encode([query], normalize_embeddings=True)
        q = self._np.asarray(q, dtype="float32")
        _scores, ids = self.index.search(q, min(top_k, len(self.premises)))
        return [self.premises[int(i)] for i in ids[0] if int(i) >= 0]
