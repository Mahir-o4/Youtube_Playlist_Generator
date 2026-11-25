"""Final playlist and coverage report schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from schemas.video import VideoCandidate


class PlaylistItem(BaseModel):
    unit_key: str
    video: VideoCandidate
    start_timestamp: str | None = None
    covered_checklist: list[str]
    decision_score: float


class CoverageItem(BaseModel):
    unit_key: str
    item: str
    status: Literal["covered", "partial", "missing"]
    evidence_video_id: str | None = None
    evidence_timestamp: str | None = None


class CoverageReport(BaseModel):
    items: list[CoverageItem]
