import logging

from lead_agent.agent import LeadAgent
from lead_agent.data import LeadDataError, load_leads
from lead_agent.models import Lead
from lead_agent.semantic import SemanticEngine, SemanticEngineError
from lead_agent.settings import ConfigError, load_settings
from lead_agent.vectorstore import LeadVectorStore, VectorStoreError

logger = logging.getLogger(__name__)

BANNER = (
    "Lead Intelligence Agent\n"
    "Type a question, 'reset' to start over, or 'exit' / Ctrl-C to quit.\n"
)

_GENERIC_ERROR = (
    "Your request could not be responded to due to an error, "
    "please try again later.\n"
)


def _configure_logging() -> None:
    """Surface our INFO logs while keeping third-party libraries quiet."""
    logging.basicConfig(
        level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s"
    )
    logging.getLogger("lead_agent").setLevel(logging.INFO)


def _format_lead(index: int, lead: Lead) -> str:
    priority = "  [HIGH PRIORITY]" if lead.high_priority else ""
    lines = [
        f"[{index}] {lead.full_name} - {lead.job_title} @ {lead.company}{priority}",
        f"    {lead.industry} | {lead.company_size} employees | {lead.location}",
    ]
    if lead.notes:
        note = lead.notes if len(lead.notes) <= 160 else lead.notes[:157] + "..."
        lines.append(f"    Notes: {note}")
    if lead.tags:
        lines.append(f"    Tags: {', '.join(lead.tags)}")
    return "\n".join(lines)

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
        if question.lower() in {"reset", "new"}:
            agent.reset()
            print("Started a new conversation.\n")
            continue

        try:
            response = agent.query(question)
        except Exception:
            logger.exception("Failed to handle question: %r", question)
            print(_GENERIC_ERROR)
            continue

        print(f"\n{response.summary}\n")
        if response.leads:
            print(f"Leads ({len(response.leads)}):")
            for i, lead in enumerate(response.leads, 1):
                print(_format_lead(i, lead))
            print()
