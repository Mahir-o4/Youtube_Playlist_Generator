from __future__ import annotations

from core.scoring import score_candidates
from schemas import VideoCandidate


def _candidate(name: str, views: int, likes: int, comments: int) -> VideoCandidate:
    return VideoCandidate(
        video_id=name,
        unit_key="1.1",
        search_query="query",
        title=name,
        channel="channel",
        url=f"https://www.youtube.com/watch?v={name}",
        thumbnail="",
        views=views,
        likes=likes,
        comments=comments,
    )


def test_popularity_prefers_balanced_engagement() -> None:
    candidates = [
        _candidate("low", 100, 10, 1),
        _candidate("viral", 10_000_000, 100, 5),
        _candidate("balanced", 500_000, 40_000, 3_000),
    ]
    ranked = score_candidates(candidates)
    assert [c.video_id for c in ranked][0] == "balanced"
    assert ranked[0].popularity_score > ranked[1].popularity_score


def test_popularity_handles_zero_counts() -> None:
    candidates = [
        _candidate("zero", 0, 0, 0),
        _candidate("some", 10, 2, 1),
    ]
    ranked = score_candidates(candidates)
    assert ranked[0].video_id == "some"
    assert ranked[1].popularity_score == 0.0
