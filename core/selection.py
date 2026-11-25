"""Deterministic aggregation of segment evaluations into a final choice.

Scoring uses one coverage term and six penalties (language is not a factor):
  1. coverage: (2*explained + mentioned) / (2*checklist_items)
  2. unusable transcript quality: -0.30
  3. noisy transcript quality: -0.10
  4. off-topic segment relevance: -0.15
  5. sponsor/channel intro fluff: -0.05
  6. garbled transcript evidence: -0.10
  7. possible error warning: -0.05

`aggregate_video` itself takes four arguments: video_id, unit_key, evaluations,
and checklist. Scores are clamped to [0, 1].
"""

from __future__ import annotations

from schemas import ChecklistItem, SegmentEvaluation, VideoDecision

_LABEL_RANK = {"absent": 0, "mentioned": 1, "explained": 2}
PENALTY_UNUSABLE = 0.30
PENALTY_NOISY = 0.10
PENALTY_OFF_TOPIC = 0.15
PENALTY_FLUFF = 0.05
PENALTY_GARBLED = 0.10
PENALTY_POSSIBLE_ERROR = 0.05


def _timestamp_seconds(value: str | None) -> float:
    if not value:
        return float("inf")
    parts = value.split(":")
    try:
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except ValueError:
        return float("inf")
    return float("inf")


def evidence_timestamp(
    evaluations: list[SegmentEvaluation], item_text: str
) -> str | None:
    """Return the earliest explained-evidence timestamp for an item."""
    candidates = [
        result.evidence_timestamp
        for evaluation in evaluations
        for result in evaluation.item_results
        if result.item == item_text
        and result.label == "explained"
        and result.evidence_timestamp
    ]
    if not candidates:
        return None
    return min(candidates, key=_timestamp_seconds)


def earliest_timestamp(timestamps: list[str | None]) -> str | None:
    """Return the earliest of several timestamp labels."""
    valid = [value for value in timestamps if value]
    if not valid:
        return None
    return min(valid, key=_timestamp_seconds)


def aggregate_video(
    video_id: str,
    unit_key: str,
    evaluations: list[SegmentEvaluation],
    checklist: list[ChecklistItem],
) -> VideoDecision:
    """Aggregate all segment evaluations for one video."""
    best_labels: dict[str, str] = {}
    explained: list[str] = []
    mentioned: list[str] = []

    for item in checklist:
        labels = [
            result.label
            for evaluation in evaluations
            for result in evaluation.item_results
            if result.item == item.text
        ]
        label = max(labels, key=lambda value: _LABEL_RANK.get(value, 0)) if labels else "absent"
        best_labels[item.text] = label
        if label == "explained":
            explained.append(item.text)
        elif label == "mentioned":
            mentioned.append(item.text)

    denominator = 2 * max(len(checklist), 1)
    coverage = (2 * len(explained) + len(mentioned)) / denominator

    penalties = 0.0
    if any(evaluation.quality == "unusable" for evaluation in evaluations):
        penalties += PENALTY_UNUSABLE
    elif any(evaluation.quality == "noisy" for evaluation in evaluations):
        penalties += PENALTY_NOISY
    if any(evaluation.relevance == "off_topic" for evaluation in evaluations):
        penalties += PENALTY_OFF_TOPIC
    if any(
        evaluation.fluff in {"sponsor", "channel_intro"}
        for evaluation in evaluations
    ):
        penalties += PENALTY_FLUFF
    if any(
        result.garbled
        for evaluation in evaluations
        for result in evaluation.item_results
    ):
        penalties += PENALTY_GARBLED
    if any(evaluation.possible_error for evaluation in evaluations):
        penalties += PENALTY_POSSIBLE_ERROR

    score = round(max(0.0, coverage - penalties), 6)
    return VideoDecision(
        video_id=video_id,
        unit_key=unit_key,
        score=score,
        best_labels=best_labels,
        explained=explained,
        mentioned=mentioned,
    )
