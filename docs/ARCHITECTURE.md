# Architecture

> **Status:** M0 implemented. The flat layout below is current; `src/` was removed. See [PLAN.md](PLAN.md) for milestone order and remaining work.

Authoritative design reference for this repo. Read this before changing layout, adding a graph node, or wiring a new service. If code diverges, update this file in the same change.

## Confirmed decisions

- One uv project at the repo root: one `pyproject.toml`, one `.venv`. `syllabus-agent/` is the project name, not a nested package.
- LLM access uses LangChain's universal `init_chat_model` (from `langchain.chat_models`) with the `google_genai` provider; `langchain-google-genai` remains the provider backend.
- Environment loading uses `python-dotenv` from the root `.env`; `.env` is gitignored and `.env.example` is committed.
- LangGraph stays the single orchestrator. New capabilities are added as nodes to the same graph, never as a parallel pipeline.
- Library docs are verified with Context7 MCP (`context7` skill), not training-data guesses. See [Doc sources](#doc-sources).

## Target layout

```
App/                         # repo root
├── app.py                   # Streamlit entrypoint: uv run streamlit run app.py
├── graph/
│   ├── state.py             # WorkflowState TypedDict
│   ├── workflow.py          # build_workflow(...) wiring + conditional error edges
│   └── nodes/
│       ├── input_validation.py
│       ├── syllabus_parser.py
│       ├── output_validation.py
│       ├── video_retrieval.py        # M1
│       ├── popularity_ranking.py     # M1
│       ├── transcript_fetch.py       # M2
│       ├── transcript_evaluation.py  # M3
│       ├── playlist_selection.py     # M4
│       └── coverage_report.py        # M4
├── schemas/
│   ├── input.py             # SyllabusInput
│   ├── syllabus.py          # Topic, LearningUnit, ChecklistItem, SyllabusBreakdown
│   ├── video.py             # VideoCandidate, TranscriptSegment (M1/M2)
│   └── evaluation.py        # VideoEvaluation structured output (M3)
├── services/
│   ├── llm.py               # init_model(), structured_model(), lazy dotenv loading
│   ├── youtube.py           # httpx REST client: search.list / videos.list (M1)
│   └── transcripts.py       # youtube-transcript-api wrapper (M2)
├── core/
│   ├── validator.py         # input/output validation + error formatting
│   ├── scoring.py           # deterministic popularity score (M1)
│   └── languages.py         # language name -> ISO 639-1 (M1/M2)
├── prompts/
│   ├── decomposition.txt
│   ├── transcript_scoring.txt  # M3, content supplied by the user
│   └── coverage.txt            # M4
├── components/
│   ├── input_form.py        # Streamlit form widgets
│   └── results.py           # breakdown/video/score/export rendering
├── tests/
├── data/
│   ├── samples/             # example syllabi for manual smoke tests
│   └── cache/               # cached YouTube responses (gitignored from M1)
├── .env.example
├── .gitignore
├── .python-version
├── README.md
├── AGENTS.md
└── pyproject.toml
```

Every package directory has an `__init__.py` (implied above).

### Migration from current code

| Current | Target |
|---|---|
| `src/app/schemas.py` | split into `schemas/input.py` + `schemas/syllabus.py` |
| `src/app/prompts.py` | `prompts/decomposition.txt` + `prompts/__init__.py` loader |
| `src/app/llm.py` | `services/llm.py`, with `init_model()` replacing direct `ChatGoogleGenerativeAI(...)` |
| `src/app/workflow.py` | `graph/state.py`, `graph/workflow.py`, and the three existing nodes |
| `src/app/ui.py` | `app.py` + `components/input_form.py` + `components/results.py` |
| `tests/*` | reorganized to mirror modules |

Delete `src/`. Remove `[project.scripts] app = "app:main"`; `app.py` is a Streamlit script, not a CLI module.

## Packaging

Top-level modules require explicit `uv_build` configuration:

```toml
[tool.uv.build-backend]
module-root = ""
module-name = ["graph", "schemas", "services", "core", "prompts", "components"]

[tool.pytest.ini_options]
pythonpath = ["."]
```

`app.py` is intentionally excluded from `module-name`: it is a Streamlit script run from the repo root, not an importable package module.

## Module responsibilities

- **`schemas/`** — pure Pydantic models, no I/O. Keep schemas union-free for Gemini `json_schema` compatibility.
- **`core/`** — deterministic Python logic: validation, scoring, language mapping. No network, no LLM.
- **`services/`** — all external I/O: Gemini, YouTube REST, transcripts. Injectable at the graph boundary.
- **`graph/`** — state shape, node wiring, conditional routing. Nodes stay thin: validate → call service → return state deltas.
- **`prompts/`** — plain-text templates loaded by a helper, so prompts can be edited without touching Python.
- **`components/`** — Streamlit rendering only; no business logic.
- **`data/`** — samples and caches; never secrets.

## Graph design

`graph/state.py` uses one `WorkflowState(TypedDict, total=False)`, extended per milestone:

- Input: `subject`, `level`, `language`, `syllabus`
- Decomposition: `breakdown: SyllabusBreakdown | None`
- Retrieval (M1): `candidates`, `finalists` keyed by learning unit
- Transcripts (M2): `transcripts`
- Evaluation (M3): `evaluations`
- Playlist (M4): `playlist`, `coverage`
- Always: `error: str | None`

`graph/workflow.py` exposes:

```python
build_workflow(
    decomposer=None,          # offline test seam
    youtube_client=None,      # M1
    transcript_fetcher=None,  # M2
)
```

Edges: `START → input_validation → syllabus_parser → output_validation → (video_retrieval → popularity_ranking → transcript_fetch → transcript_evaluation → playlist_selection → coverage_report) → END`. After each node a conditional edge routes any `error` state straight to `END`, so the UI renders a message instead of crashing.

## LLM service (`services/llm.py`)

- `load_environment()` loads the root `.env` with `python-dotenv` without overriding real environment variables.
- `init_model(model: str | None = None)` reads `APP_GEMINI_MODEL` (default `gemini-3.5-flash-lite`) and calls:
  ```python
  from langchain.chat_models import init_chat_model
  init_chat_model(f"google_genai:{model}")
  ```
  It is **lazy** — no model is constructed at import time.
- `structured_model(schema)` applies `model.with_structured_output(schema, method="json_schema")`.
- Missing `GOOGLE_API_KEY` / `GEMINI_API_KEY` raises a clear `RuntimeError`, surfaced through the graph's `error` state.

## YouTube retrieval and scoring (M1)

- `services/youtube.py` uses `httpx` against the REST endpoints:
  - `GET /youtube/v3/search` with `part=snippet`, `q=<unit.search_query>`, `type=video`, `maxResults=20`, `order=relevance`, `relevanceLanguage=<ISO code>`.
  - `GET /youtube/v3/videos` with `part=snippet,statistics,contentDetails` and comma-separated `id` batches of at most 50, to obtain `viewCount`, `likeCount`, `commentCount`, duration, thumbnail, and channel.
- Cache raw responses in `data/cache/` to avoid repeat quota cost.
- Quota: `search.list` has a dedicated 100-calls/day bucket (1 call each); `videos.list` costs 1 unit per call. Twenty units → 20 search calls plus a few `videos.list` calls.
- **Assumption pending confirmation:** 20 candidates and 5 finalists are **per learning unit**, not per syllabus.
- `core/scoring.py` is deterministic and LLM-free:
  1. `log1p` each of views, likes, comments;
  2. min-max normalize within the 20-candidate pool (guards against one viral outlier);
  3. `score = 0.40 * views_norm + 0.35 * likes_norm + 0.25 * comments_norm` (named constants);
  4. sort descending, keep top 5.

## Transcripts (M2)

- `services/transcripts.py` wraps `YouTubeTranscriptApi().fetch(video_id, languages=[...])`; each snippet yields `text`, `start`, `duration`.
- Missing or disabled transcripts are normal: record `transcript=None`, keep the video, and let M3 fall back to title/description.
- The library uses an undocumented YouTube endpoint and can be IP-blocked; keep it isolated behind the service seam and out of the test suite.

## Transcript evaluation (M3)

- The user-supplied rubric is refined and stored in `prompts/transcript_scoring.txt`. Do not invent or replace its criteria.
- It evaluates ONE transcript-segment window against one unit's checklist. Inputs: `UNIT_TITLE` (relevance only), `CHECKLIST`, `TRANSCRIPT_SEGMENT` lines formatted `[timestamp] text`.
- Per-item output fields: `item`, `evidence_quote`, `evidence_timestamp`, `span`, `garbled`, `has_example`, `label` (`explained` / `mentioned` / `absent`).
- Segment-level output fields: `level`, `relevance`, `fluff`, `format`, `quality`, `prereqs`, `possible_error`.
- Schema goes in `schemas/evaluation.py`; node in `graph/nodes/transcript_evaluation.py`; use `structured_model(VideoEvaluation)`.
- This structured output is the ground for the FINAL choice among the 5 finalists selected in M1 — not for the initial 20-candidate shortlist.
- Aggregation from segment results to a per-video decision is not specified yet; confirm the rule before implementing final selection.

## Verification

- `uv run pytest -q` — offline; services are injected as fakes through `build_workflow(...)`. No live API calls in tests.
- Manual: `uv run streamlit run app.py` with `GOOGLE_API_KEY` (and `YOUTUBE_API_KEY` from M1) in `.env`.

## Doc sources

Verified with Context7 MCP (via the `context7` skill):

- LangChain `/websites/langchain_oss_python_langchain` — `init_chat_model("google_genai:...")`, `with_structured_output`, Pydantic schemas.
- LangGraph `/websites/langchain_oss_python_langgraph` — `StateGraph`, `TypedDict` state, `add_conditional_edges`, `compile`.
- YouTube API `/websites/developers_google_youtube/v3` — `search.list`, `videos.list` statistics, quota costs.
- YouTube Transcript API `/jdepoix/youtube-transcript-api` — `fetch(video_id, languages=[...])` and snippet fields.
- uv build backend module configuration was verified from official uv documentation.
