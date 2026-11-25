"""Node: choose the best finalist per unit and build the coverage report."""

from __future__ import annotations

from graph.state import WorkflowState
from core.selection import aggregate_video, earliest_timestamp, evidence_timestamp
from schemas import (
    CoverageItem,
    CoverageReport,
    PlaylistItem,
    SegmentEvaluation,
    VideoCandidate,
    VideoDecision,
)


def _unit_checklists(state: WorkflowState) -> dict[str, tuple[str, list]]:
    breakdown = state.get("breakdown")
    if not breakdown:
        return {}
    result: dict[str, tuple[str, list]] = {}
    for topic_index, topic in enumerate(breakdown.topics, start=1):
        for unit_index, unit in enumerate(topic.units, start=1):
            result[f"{topic_index}.{unit_index}"] = (
                f"{topic.title} — {unit.title}",
                unit.checklist,
            )
    return result


def playlist_selection(state: WorkflowState) -> dict:
    finalists = state.get("finalists") or {}
    evaluations: dict[str, list[SegmentEvaluation]] = state.get("evaluations") or {}
    checklists = _unit_checklists(state)
    playlist: list[PlaylistItem] = []
    coverage_items: list[CoverageItem] = []

    try:
        for unit_key, videos in finalists.items():
            _, checklist = checklists.get(unit_key, (unit_key, []))
            ranked: list[tuple[VideoCandidate, VideoDecision, list[SegmentEvaluation]]] = []
            for video in videos:
                video_evaluations = evaluations.get(
                    f"{unit_key}:{video.video_id}", []
                )
                if not video_evaluations:
                    continue
                decision = aggregate_video(
                    video.video_id, unit_key, video_evaluations, checklist
                )
                ranked.append((video, decision, video_evaluations))

            if not ranked:
                continue

            best_video, best_decision, best_evaluations = max(
                ranked,
                key=lambda entry: (
                    entry[1].score,
                    entry[0].popularity_score,
                    entry[0].views,
                ),
            )
            start = earliest_timestamp(
                [
                    evidence_timestamp(best_evaluations, item)
                    for item in best_decision.explained
                ]
            )
            playlist.append(
                PlaylistItem(
                    unit_key=unit_key,
                    video=best_video,
                    start_timestamp=start,
                    covered_checklist=(
                        best_decision.explained + best_decision.mentioned
                    ),
                    decision_score=best_decision.score,
                )
            )

            for item in checklist:
                if item.text in best_decision.explained:
                    status = "covered"
                elif item.text in best_decision.mentioned:
                    status = "partial"
                else:
                    status = "missing"
                coverage_items.append(
                    CoverageItem(
                        unit_key=unit_key,
                        item=item.text,
                        status=status,
                        evidence_video_id=(
                            best_video.video_id if status != "missing" else None
                        ),
                        evidence_timestamp=(
                            evidence_timestamp(best_evaluations, item.text)
                            if status != "missing"
                            else None
                        ),
                    )
                )
    except Exception as exc:
        return {"error": f"Playlist selection failed: {exc}"}

    return {
        "playlist": playlist,
        "coverage": CoverageReport(items=coverage_items),
        "error": None,
    }
