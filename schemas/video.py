"""YouTube candidate and transcript schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class VideoCandidate(BaseModel):
    video_id: str
    unit_key: str
    search_query: str
    title: str
    channel: str
    url: str
    thumbnail: str
    duration_seconds: int | None = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    popularity_score: float = 0.0

    @property
    def watch_url(self) -> str:
        return self.url


class TranscriptSegment(BaseModel):
    video_id: str
    start: float
    duration: float
    text: str
