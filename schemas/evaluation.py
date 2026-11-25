"""Structured output schemas for transcript evaluation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Span(BaseModel):
    start: str
    end: str


class PossibleError(BaseModel):
    item: str
    quote: str


class ItemResult(BaseModel):
    item: str
    evidence_quote: str | None = None
    evidence_timestamp: str | None = None
    span: Span | None = None
    garbled: bool = False
    has_example: bool = False
    label: Literal["explained", "mentioned", "absent"]


class SegmentEvaluation(BaseModel):
    item_results: list[ItemResult]
    level: Literal["intro", "intermediate", "advanced", "unclear"]
    relevance: Literal["on_topic", "related", "off_topic"]
    fluff: Literal["none", "sponsor", "channel_intro", "recap", "chatter"]
    format: Literal["explanation", "slides_read", "demo", "qa"]
    quality: Literal["clean", "noisy", "unusable"]
    prereqs: list[str] = Field(default_factory=list)
    possible_error: PossibleError | None = None


class VideoDecision(BaseModel):
    video_id: str
    unit_key: str
    score: float
    best_labels: dict[str, str]
    explained: list[str]
    mentioned: list[str]
