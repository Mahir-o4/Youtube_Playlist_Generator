# AGENTS.md

Early-stage syllabus-to-YouTube-playlist app. `pyproject.toml` and `uv.lock` are the dependency sources of truth.

## Read first

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — module layout, graph design, and invariants (M0–M4 implemented).
- [`docs/PLAN.md`](docs/PLAN.md) — milestone status and verification.
- Read both before changing structure or adding a node/service; keep them updated in the same change when code diverges.

## Toolchain

- `uv`-managed: use `uv run ...` and `uv sync`; `.venv/` is generated and gitignored. Add dependencies with `uv add` (`uv add --dev pytest` for test tooling) so `pyproject.toml` and `uv.lock` stay in sync.
- Python is pinned to 3.14 in `.python-version` (`requires-python = ">=3.14"`); don't downgrade it.
- Secrets live in the gitignored root `.env`. `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) is required for decomposition/transcript scoring; `YOUTUBE_API_KEY` is required for retrieval. `APP_GEMINI_MODEL` overrides the default `gemini-3.5-flash-lite`. Never commit `.env`; use `.env.example` as the template.

## Layout and entrypoints

- Modular flat layout at the repo root; `src/` and the `app = "app:main"` script are gone. `uv_build` uses `module-root = ""` with named packages (see `pyproject.toml`).
- Streamlit entrypoint: `uv run streamlit run app.py`. `app.py` is not packaged as an importable module; run it from the repo root.
- Pipeline packages: `schemas/` (Pydantic models) → `prompts/` (text templates) → `services/` (Gemini, YouTube REST, transcripts) → `graph/` (`build_workflow` + nodes in `graph/nodes/`). UI pieces live in `components/`, pure logic in `core/` (scoring, selection, validation), caches/samples in `data/`.

## Architecture constraints

- The graph is `START → input_validation → syllabus_parser → output_validation → video_retrieval → popularity_ranking → transcript_fetch → transcript_evaluation → playlist_selection → END`, single-shot with no checkpointer. Errors route straight to `END`. Add new steps as nodes in this graph, not a parallel pipeline.
- `build_workflow(decomposer=None, youtube_client=None, transcript_fetcher=None, evaluator=None)` accepts injected services. All external clients/models are lazy — constructing them at import time would break tests and UI startup without keys.
- `LearningUnit.search_query` is generated during decomposition and passed directly as YouTube `search.list` `q`. The checklist is never sent to YouTube; it is the target for transcript coverage.
- No language input and no language weighting: the decomposition prompt follows the syllabus language (English or Hindi), YouTube search sends no `relevanceLanguage`, and transcripts try `["en", "hi"]` equally. Region is unrestricted unless `YOUTUBE_REGION_CODE` is set (e.g. `IN`).
- UI is unit-centric: coverage icons, timestamps, YouTube search text, and selected/candidate video links render inside each unit. Missing coverage shows explicit `no transcript evidence`, never an empty `- [ ]` placeholder. Do not reintroduce separate video sections. Keep the input form compact (subject/level in one row, short syllabus area).
- Top 20 candidates per unit are scored deterministically by views/likes/comments; top 5 get transcripts. The final winner per unit is chosen by `core/selection.py` from the structured transcript rubric, with popularity only as a tie-break.
- Independent retrieval, transcript, and evaluation work runs in bounded threads (`core/concurrency.map_parallel`), preserving order. Tune with `YOUTUBE_WORKERS=4`, `TRANSCRIPT_WORKERS=3`, `EVALUATION_WORKERS=4`. Keep defaults conservative for quota/rate limits.
- Structured LLM results (decomposition and evaluation) are cached by schema + prompt hash in `data/cache/`; reruns skip repeat calls. `gemini-3.5-flash-lite` uses fixed sampling defaults — don't pass `temperature`.
- Gemini is built via `init_chat_model("google_genai:<model>")` in `services/llm.py` with `with_structured_output(..., method="json_schema")`; keep the Pydantic schema union-free for compatibility.

## Verification

- `uv run pytest -q` — offline; tests inject fakes for all services via `build_workflow`. Do not add live API calls to the test suite.
- Live smoke check (manual, not a test): `uv run streamlit run app.py` with `GOOGLE_API_KEY` and `YOUTUBE_API_KEY` set. `YOUTUBE_FINALISTS=1` makes a cheap end-to-end check.
- If Streamlit raises `ImportError` for a symbol that exists on disk, restart the Streamlit process — a long-running server can hold a stale Python module cache.
- There is no lint/format/typecheck/CI config yet; don't invent those commands.

## Current state

M0–M4 are complete. The app decomposes a syllabus, shortlists YouTube videos, evaluates transcripts with the user rubric, and renders a playlist with coverage. There is no scheduled next milestone; follow `docs/PLAN.md` for status and verify with `uv run pytest -q` after any change.
