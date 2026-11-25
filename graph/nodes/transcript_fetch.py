"""Node: fetch transcripts for the 5 finalists of each unit, in parallel."""

from __future__ import annotations

from collections.abc import Callable

from core.concurrency import map_parallel, worker_count
from graph.state import WorkflowState
from schemas import TranscriptSegment


def make_transcript_fetcher(
    fetcher, workers: int | None = None
) -> Callable[[WorkflowState], dict]:
    """Build a transcript node around an injectable fetcher."""

    def transcript_fetch(state: WorkflowState) -> dict:
        finalists = state.get("finalists") or {}
        languages = ["en", "hi"]

        video_ids: list[str] = []
        seen: set[str] = set()
        for videos in finalists.values():
            for video in videos:
                if video.video_id not in seen:
                    seen.add(video.video_id)
                    video_ids.append(video.video_id)

        def fetch(video_id: str):
            return video_id, fetcher.fetch(video_id, languages)

        try:
            transcripts: dict[str, list[TranscriptSegment] | None] = dict(
                map_parallel(
                    fetch,
                    video_ids,
                    workers or worker_count("TRANSCRIPT_WORKERS", 3),
                )
            )
        except Exception as exc:
            return {"error": f"Transcript fetch failed: {exc}", "transcripts": {}}
        return {"transcripts": transcripts, "error": None}

    return transcript_fetch
