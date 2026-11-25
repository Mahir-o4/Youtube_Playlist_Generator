"""State schema for the LangGraph workflow."""

from __future__ import annotations

from typing import TypedDict

from schemas import (
    CoverageReport,
    PlaylistItem,
    SegmentEvaluation,
    SyllabusBreakdown,
    SyllabusInput,
    TranscriptSegment,
    VideoCandidate,
)


class WorkflowState(TypedDict, total=False):
    subject: str
    level: str
    syllabus: str
    syllabus_input: SyllabusInput | None
    breakdown: SyllabusBreakdown | None
    candidates: dict[str, list[VideoCandidate]]
    finalists: dict[str, list[VideoCandidate]]
    transcripts: dict[str, list[TranscriptSegment] | None]
    evaluations: dict[str, list[SegmentEvaluation]]
    playlist: list[PlaylistItem]
    coverage: CoverageReport | None
    error: str | None
