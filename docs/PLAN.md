# Implementation Plan

> **Status:** M0–M4 complete. See [ARCHITECTURE.md](ARCHITECTURE.md) for the current structure and invariants. Update this file when the pipeline changes.

## Current status

- Implemented: the full syllabus → searchable units → YouTube candidates → 5 finalists per unit → transcript evaluation → selected playlist + coverage report pipeline.
- No language input or weighting: English/Hindi are handled equally from the syllabus text; YouTube search sends no `relevanceLanguage`; region is unrestricted unless `YOUTUBE_REGION_CODE` is set.
- Default model: `gemini-3.5-flash-lite` via `init_chat_model`.
- `uv run pytest -q` → **25 passed**. Live end-to-end check produced a 4-item playlist with coverage statuses.
- Cached YouTube/transcript responses and cached structured evaluations live in gitignored `data/cache/`.
- Independent retrieval, transcript fetching, and transcript evaluation stages run in bounded threads via `core/concurrency.map_parallel`; worker counts are tunable through `YOUTUBE_WORKERS`, `TRANSCRIPT_WORKERS`, and `EVALUATION_WORKERS`.

## Milestones

### M0 — modular restructure + `init_chat_model` ✅ done

Flat packages at repo root, `src/` removed, text prompts, graph nodes, Streamlit components, `uv_build` configured for top-level modules.

### M1 — YouTube retrieval and top-20 → top-5 shortlist ✅ done

- `services/youtube.py`: `search.list` + batched `videos.list`, disk-cached; `YOUTUBE_API_KEY` from `.env`.
- 20 candidates per **learning unit** (assumption used), scored by `core/scoring.py`: log-scale + min-max normalize views/likes/comments within the pool, weights `0.40 / 0.35 / 0.25`.
- Top 5 per unit become `finalists`; shown in the UI with popularity scores.

### M2 — transcripts for the 5 finalists ✅ done

- `services/transcripts.py` wraps `youtube-transcript-api` with `languages=["en", "hi"]` treated equally and disk caching.
- Missing transcripts become `None` and do not fail the run.

### M3 — LLM scoring of those 5 transcripts ✅ done

- User-supplied rubric refined into `prompts/transcript_scoring.txt`.
- `schemas/evaluation.py` defines `SegmentEvaluation` with per-item coverage/evidence/example/garbled/span/label and segment-level fields.
- `graph/nodes/transcript_evaluation.py` chunks transcripts into ~700-word windows, formats them as `[mm:ss] text`, and calls `structured_model(SegmentEvaluation)`.
- `core/selection.py` aggregates segment results deterministically: best label per item, coverage ratio, penalties for noisy/unusable quality, off-topic relevance, sponsor/channel fluff, garbled text, and possible errors.

### M4 — playlist sequencing, coverage report, export ✅ done

- `graph/nodes/playlist_selection.py` picks the best finalist per unit using the M3 decision score (popularity only as tie-break), records the earliest explained timestamp, and builds a coverage report with `covered` / `partial` / `missing`.
- `components/results.py` renders the playlist, jump-to timestamps, coverage matrix, finalists, JSON download, and playlist CSV download.

## Verification checklist

- `uv run pytest -q` after every change; offline fakes only.
- Manual `uv run streamlit run app.py` smoke check with real keys.
- Live API smoke calls are manual, never part of the test suite.
- `YOUTUBE_FINALISTS=1` is useful for a cheap end-to-end live check.
