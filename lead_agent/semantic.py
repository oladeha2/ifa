from sentence_transformers import CrossEncoder, SentenceTransformer

from lead_agent.models import ScoredLead
from lead_agent.settings import Settings


class SemanticEngineError(RuntimeError):
    """Raised when the embedding/reranking models cannot be loaded."""


class SemanticEngine:
    def __init__(self, settings: Settings) -> None:
        try:
            self._embedder = SentenceTransformer(settings.embedding_model)
            self._reranker = CrossEncoder(settings.cross_encoder_model)
        except Exception as exc:
            raise SemanticEngineError(
                "Could not load the embedding/reranking models "
                f"('{settings.embedding_model}', '{settings.cross_encoder_model}'). "
                "The first run downloads them from Hugging Face; check your network."
            ) from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed documents into normalized vectors (for cosine similarity)."""
        vectors = self._embedder.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        return self.embed([text])[0]

    def rerank(self, query: str, candidates: list[ScoredLead]) -> list[ScoredLead]:
        """Re-score candidates with the cross-encoder and sort best-first."""
        if not candidates:
            return []

        pairs = [(query, c.lead.to_embedding_text()) for c in candidates]
        scores = self._reranker.predict(pairs)
        
        reranked = [
            ScoredLead(lead=c.lead, score=float(s))
            for c, s in zip(candidates, scores)
        ]
        reranked.sort(key=lambda c: c.score, reverse=True)
        return reranked
