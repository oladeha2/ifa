"""Command-line REPL for the Lead Intelligence Agent.

Phase 0: a placeholder loop that echoes input and exits cleanly. Later phases
wire in settings, ingestion, and the agent, and add the top-level error
boundary and formatted `{summary, leads}` output.
"""

from __future__ import annotations

BANNER = (
    "Lead Intelligence Agent (scaffold)\n"
    "Type a question, or 'exit' / Ctrl-C to quit.\n"
)


def run() -> None:
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
