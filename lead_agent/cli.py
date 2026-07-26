from lead_agent.data import LeadDataError, load_leads
from lead_agent.settings import ConfigError, load_settings

BANNER = (
    "Lead Intelligence Agent\n"
    "Type a question, or 'exit' / Ctrl-C to quit.\n"
)


def startup() -> None:
    """Load settings and lead data. Raises ConfigError / LeadDataError."""
    settings = load_settings()
    leads = load_leads(settings.leads_path)
    print(f"Loaded {len(leads)} leads from {settings.leads_path}.\n")


def run() -> None:
    try:
        startup()
    except (ConfigError, LeadDataError) as exc:
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

        # Placeholder until the agent is wired up (Phase 7+).
        print(f"(scaffold) you asked: {question}\n")
