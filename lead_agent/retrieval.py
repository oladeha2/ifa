import logging

from lead_agent.models import ScoredLead
from lead_agent.semantic import SemanticEngine
from lead_agent.settings import Settings
from lead_agent.vectorstore import LeadVectorStore

logger = logging.getLogger(__name__)


def retrieve(
    query_text: str,
    filters: dict,
    store: LeadVectorStore,
    engine: SemanticEngine,
    settings: Settings,
) -> list[ScoredLead]:

    candidates = store.query(query_text, filters, limit=settings.overfetch)
    reranked = engine.rerank(query_text, candidates)
    kept = [c for c in reranked if c.score >= settings.rerank_threshold]
    result = kept[: settings.top_k]
    return result
