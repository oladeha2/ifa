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
    logger.info("retrieve: %d candidates from vector search", len(candidates))
    for c in candidates:
        logger.info(
            "  candidate: %s - %s @ %s (%s) [score=%.3f]",
            c.lead.full_name,
            c.lead.job_title,
            c.lead.company,
            c.lead.industry,
            c.score,
        )

    reranked = engine.rerank(query_text, candidates)
    logger.info("retrieve: %d reranked candidates (pre-threshold)", len(reranked))
    for c in reranked:
        logger.info(
            "  reranked: %s - %s @ %s (%s) [score=%.3f]",
            c.lead.full_name,
            c.lead.job_title,
            c.lead.company,
            c.lead.industry,
            c.score,
        )

    kept = [c for c in reranked if c.score >= settings.rerank_threshold]
    result = kept[: settings.top_k]
    logger.info(
        "retrieve: %d leads after rerank + threshold (kept %d of %d, top_k=%d)",
        len(result),
        len(kept),
        len(reranked),
        settings.top_k,
    )
    return result
