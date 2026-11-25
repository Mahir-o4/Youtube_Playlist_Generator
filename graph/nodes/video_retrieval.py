"""Node: retrieve up to 20 YouTube candidates per learning unit, in parallel."""

from __future__ import annotations

from collections.abc import Callable

from core.concurrency import map_parallel, worker_count
from graph.state import WorkflowState
from schemas import VideoCandidate


def make_video_retrieval(client, workers: int | None = None) -> Callable[[WorkflowState], dict]:
    """Build a retrieval node around a YouTube-like client."""

    def video_retrieval(state: WorkflowState) -> dict:
        breakdown = state.get("breakdown")
        if breakdown is None:
            return {}

        unique_queries: dict[str, str] = {}
        aliases: dict[str, str] = {}
        for topic_index, topic in enumerate(breakdown.topics, start=1):
            for unit_index, unit in enumerate(topic.units, start=1):
                key = f"{topic_index}.{unit_index}"
                aliases[key] = unit.search_query
                unique_queries.setdefault(unit.search_query, key)

        def fetch(query: str):
            source_key = unique_queries[query]
            return query, client.candidates_for_query(query, source_key)

        try:
            fetched = dict(
                map_parallel(
                    fetch,
                    list(unique_queries),
                    workers or worker_count("YOUTUBE_WORKERS", 4),
                )
            )
            candidates: dict[str, list[VideoCandidate]] = {
                key: [
                    candidate.model_copy(update={"unit_key": key})
                    for candidate in fetched[query]
                ]
                for key, query in aliases.items()
            }
        except Exception as exc:
            return {"error": f"YouTube retrieval failed: {exc}", "candidates": {}}
        return {"candidates": candidates, "error": None}

    return video_retrieval
