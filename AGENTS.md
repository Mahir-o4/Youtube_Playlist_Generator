# AGENTS.md

Early-stage syllabus-to-YouTube-playlist app. `pyproject.toml` and `uv.lock` are the dependency sources of truth.

## Read first

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — module layout, graph design, and invariants (M0 implemented).
- [`docs/PLAN.md`](docs/PLAN.md) — milestone order, current status, and open items.
- Read both before changing structure or adding a node/service; keep them updated in the same change when code diverges.

## Toolchain

- `uv`-managed: use `uv run ...` and `uv sync`; `.venv/` is generated and gitignored. Add dependencies with `uv add` (`uv add --dev pytest` for test tooling) so `pyproject.toml` and `uv.lock` stay in sync.
- Python is pinned to 3.14 in `.python-version` (`requires-python = ">=3.14"`); don't downgrade it.
- Secrets live in the gitignored root `.env`. `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) is required for live decomposition; `APP_GEMINI_MODEL` overrides the default `gemini-3.5-flash-lite`. Never commit `.env`.

## Layout and entrypoints

- Modular flat layout at the repo root; `src/` and the `app = "app:main"` script are gone. `uv_build` uses `module-root = ""` with named packages (see `pyproject.toml`).
- Streamlit entrypoint: `uv run streamlit run app.py`. `app.py` is not packaged as an importable module; run it from the repo root.
- Pipeline packages: `schemas/` (Pydantic models) → `prompts/` (text templates) → `services/llm.py` (Gemini via `init_chat_model`) → `graph/` (`build_workflow` + nodes in `graph/nodes/`). UI pieces live in `components/`, pure logic in `core/`, caches/samples in `data/`.

## Architecture constraints

- The graph is `START → input_validation → syllabus_parser → output_validation → END`, single-shot with no checkpointer. Errors route straight to `END`. Extend this graph with one new node per milestone; do not build a parallel pipeline.
- `build_workflow(decomposer=None)` accepts an injected decomposer. `init_model()` and `make_decomposer()` must stay lazy — constructing the model at import time would break tests and UI startup without a key.
- `LearningUnit.search_query` is generated during decomposition so later YouTube retrieval stays deterministic (no extra LLM call).
- Gemini is built via `init_chat_model("google_genai:<model>")` in `services/llm.py` with `with_structured_output(..., method="json_schema")`; keep the Pydantic schema union-free for compatibility.

## Verification

- `uv run pytest -q` — offline; tests inject a fake decomposer via `build_workflow`. Do not add live API calls to the test suite.
- Live smoke check (manual, not a test): `uv run streamlit run app.py`, then submit a short syllabus with `GOOGLE_API_KEY` set.
- There is no lint/format/typecheck/CI config yet; don't invent those commands.

## Next milestone

M0 is complete. Next is M1: YouTube retrieval via the Data API (20 → 5 per unit), adding `VideoCandidate` and retrieval/ranking nodes to the same graph. Follow `docs/PLAN.md` and keep one milestone at a time.
