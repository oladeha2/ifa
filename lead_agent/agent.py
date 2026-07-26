import json
import uuid

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from lead_agent.models import Lead, SearchResponse
from lead_agent.prompts import SYSTEM_PROMPT
from lead_agent.semantic import SemanticEngine
from lead_agent.settings import Settings
from lead_agent.tools import make_search_leads_tool
from lead_agent.vectorstore import LeadVectorStore


class AgentError(RuntimeError):
    """Raised when the agent cannot complete a turn."""


def _build_model(settings: Settings) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.llm_model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=0,
    )


class LeadAgent:
    def __init__(
        self, settings: Settings, store: LeadVectorStore, engine: SemanticEngine
    ) -> None:
        model = _build_model(settings)
        tool = make_search_leads_tool(store, engine, settings)
        self._graph = create_agent(
            model,
            tools=[tool],
            system_prompt=SYSTEM_PROMPT,
            middleware=[
                SummarizationMiddleware(
                    model=model,
                    trigger=("messages", settings.summarize_every_n_turns * 4),
                    keep=("messages", 10),
                )
            ],
            checkpointer=InMemorySaver(),
        )
        self.reset()

    def reset(self) -> None:
        """Start a fresh conversation thread (drops follow-up memory)."""
        self._thread_id = str(uuid.uuid4())
        self._config = {"configurable": {"thread_id": self._thread_id}}

    def query(self, user_input: str) -> SearchResponse:
        try:
            state = self._graph.invoke(
                {"messages": [HumanMessage(content=user_input)]}, self._config
            )
        except Exception as exc:
            raise AgentError("The agent failed to process the request.") from exc

        messages = state["messages"]
        start = _last_user_index(messages)
        summary = _extract_summary(messages, start)
        leads = _extract_leads(messages, start)
        return SearchResponse(summary=summary, leads=leads)


def _last_user_index(messages: list) -> int:
    """Index of the most recent real user message (ignoring summary injections).

    Scopes summary/lead extraction to the current turn, since the checkpointer
    accumulates every message across the whole conversation.
    """
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if (
            isinstance(m, HumanMessage)
            and m.additional_kwargs.get("lc_source") != "summarization"
        ):
            return i
    return 0


def _extract_summary(messages: list, start: int) -> str:
    """The LLM's final natural-language answer for the current turn."""
    for m in reversed(messages[start:]):
        if isinstance(m, AIMessage) and isinstance(m.content, str) and m.content.strip():
            return m.content.strip()
    return "Sorry, I could not produce a response."


def _extract_leads(messages: list, start: int) -> list[Lead]:
    """Leads from the most recent `search_leads` call this turn, verbatim.

    Scoped to the current turn, so a follow-up answered from context without a
    tool call returns no leads rather than echoing an earlier turn's results.
    """
    for m in reversed(messages[start:]):
        if isinstance(m, ToolMessage) and m.name == "search_leads":
            try:
                payload = json.loads(m.content)
            except (json.JSONDecodeError, TypeError):
                return []
            if payload.get("status") != "ok":
                return []
            return [Lead.model_validate(record) for record in payload.get("leads", [])]
    return []
