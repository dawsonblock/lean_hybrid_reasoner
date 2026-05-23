from __future__ import annotations

from lean_hybrid_reasoner.retrieval.premise_index import PremiseIndex
from lean_hybrid_reasoner.retrieval.semantic_index import HashingSemanticPremiseIndex, SentenceTransformerPremiseIndex, PremiseSearchIndex
from lean_hybrid_reasoner.schemas.proof_state import LeanProofState


class PremiseRetriever:
    def __init__(self, index: PremiseSearchIndex | None = None, top_k: int = 8):
        self.index = index or PremiseIndex.starter()
        self.top_k = top_k

    @classmethod
    def from_mode(cls, mode: str = "bm25", top_k: int = 8, lean_file: str | None = None, embedding_model: str | None = None) -> "PremiseRetriever":
        mode = mode.lower().strip()
        if mode == "bm25":
            index = PremiseIndex.from_lean_file(lean_file) if lean_file else PremiseIndex.starter()
        elif mode in {"semantic", "hashing_semantic"}:
            index = HashingSemanticPremiseIndex.from_lean_file(lean_file) if lean_file else HashingSemanticPremiseIndex.starter()
        elif mode in {"sentence_transformers", "faiss"}:
            if lean_file:
                index = SentenceTransformerPremiseIndex.from_lean_file(lean_file, model_name=embedding_model or "sentence-transformers/all-MiniLM-L6-v2")
            else:
                index = SentenceTransformerPremiseIndex.starter(model_name=embedding_model or "sentence-transformers/all-MiniLM-L6-v2")
        else:
            raise ValueError(f"Unsupported retrieval mode: {mode}")
        return cls(index=index, top_k=top_k)

    def retrieve(self, state: LeanProofState) -> list[str]:
        query = "\n".join(
            [
                state.theorem_statement,
                state.current_goal,
                *state.open_goals,
                *state.hypotheses,
                *state.proof_prefix[-5:],
            ]
        )
        premises = self.index.search(query, top_k=self.top_k)
        return [f"{p.name}: {p.statement}" for p in premises]
