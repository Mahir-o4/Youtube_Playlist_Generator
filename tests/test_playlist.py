from __future__ import annotations

from graph.nodes.playlist_selection import playlist_selection
from schemas import (
    ChecklistItem,
    ItemResult,
    SegmentEvaluation,
    SyllabusBreakdown,
    VideoCandidate,
)


def _video() -> VideoCandidate:
    return VideoCandidate(
        video_id="abc",
        unit_key="1.1",
        search_query="vectors",
        title="Vectors explained",
        channel="Channel",
        url="https://www.youtube.com/watch?v=abc",
        thumbnail="",
    )


def _evaluation() -> SegmentEvaluation:
    return SegmentEvaluation(
        item_results=[
            ItemResult(
                item="Define a vector in R^n.",
                label="explained",
                evidence_quote="a vector is an arrow",
                evidence_timestamp="01:20",
            )
        ],
        level="intro",
        relevance="on_topic",
        fluff="none",
        format="explanation",
        quality="clean",
    )


def test_playlist_selection_builds_playlist_and_coverage(
    valid_breakdown: SyllabusBreakdown,
) -> None:
    state = {
        "breakdown": valid_breakdown,
        "finalists": {"1.1": [_video()]},
        "evaluations": {"1.1:abc": [_evaluation()]},
    }
    result = playlist_selection(state)

    assert result["error"] is None
    assert len(result["playlist"]) == 1
    assert result["playlist"][0].start_timestamp == "01:20"
    assert result["coverage"].items[0].status == "covered"
