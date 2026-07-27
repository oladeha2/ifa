"""LeadVectorStore: persistent ChromaDB collection for idempotent ingest and
filtered vector queries. Embeddings are owned by SemanticEngine.
"""

import chromadb

from lead_agent.models import Lead, ScoredLead
from lead_agent.semantic import SemanticEngine
from lead_agent.settings import Settings


class VectorStoreError(RuntimeError):
    """Raised when the vector store cannot be initialised or queried."""


class LeadVectorStore:
    def __init__(self, settings: Settings, engine: SemanticEngine) -> None:
        self._engine = engine
        try:
            client = chromadb.PersistentClient(path=str(settings.chroma_path))

            self._collection = client.get_or_create_collection(
                name=settings.collection_name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=None,
            )

        except Exception as exc:
            raise VectorStoreError(f"Could not open vector store: {exc}") from exc

    def count(self) -> int:
        return self._collection.count()

    def upsert(self, leads: list[Lead]) -> None:
        if self.count() == len(leads): # skip reindex if ./chroma already has leads
            return

        documents = [lead.to_embedding_text() for lead in leads]

        try:
            self._collection.upsert(
                ids=[str(lead.id) for lead in leads],
                embeddings=self._engine.embed(documents),
                documents=documents,
                metadatas=[lead.to_metadata() for lead in leads],
            )

        except Exception as exc:
            raise VectorStoreError(f"Failed to index leads: {exc}") from exc

    def query(self, query_text: str, filters: dict, limit: int) -> list[ScoredLead]:
        try:
            result = self._collection.query(
                query_embeddings=[self._engine.embed_query(query_text)],
                n_results=limit,
                where=filters or None,
                include=["metadatas", "distances"],
            )

        except Exception as exc:
            raise VectorStoreError(f"Query failed: {exc}") from exc

        metadatas = result["metadatas"][0]
        distances = result["distances"][0]

        return [
            ScoredLead(lead=Lead.from_metadata(meta), score=1.0 - dist)
            for meta, dist in zip(metadatas, distances)
        ]
