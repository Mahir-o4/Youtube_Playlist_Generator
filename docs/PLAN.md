# Implementation Plan

> **Status:** M0 complete. See [ARCHITECTURE.md](ARCHITECTURE.md) for the current structure and invariants. Implement **one milestone at a time** and update this file's status after each.

## Current status

- Implemented: M0 modular restructure (flat packages, `init_chat_model`, text prompts, graph nodes, Streamlit components) plus the original syllabus-decomposition feature. `uv run pytest -q` → 16 passed; live `init_chat_model` smoke call succeeds with `gemini-3.5-flash-lite`.
- Not implemented: YouTube retrieval, transcripts, ranking, playlist selection, coverage report.

## Milestones

### M0 — modular restructure + `init_chat_model` ✅ done

1. Create the folder tree in [ARCHITECTURE.md](ARCHITECTURE.md#target-layout); move current code; delete `src/`.
2. Add `langchain` with `uv add langchain`; replace direct `ChatGoogleGenerativeAI` construction with `init_model()` → `init_chat_model(f"google_genai:{model}")` in `services/llm.py`.
3. Split schemas, prompt text, workflow nodes, and UI components; configure `[tool.uv.build-backend]` as documented.
4. Update `README.md`, `AGENTS.md`, `.env.example`; add `data/cache/` to `.gitignore`.
5. Verify: relocated tests pass (`uv run pytest -q`) + one live decomposition smoke call.

### M1 — YouTube retrieval and top-20 → top-5 shortlist

1. Add `httpx` as a direct dependency; build `services/youtube.py` with `search.list` + batched `videos.list`.
2. For each learning unit: fetch up to 20 videos, collect views/likes/comments, cache responses.
3. Add `core/scoring.py`: log-scale → min-max normalize within the pool → `0.40 views + 0.35 likes + 0.25 comments`; keep top 5.
4. Add `VideoCandidate` schema, retrieval + ranking nodes, and offline tests with fixture stats.
5. `YOUTUBE_API_KEY` is now present in `.env`; use it for the M1 live smoke test.
6. Confirm the assumption that 20/5 are **per learning unit** before starting.

### M2 — transcripts for the 5 finalists

1. `uv add youtube-transcript-api`; build `services/transcripts.py` with language preference from the syllabus input.
2. Store timestamped segments; handle missing transcripts without failing the run.
3. Add `TranscriptSegment` schema and the `transcript_fetch` node; test with a fake fetcher only.

### M3 — LLM scoring of those 5 transcripts

1. User-supplied rubric is refined and saved as `prompts/transcript_scoring.txt`; do not invent replacement criteria.
2. Define `VideoEvaluation` structured-output schema matching the prompt: per-item coverage/evidence/example/garbled/span/label plus segment-level level/relevance/fluff/format/quality/prereqs/possible_error.
3. Add `transcript_evaluation` node using `structured_model(VideoEvaluation)` over transcript windows for the 5 M1 finalists.
4. Aggregate segment results into a per-video decision deterministically. Confirm the aggregation rule before implementing final selection.
5. This structured output — not the 20-candidate popularity score — is the ground for the final choice among the 5 videos.

### M4 — playlist sequencing, coverage report, export

1. Greedy checklist coverage in breakdown order → `PlaylistItem(video, start_timestamp, covered_checklist)`.
2. `prompts/coverage.txt` + coverage schema: covered / partial / missing with evidence.
3. Render playlist, jump-to timestamps, coverage matrix, JSON/CSV export in `components/results.py`.

## Verification checklist

- `uv run pytest -q` after every milestone; offline fakes only.
- Manual `uv run streamlit run app.py` smoke check with real keys.
- Live API smoke calls are manual, never part of the test suite.

## Open items

- User-supplied transcript scoring prompt (needed at M3).
- `YOUTUBE_API_KEY` is already in `.env` for M1 live verification.
- Confirm per-unit vs whole-syllabus interpretation of 20 candidates / 5 finalists.
