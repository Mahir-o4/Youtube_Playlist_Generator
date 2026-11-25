from __future__ import annotations

from graph.nodes.transcript_evaluation import make_transcript_evaluation
from schemas import (
    ItemResult,
    SegmentEvaluation,
    SyllabusBreakdown,
    TranscriptSegment,
    VideoCandidate,
)


def test_evaluation_node_groups_results_per_video(
    valid_breakdown: SyllabusBreakdown,
) -> None:
    calls: list[str] = []

    def fake_evaluator(messages):
        calls.append(messages[1].content)
        return SegmentEvaluation(
            item_results=[
                ItemResult(
                    item="Define a vector in R^n.",
                    label="explained",
                    evidence_quote="a vector is an arrow",
                    evidence_timestamp="00:10",
                )
            ],
            level="intro",
            relevance="on_topic",
            fluff="none",
            format="explanation",
            quality="clean",
        )

    video = VideoCandidate(
        video_id="abc",
        unit_key="1.1",
        search_query="vectors",
        title="Vectors",
        channel="Channel",
        url="https://www.youtube.com/watch?v=abc",
        thumbnail="",
    )
    state = {
        "breakdown": valid_breakdown,
        "finalists": {"1.1": [video]},
        "transcripts": {
            "abc": [
                TranscriptSegment(
                    video_id="abc", start=10.0, duration=2.0, text="a vector is an arrow"
                )
            ]
        },
    }

    result = make_transcript_evaluation(fake_evaluator)(state)

    assert result["error"] is None
    assert "1.1:abc" in result["evaluations"]
    assert "Define a vector in R^n." in calls[0]
