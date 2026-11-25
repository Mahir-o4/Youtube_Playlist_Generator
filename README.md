# Syllabus → YouTube Playlist Agent

A Streamlit app backed by a LangGraph workflow. It turns a university syllabus module into topics, learning units, checklists, and ready-to-use YouTube search queries using Gemini structured output.

Design docs: [`docs/WORKFLOW.md`](docs/WORKFLOW.md) (end-to-end diagram and file map), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (module layout and invariants), and [`docs/PLAN.md`](docs/PLAN.md) (milestones and status). Read them before changing the structure or pipeline.

## Setup

```bash
uv sync
```

Create a gitignored `.env` in the repo root:

```dotenv
GOOGLE_API_KEY=your-key-here
YOUTUBE_API_KEY=your-key-here
# Optional: APP_GEMINI_MODEL=gemini-3.5-flash-lite
# Optional: YOUTUBE_REGION_CODE=   # e.g. IN; unset = global
# Optional: YOUTUBE_WORKERS=4, TRANSCRIPT_WORKERS=3, EVALUATION_WORKERS=4
```

## Run

```bash
uv run streamlit run app.py
```

## Test

```bash
uv run pytest -q
```

Tests are offline: the workflow accepts injected decomposer, YouTube, transcript, and evaluator fakes, so no API key or network call is needed.

## Current scope

Full pipeline implemented: syllabus input → LLM decomposition → 20 YouTube candidates per unit → deterministic top-5 by views/likes/comments → transcript evaluation with the supplied rubric → selected playlist with jump-to timestamps, coverage report, JSON and CSV downloads. See [`docs/PLAN.md`](docs/PLAN.md) for milestone status.
