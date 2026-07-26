from lead_agent.data import LeadDataError, load_leads
from lead_agent.retrieval import retrieve
from lead_agent.semantic import SemanticEngine, SemanticEngineError
from lead_agent.settings import ConfigError, Settings, load_settings
from lead_agent.vectorstore import LeadVectorStore, VectorStoreError

BANNER = (
    "Lead Intelligence Agent\n"
    "Type a question, or 'exit' / Ctrl-C to quit.\n"
)


def startup() -> tuple[LeadVectorStore, SemanticEngine, Settings]:
    """Load settings and data, then build and populate the vector store."""
    settings = load_settings()
    leads = load_leads(settings.leads_path)
    engine = SemanticEngine(settings)
    store = LeadVectorStore(settings, engine)
    store.upsert(leads)
    print(f"Indexed {store.count()} leads from {settings.leads_path}.\n")
    return store, engine, settings


def run() -> None:
    try:
        store, engine, settings = startup()
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

        # Interim retrieval (rerank + threshold, no filters yet - Phase 6).
        # Replaced by the agent in Phase 7.
        try:
            results = retrieve(question, {}, store, engine, settings)
        except VectorStoreError as exc:
            print(f"Search error: {exc}\n")
            continue

        if not results:
            print("No leads found.\n")
        else:
            for r in results:
                lead = r.lead
                print(
                    f"  [{r.score:.3f}] {lead.full_name} - {lead.job_title} "
                    f"@ {lead.company} ({lead.industry})"
                )
            print()
