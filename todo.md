# Build Plan — Lead Intelligence Agent

Tasks are ordered bottom-up so each layer is verifiable before the next depends on it.
Work through them one at a time, checking each box as it is completed. Full design context
lives in `project_plan.html`.

---

## Phase 0 — Project scaffolding
- [x] Initialise the project with **uv** (`uv init`), set Python version, create `pyproject.toml`.
- [x] Add core dependencies via uv: `chromadb`, `sentence-transformers`, `langgraph`, `langchain`, `langchain-openai`, `pydantic`, `pydantic-settings`, `python-dotenv`.
- [x] Export `requirements.txt` from uv (rubric compliance) and confirm plain-pip install works.
- [x] Create the `lead_agent/` package with an empty `__init__.py` and the module files (empty stubs).
- [x] Add `.gitignore` (`.env`, `.chroma/`, `memory/`, `__pycache__/`) and `.env.example` with `OPENROUTER_API_KEY=`.
- [x] Create a thin `main.py` and a `cli.py` that runs a placeholder REPL (echoes input, handles Ctrl-C/EOF cleanly).
- [x] **Verify:** `python main.py` (and `uv run main.py`) starts the REPL and exits cleanly.

## Phase 1 — Settings & typed models
- [x] Implement `Settings` in `settings.py` using `pydantic-settings` (models, paths, top_k, overfetch, threshold, N-turns, API key).
- [x] Fail fast with a clear message when `OPENROUTER_API_KEY` is missing.
- [x] Implement `Lead`, `ScoredLead`, `SearchResponse` in `models.py`, plus `Industry` / `LeadSource` `Literal` types (all 29 / 8 values).
- [x] Implement `Lead.to_embedding_text()` and `Lead.to_metadata()`.
- [x] **Verify:** construct a `Lead` from a sample dict; print its embedding text and metadata.

## Phase 2 — Data loading & scoring
- [x] Implement `load_leads(path) -> list[Lead]` in `data.py` (read + validate each record).
- [x] Compute `high_priority` per the rule (VP/Director in title OR company_size > 500). _(Handled by the `@computed_field` on `Lead`; no loader logic needed.)_
- [x] Handle errors: file missing, invalid JSON, schema mismatch — each with a distinct clear message.
- [x] **Verify:** load `leads.json`; assert 200 leads; spot-check a few `high_priority` values.

## Phase 3 — Semantic engine (embeddings + rerank)
- [x] Implement `SemanticEngine` in `semantic.py` loading the bi-encoder and cross-encoder.
- [x] Implement `embed()`, `embed_query()`, and `rerank(query, candidates)`.
- [x] Handle first-run model-download failure with a clear message.
- [x] **Verify:** embed a couple of strings (check vector dim); rerank a small candidate list and confirm ordering.

## Phase 4 — Vector store (ingest + query)
- [x] Implement `LeadVectorStore` in `vectorstore.py` over a Chroma `PersistentClient`, using `SemanticEngine`.
- [x] Implement `count()`, `upsert(leads)` (build text + metadata, embed, store), and idempotent skip when populated.
- [x] Implement `query(query_text, filters, limit) -> list[ScoredLead]` with metadata filtering (`$in`, `$gte`, etc.) and `get_by_id()`.
- [x] Wire ingestion into startup (`cli.py`): load → build components → upsert if empty. _(Plus an interim plain vector-search REPL for iterative testing.)_
- [x] **Verify:** after first run, `count() == 200`; a filtered query returns only matching industry/size; second run skips re-embedding.

## Phase 5 — Retrieval function
- [x] Implement `retrieve()` in `retrieval.py`: over-fetch → rerank → threshold → top_k.
- [x] **Verify:** a relevant query returns sensible leads; an irrelevant query returns an empty list after thresholding. _(Interim REPL now uses `retrieve()`; `rerank_threshold=0.0` cleanly separates relevant (+) from noise (~-10).)_

## Phase 6 — Search tool
- [x] Implement the `search_leads` LangChain tool in `tools.py` with typed args (list-of-enum filters) and the mapping docstring.
- [x] Implement the return contract: `ok` with leads, `ok` with empty list, `error` on store failure.
- [x] **Verify:** call the tool directly with several arg combinations (semantic-only, filter-only, both, no-match).

## Phase 7 — Prompts & agent
- [x] Write the system prompt in `prompts.py` (role, enum values, colloquial→enum mapping, summary-writing instruction).
- [x] Configure the OpenRouter Claude model via `ChatOpenAI` (base_url + key).
- [x] Build the agent with the single tool in `agent.py` (langchain 1.x `create_agent`, since `create_react_agent` is deprecated); wrap it in a `LeadAgent` class with `.query()` and `.reset()`.
- [x] Assemble `SearchResponse` with the LLM-authored summary + tool leads verbatim (LLM never regenerates leads; leads deduped by id across tool calls).
- [x] **Verify:** a one-shot question runs end-to-end and returns a structured `{summary, leads}`. _(Logic verified offline with a fake tool-calling model; live LLM run pending a valid `OPENROUTER_API_KEY` — current key returns 401.)_

## Phase 8 — Memory & summarization
- [x] Thread/session memory via the `InMemorySaver` checkpointer so follow-up questions work (this is the brief's "basic memory mechanism").
- [x] Summarization via `SummarizationMiddleware`: after ~N turns, condense older messages and keep the recent ones (context control). _(Local JSON persistence dropped — not required by the brief and never fed back into the model.)_
- [x] **Verify:** a follow-up resolves using prior context; a no-tool follow-up yields no stale leads; summarization trips and trims state after ~N turns.

## Phase 9 — CLI integration & response formatting
- [x] Flesh out `cli.py`: read question → `agent.query()` → print summary + nicely formatted lead list (numbered, high-priority marker, trimmed notes, `Leads (N):` header). Added a `reset`/`new` command.
- [x] Add the top-level error boundary (catch-all that logs the real error via `logger.exception` + generic message, keeps looping) and clean `exit`/Ctrl-C/EOF exit.
- [x] **Verify:** full interactive session via `python main.py` including a multi-turn exchange, no-match, and the error boundary (bogus model slug).

## Phase 10 — Hardening & polish
- [ ] Exercise every error path (missing key, bad JSON, store error, no results, LLM failure).
- [ ] Add a small set of scripted demo queries showing filter-only, semantic-only, hybrid, follow-up, and no-match.
- [ ] Tune `rerank_threshold`, `top_k`, `overfetch`, `summarize_every_n_turns`.
- [ ] Write `README.md` (setup with uv and with pip; how to run; example queries; notes on first-run downloads).

## Non-code deliverables (owned separately)
- [ ] Part 1: workflow diagram + written RAG-vs-RPA explanation.
- [ ] Part 3 (optional): metrics, orchestration, improvement writeup.
