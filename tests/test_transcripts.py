from __future__ import annotations

from graph.nodes.transcript_fetch import make_transcript_fetcher
from schemas import TranscriptSegment, VideoCandidate


def _video(video_id: str) -> VideoCandidate:
    return VideoCandidate(
        video_id=video_id,
        unit_key="1.1",
        search_query="query",
        title="Video",
        channel="Channel",
        url=f"https://www.youtube.com/watch?v={video_id}",
        thumbnail="",
    )


def test_transcript_node_fetches_each_video_once() -> None:
    calls: list[str] = []

    class Fetcher:
        def fetch(self, video_id: str, languages):
            calls.extend([video_id])
            return [
                TranscriptSegment(
                    video_id=video_id, start=0.0, duration=1.5, text="hello"
                )
            ]

    state = {
        "breakdown": None,
        "finalists": {"1.1": [_video("a"), _video("b")], "1.2": [_video("a")]},
    }
    result = make_transcript_fetcher(Fetcher())(state)

    assert calls == ["a", "b"]
    assert set(result["transcripts"]) == {"a", "b"}
    assert result["error"] is None


def test_transcript_node_handles_unavailable_transcript() -> None:
    class Fetcher:
        def fetch(self, video_id: str, languages):
            return None

    state = {"finalists": {"1.1": [_video("a")]}, "breakdown": None}
    result = make_transcript_fetcher(Fetcher())(state)
    assert result["transcripts"]["a"] is None
