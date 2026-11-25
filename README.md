# Syllabus → YouTube Playlist Agent

A Streamlit app backed by a LangGraph workflow. It turns a university syllabus module into topics, learning units, checklists, and ready-to-use YouTube search queries using Gemini structured output.

Design docs: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (module layout and invariants) and [`docs/PLAN.md`](docs/PLAN.md) (milestones and status). Read them before changing the structure or pipeline.

## Setup

```bash
uv sync
```

Create a gitignored `.env` in the repo root:

```dotenv
GOOGLE_API_KEY=your-key-here
YOUTUBE_API_KEY=your-key-here
# Optional: APP_GEMINI_MODEL=gemini-3.5-flash-lite
```

## Run

```bash
uv run streamlit run app.py
```

## Test

```bash
uv run pytest -q
```

Tests are offline: the workflow accepts an injected decomposer, so no API key or network call is needed.

## Current scope

M0 complete: modular flat layout with LangGraph nodes, `init_chat_model`, plain-text prompts, and Streamlit components. Current feature scope is still syllabus input → LLM decomposition → Pydantic validation → structured display. YouTube retrieval, transcript analysis, ranking, and playlist generation come in later milestones, one graph node at a time.
