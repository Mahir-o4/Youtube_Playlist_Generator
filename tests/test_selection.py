from __future__ import annotations

from core.selection import aggregate_video
from schemas import ChecklistItem, ItemResult, SegmentEvaluation


def _evaluation(
    label: str,
    quality: str = "clean",
    relevance: str = "on_topic",
    fluff: str = "none",
    garbled: bool = False,
) -> SegmentEvaluation:
    return SegmentEvaluation(
        item_results=[
            ItemResult(
                item="Define a vector.",
                label=label,  # type: ignore[arg-type]
                evidence_quote="a vector is an arrow",
                evidence_timestamp="01:20",
                garbled=garbled,
            )
        ],
        level="intro",
        relevance=relevance,  # type: ignore[arg-type]
        fluff=fluff,  # type: ignore[arg-type]
        format="explanation",
        quality=quality,  # type: ignore[arg-type]
    )


def test_aggregate_takes_best_label_across_segments() -> None:
    decision = aggregate_video(
        "abc",
        "1.1",
        [_evaluation("mentioned"), _evaluation("explained")],
        [ChecklistItem(text="Define a vector.")],
    )
    assert decision.best_labels["Define a vector."] == "explained"
    assert decision.explained == ["Define a vector."]
    assert decision.score == 1.0


def test_aggregate_penalizes_noise_and_off_topic() -> None:
    decision = aggregate_video(
        "abc",
        "1.1",
        [
            _evaluation(
                "explained", quality="noisy", relevance="off_topic", garbled=True
            )
        ],
        [ChecklistItem(text="Define a vector.")],
    )
    assert decision.score < 1.0
    assert decision.score >= 0.0
