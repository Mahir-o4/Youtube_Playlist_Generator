from __future__ import annotations

from graph.nodes.video_retrieval import make_video_retrieval
from schemas import SyllabusBreakdown, VideoCandidate


def _candidate(video_id: str, unit_key: str) -> VideoCandidate:
    return VideoCandidate(
        video_id=video_id,
        unit_key=unit_key,
        search_query="same query",
        title="Video",
        channel="Channel",
        url=f"https://www.youtube.com/watch?v={video_id}",
        thumbnail="",
    )


def test_identical_queries_are_fetched_once() -> None:
    calls: list[str] = []

    class Client:
        def candidates_for_query(self, query, unit_key):
            calls.append(query)
            return [_candidate("abc", unit_key)]

    breakdown = SyllabusBreakdown.model_validate(
        {
            "subject": "Math",
            "level": "Undergraduate",
            "topics": [
                {
                    "title": "Basics",
                    "summary": "Basics.",
                    "units": [
                        {
                            "title": "One",
                            "objective": "One.",
                            "checklist": [{"text": "Define one."}],
                            "search_query": "same query",
                        },
                        {
                            "title": "Two",
                            "objective": "Two.",
                            "checklist": [{"text": "Define two."}],
                            "search_query": "same query",
                        },
                    ],
                }
            ],
        }
    )

    result = make_video_retrieval(Client(), workers=2)({"breakdown": breakdown})

    assert calls == ["same query"]
    assert set(result["candidates"]) == {"1.1", "1.2"}
    assert result["candidates"]["1.1"][0].unit_key == "1.1"
    assert result["candidates"]["1.2"][0].unit_key == "1.2"
