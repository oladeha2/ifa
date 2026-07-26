import logging

from lead_agent.agent import AgentError, LeadAgent
from lead_agent.data import LeadDataError, load_leads
from lead_agent.semantic import SemanticEngine, SemanticEngineError
from lead_agent.settings import ConfigError, load_settings
from lead_agent.vectorstore import LeadVectorStore, VectorStoreError

BANNER = (
    "Lead Intelligence Agent\n"
    "Type a question, or 'exit' / Ctrl-C to quit.\n"
)


def _configure_logging() -> None:
    """Surface our INFO logs while keeping third-party libraries quiet."""
    logging.basicConfig(
        level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s"
    )
    logging.getLogger("lead_agent").setLevel(logging.INFO)


def startup() -> LeadAgent:
    """Load settings and data, build the vector store, and wire up the agent."""
    settings = load_settings()
    leads = load_leads(settings.leads_path)
    engine = SemanticEngine(settings)
    store = LeadVectorStore(settings, engine)
    store.upsert(leads)
    print(f"Indexed {store.count()} leads from {settings.leads_path}.\n")
    return LeadAgent(settings, store, engine)


def run() -> None:
    _configure_logging()
    try:
        agent = startup()
    except (ConfigError, LeadDataError, SemanticEngineError, VectorStoreError) as exc:
        raise SystemExit(f"Startup failed: {exc}")

    print(BANNER)
    while True:
        try:
            question = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        try:
            response = agent.query(question)
        except AgentError:
            print(
                "Your request could not be responded to due to an error, "
                "please try again later.\n"
            )
            continue

        print(f"\n{response.summary}\n")
        for lead in response.leads:
            print(
                f"  - {lead.full_name} - {lead.job_title} @ {lead.company} "
                f"({lead.industry}, {lead.company_size} employees, {lead.location}) Notes: {lead.notes}"
            )
        print()
