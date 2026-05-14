# Minerva — Deep Research Assistant

Minerva is a hierarchical multi-agent research assistant that takes a single question and returns a comprehensive, cited Markdown report. It decomposes the question into subtopics, researches each one in parallel using web search and page reading, caches findings in a vector store to avoid redundant fetches, and synthesises everything into a polished final report.

Built with [LangGraph](https://github.com/langchain-ai/langgraph), [Claude](https://anthropic.com), and [Tavily](https://tavily.com).

---

## How it works

```
User query
    │
    ▼
┌─────────────────┐
│  Manager Agent  │  Decomposes the query into up to 5 subtopics,
│  (Sonnet 4.6)   │  each with a search query and worker type.
└────────┬────────┘
         │  parallel fan-out (LangGraph Send)
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐  ...one worker per subtopic
│ Memory │ │ Memory │  ChromaDB vector cache — returns instantly
│ lookup │ │ lookup │  if a similar query was seen before.
└───┬────┘ └───┬────┘
    │ miss      │ miss
    ▼           ▼
┌────────┐ ┌────────┐
│ Search │ │ Reader │  Search: Tavily API
│ Worker │ │ Worker │  Reader: fetch + extract page content
└───┬────┘ └───┬────┘
    │           │
    └─────┬─────┘
          ▼
┌──────────────────┐
│ Synthesis Agent  │  Merges all findings into a structured
│  (Sonnet 4.6)    │  Markdown report with inline citations.
└──────────────────┘
          │
          ▼
     Final report
```

### Agents

| Agent | Model | Role |
|---|---|---|
| **Manager** | Claude Sonnet 4.6 | Breaks the query into subtopics and assigns a worker type to each |
| **Search Worker** | Claude Haiku 4.5 | Runs Tavily web searches and summarises results |
| **Reader Worker** | Claude Haiku 4.5 | Fetches and extracts content from specific URLs |
| **Memory Agent** | — | Checks ChromaDB for cached findings before hitting the web; stores new results after |
| **Synthesis Agent** | Claude Sonnet 4.6 | Merges all subtopic findings into a final cited report |

---

## Features

- **Parallel research** — subtopics are researched concurrently via LangGraph's `Send` fan-out
- **RAG cache** — ChromaDB + `all-MiniLM-L6-v2` embeddings; repeated or similar queries return instantly from cache
- **Streaming UI** — live progress updates per agent via `stream_mode="updates"`
- **Prompt caching** — `cache_control: ephemeral` on system prompts reduces API cost on repeated runs
- **Quality gates** — radon complexity check (all functions must be grade A/B) + pytest-cov on every CI run

---

## Project structure

```
minerva/
├── agents/
│   ├── manager_agent.py     # Subtopic decomposition
│   ├── search_agent.py      # Tavily web search worker
│   ├── reader_agent.py      # URL fetch + extraction worker
│   ├── memory_agent.py      # ChromaDB cache lookup/store
│   └── synthesis_agent.py   # Final report generation
├── graph/
│   ├── orchestrator.py      # LangGraph StateGraph definition
│   └── state.py             # ResearchState TypedDict
├── ui/
│   └── app.py               # Streamlit front-end
├── tests/                   # pytest suite
├── config.py                # Pydantic settings (reads .env)
└── .github/workflows/ci.yml # CI: tests + coverage + complexity
```

---

## Getting started

### Prerequisites

- Python 3.12
- An [Anthropic API key](https://console.anthropic.com)
- A [Tavily API key](https://app.tavily.com)

### Local setup

```bash
git clone https://github.com/rbadri91/minerva.git
cd minerva

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then fill in your keys
```

**.env**
```
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
```

```bash
python -m streamlit run ui/app.py
```

Open [http://localhost:8501](http://localhost:8501), enter a research question, and click **Research**.

---

## Deployment

### Streamlit Community Cloud (free)

1. Fork or connect this repo at [share.streamlit.io](https://share.streamlit.io)
2. Set **Main file path** to `ui/app.py`
3. Under **App Settings → Secrets**, add:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   TAVILY_API_KEY = "tvly-..."
   ```
4. Click **Deploy**

> The ChromaDB cache is ephemeral on the free tier and resets on restart. The app works without it — research just re-fetches from the web.

---

## Running tests

```bash
# Fast unit tests (no API calls)
python -m pytest tests/test_branch_guard.py tests/test_synthesis.py::test_format_findings_skips_empty_content -v

# Full suite (requires API keys)
python -m pytest --cov=agents --cov=graph --cov-config=.coveragerc -v

# Complexity check
python -m radon cc agents/ graph/ -n C -s
```

---

## Configuration

All settings are in `config.py` and can be overridden via `.env`:

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required |
| `TAVILY_API_KEY` | — | Required |
| `MANAGER_MODEL` | `claude-sonnet-4-6` | Model for query decomposition |
| `WORKER_MODEL` | `claude-haiku-4-5` | Model for search/reader workers |
| `SYNTHESIS_MODEL` | `claude-sonnet-4-6` | Model for final report |
| `MAX_SUBTOPICS` | `5` | Maximum parallel research threads |
| `SIMILARITY_THRESHOLD` | `0.85` | ChromaDB cosine similarity threshold for cache hits |
| `CHROMA_DB_PATH` | `./chroma_db` | Local path for the vector store |
