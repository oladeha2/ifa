import logging
from typing import Optional

from langchain_core.tools import tool

from lead_agent.models import Industry, LeadSource
from lead_agent.retrieval import retrieve
from lead_agent.semantic import SemanticEngine
from lead_agent.settings import Settings
from lead_agent.vectorstore import LeadVectorStore, VectorStoreError

logger = logging.getLogger(__name__)


def _build_where(
    industry: Optional[list[Industry]],
    lead_source: Optional[list[LeadSource]],
    min_company_size: Optional[int],
    high_priority: Optional[bool],
) -> dict:
    conditions: list[dict] = []

    if industry:
        conditions.append({"industry": {"$in": list(industry)}})
    if lead_source:
        conditions.append({"lead_source": {"$in": list(lead_source)}})
    if min_company_size is not None:
        conditions.append({"company_size": {"$gte": min_company_size}})
    if high_priority is not None:
        conditions.append({"high_priority": high_priority})

    if not conditions:
        return {}

    if len(conditions) == 1:
        return conditions[0]

    return {"$and": conditions}  # Chroma requires $and for multiple conditions


def make_search_leads_tool(
    store: LeadVectorStore, engine: SemanticEngine, settings: Settings
):
    @tool
    def search_leads(
        query: str,
        industry: Optional[list[Industry]] = None,
        lead_source: Optional[list[LeadSource]] = None,
        min_company_size: Optional[int] = None,
        high_priority: Optional[bool] = None,
    ) -> dict:
        """Search sales leads by meaning plus optional hard filters.

        Put descriptive intent (pain points, interests, tech, seniority,
        location) in `query`. Use the filter arguments only for hard
        constraints. Map colloquial industry terms to the allowed values and
        include related variants, e.g. "fintech" -> ["Financial Services",
        "Fintech"], "ecommerce" -> ["Ecommerce", "DTC", "Retail"].
        Set high_priority=true when the user asks for priority/important leads.
        """
        where = _build_where(industry, lead_source, min_company_size, high_priority)
        logger.info("search_leads: query=%r filters=%s", query, where or {})

        try:
            results = retrieve(query, where, store, engine, settings)

        except VectorStoreError:
            return {
                "status": "error",
                "message": "There was an issue retrieving results from the data store.",
            }

        return {"status": "ok", "leads": [r.lead.model_dump() for r in results]}

    return search_leads
