"""Pydantic schemas for the syllabus agent."""

from schemas.evaluation import (
    ItemResult,
    PossibleError,
    SegmentEvaluation,
    Span,
    VideoDecision,
)
from schemas.input import StrictTextModel, SyllabusInput
from schemas.playlist import CoverageItem, CoverageReport, PlaylistItem
from schemas.syllabus import ChecklistItem, LearningUnit, SyllabusBreakdown, Topic
from schemas.video import TranscriptSegment, VideoCandidate

__all__ = [
    "ChecklistItem",
    "CoverageItem",
    "CoverageReport",
    "ItemResult",
    "LearningUnit",
    "PlaylistItem",
    "PossibleError",
    "SegmentEvaluation",
    "Span",
    "StrictTextModel",
    "SyllabusBreakdown",
    "SyllabusInput",
    "Topic",
    "TranscriptSegment",
    "VideoCandidate",
    "VideoDecision",
]
