from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import log
from pathlib import Path
import re

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_']*|[∧∨→=+*/<>≤≥¬]")
_DECL_RE = re.compile(
    r"^\s*(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_']*)\s*(.*?)(?:\s*:=\s*by|\s*:=|$)"
)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


@dataclass(frozen=True)
class Premise:
    name: str
    statement: str
    source: str = "starter"


class PremiseIndex:
    """Small dependency-free BM25-ish premise index.

    This remains lightweight for the starter zip but is a cleaner seam for later
    replacement with embeddings or Lean-aware premise retrievers.
    """

    def __init__(self, premises: list[Premise], *, k1: float = 1.4, b: float = 0.75):
        self.premises = premises
        self.k1 = k1
        self.b = b
        self._vectors = [
            Counter(tokenize(p.name + " " + p.statement)) for p in premises
        ]
        self._doc_lens = [sum(v.values()) for v in self._vectors]
        self._avg_len = (
            sum(self._doc_lens) / len(self._doc_lens) if self._doc_lens else 1.0
        )
        self._df = Counter()
        for vec in self._vectors:
            self._df.update(vec.keys())

    @classmethod
    def starter(cls) -> "PremiseIndex":
        return cls(
            premises=[
                Premise("Nat.add_zero", "n + 0 = n"),
                Premise("Nat.zero_add", "0 + n = n"),
                Premise("And.intro", "p -> q -> p ∧ q"),
                Premise("And.left", "p ∧ q -> p"),
                Premise("And.right", "p ∧ q -> q"),
                Premise("Eq.refl", "x = x"),
                Premise("Iff.intro", "(p -> q) -> (q -> p) -> (p ↔ q)"),
            ]
        )

    @classmethod
    def from_lean_file(cls, path: str | Path) -> "PremiseIndex":
        path = Path(path)
        premises: list[Premise] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _DECL_RE.match(line)
            if not match:
                continue
            name, statement = match.groups()
            premises.append(
                Premise(name=name, statement=statement.strip(), source=str(path))
            )
        if not premises:
            raise ValueError(f"No theorem/lemma declarations found in {path}")
        return cls(premises)

    def search(self, query: str, top_k: int = 8) -> list[Premise]:
        qv = Counter(tokenize(query))
        if not qv:
            return []
        scored: list[tuple[float, Premise]] = []
        n_docs = max(len(self.premises), 1)
        for premise, vec, doc_len in zip(self.premises, self._vectors, self._doc_lens):
            score = 0.0
            for token, qtf in qv.items():
                tf = vec.get(token, 0)
                if tf == 0:
                    continue
                df = self._df.get(token, 0)
                idf = log(1 + (n_docs - df + 0.5) / (df + 0.5))
                denom = tf + self.k1 * (1 - self.b + self.b * doc_len / self._avg_len)
                score += qtf * idf * ((tf * (self.k1 + 1)) / denom)
            if premise.name.lower() in query.lower():
                score += 0.5
            if score > 0:
                scored.append((score, premise))
        scored.sort(key=lambda x: (x[0], x[1].name), reverse=True)
        return [p for _, p in scored[:top_k]]
